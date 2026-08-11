"""Phase 2 AI explanation application service (extends Phase 1).

Responsibilities:
1. Verify the caller owns the assessment (reuses existing report ownership
   semantics — no new access-control path).
2. Assemble a minimal, PHI-scrubbed ``ReportExplanationContext`` from the
   deterministic ``HealthAssessmentModel`` + ``AssessmentResultModel`` (the
   CDSE output) and the knowledge graph (for human-readable names).
3. **Phase 2:** retrieve approved, eligible evidence via
   ``EvidenceRetrievalService`` (knowledge-graph grounded, ranked, bounded)
   and enrich the AI context with it.
4. Call the configured ``AIExplanationProvider``.
5. Parse + validate the raw provider output against the deterministic
   allow-lists — **including evidence ids** (rejects hallucinated citations).
6. Cache the result in-memory keyed by (trace_id, prompt_version) so the LLM
   is not called repeatedly for an unchanged report.

AI failure and retrieval failure NEVER break the clinical report: on any
provider/validation error the service returns the standard
``UNAVAILABLE_FALLBACK`` (available=False), and the report endpoint surfaces
the report normally. If retrieval returns zero evidence, the AI still explains
the deterministic report but must state that no supporting evidence was
available (never fabricate evidence).

The deterministic CDSE / ReportService are not modified or re-invoked here.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.phase7_prompts import (
    AI_TRANSPARENCY_NOTICE,
    PHASE7_PROMPT_VERSION,
)
from app.application.ai.prompts import PROMPT_VERSION
from app.application.ai.provider import (
    AIProviderError,
    AIValidationFailure,
    AIExplanationProvider,
    get_explanation_provider,
)
from app.application.ai.language import normalize_language
from app.application.dtos.ai_dtos import (
    AIExplanationResponse,
    AIQualityStatus,
    BodySystemContext,
    ConditionContext,
    IndicatorContext,
    LaboratoryTestContext,
    LiteracyLevel,
    RecommendationContext,
    ReportExplanationContext,
    SourceBreakdownItem,
    UNAVAILABLE_FALLBACK,
)
from app.application.services.ai_audit_service import AIAuditService
from app.application.services.evidence_retrieval_service import (
    EvidenceRetrievalService,
)
from app.core.logging import get_logger
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.recommendation import (
    RecommendationModel,
)
from app.infrastructure.persistence.models.report import HealthAssessmentModel
from app.infrastructure.persistence.repositories.sql_decision_repository import (
    SQLDecisionRepository,
)
from app.infrastructure.persistence.repositories.sql_report_repository import (
    SQLReportRepository,
)

logger = get_logger(__name__)

_TRACE_RE = re.compile(r"\[trace:([0-9a-fA-F]+)\]")


class _ExplanationCache:
    """Tiny in-memory cache keyed by (trace_id, prompt_version).

    Intentionally process-local and dependency-free: avoids Redis/DB schema
    changes for Phase 1. A prompt-version bump invalidates entries. Capacity
    is bounded with a simple FIFO eviction.
    """

    def __init__(self, capacity: int = 256) -> None:
        self._capacity = capacity
        self._store: dict[str, AIExplanationResponse] = {}
        self._order: list[str] = []

    def get(self, key: str) -> AIExplanationResponse | None:
        return self._store.get(key)

    def put(self, key: str, value: AIExplanationResponse) -> None:
        if key in self._store:
            return
        if len(self._order) >= self._capacity:
            old = self._order.pop(0)
            self._store.pop(old, None)
        self._store[key] = value
        self._order.append(key)

    def clear(self) -> None:
        self._store.clear()
        self._order.clear()


_explanation_cache = _ExplanationCache()


def _extract_trace_id(result: AssessmentResultModel | None) -> str | None:
    """Recover the CDSE run trace_id from the persisted result summary.

    The CDSE stores ``summary=str(dict)`` where the dict includes ``trace_id``.
    If parsing fails, fall back to the ``[trace:<id>]`` marker embedded in the
    explanation_records text.
    """
    if not result:
        return None
    summary = getattr(result, "summary", None)
    if summary:
        try:
            parsed = ast.literal_eval(summary)
            if isinstance(parsed, dict) and parsed.get("trace_id"):
                return str(parsed["trace_id"])
        except Exception:
            pass
        m = _TRACE_RE.search(summary)
        if m:
            return m.group(1)
    for expl in getattr(result, "explanations", []) or []:
        text = getattr(expl, "text", None) or ""
        m = _TRACE_RE.search(text)
        if m:
            return m.group(1)
    return None


class AIExplanationService:
    def __init__(
        self,
        session: AsyncSession,
        provider: AIExplanationProvider | None = None,
        retrieval_service: EvidenceRetrievalService | None = None,
    ) -> None:
        self.session = session
        self.report_repo = SQLReportRepository(session)
        self.dec_repo = SQLDecisionRepository(session)
        self.retrieval = retrieval_service or EvidenceRetrievalService(session)
        self.provider = provider or get_explanation_provider()
        self.audit = AIAuditService(session)

    async def explain_report(
        self,
        session_id: str,
        user_id: str,
        *,
        language: str = "en",
        literacy_level: str = "standard",
    ) -> AIExplanationResponse:
        """Return a validated, evidence-grounded AI explanation for the
        caller's report.

        Ownership is enforced via the existing report repository getters. If
        there is no report, raises ValueError (the endpoint maps it to 404). If
        the AI provider fails or returns invalid output, returns the safe
        ``UNAVAILABLE_FALLBACK`` — never raises for an AI failure. Retrieval
        failure is treated the same way (the report still works).

        Phase 7: ``language`` and ``literacy_level`` personalize the
        communication. The deterministic result is identical at every level;
        only communication changes.
        """
        report = await self.report_repo.get_report_by_session(session_id)
        if not report or report.user_id != user_id:
            # Reuse the existing ownership semantics: missing OR not owned.
            raise ValueError("report not found")

        result = await self.dec_repo.get_result_by_session(session_id)
        trace_id = _extract_trace_id(result)

        # Phase 7: normalize language + literacy level.
        lang = normalize_language(language) or "en"
        try:
            lit = LiteracyLevel(literacy_level)
        except ValueError:
            lit = LiteracyLevel.STANDARD

        cache_key = f"{trace_id or session_id}:{PROMPT_VERSION}:{lang}:{lit.value}"
        cached = _explanation_cache.get(cache_key)
        if cached is not None:
            return cached

        context = await self._build_context(
            report, result, trace_id, language=lang, literacy_level=lit
        )

        provider_name = getattr(self.provider, "name", "stub")
        provider_model = getattr(self.provider, "model", "") or ""
        prompt_ver = getattr(self.provider, "prompt_version", PROMPT_VERSION)

        # Build the input-context hash source (ids only, no PHI).
        input_context = self._context_hash_source(context)

        try:
            raw = await self.provider.explain(context)
            response = self._parse_and_validate(raw, context)
            response.trace_id = trace_id
            response.prompt_version = prompt_ver
            response.retrieved_evidence = context.evidence
            response.evidence_available = context.evidence_available
            response.language = lang
            response.literacy_level = lit
            response.provider = provider_name
            response.model = provider_model
            response.transparency_notice = AI_TRANSPARENCY_NOTICE
            response.source_breakdown = self._build_source_breakdown(
                context, trace_id
            )
            if context.evidence_available and context.evidence:
                response.quality_status = AIQualityStatus.VALID
            elif context.activated_indicators:
                response.quality_status = AIQualityStatus.EVIDENCE_UNAVAILABLE
            else:
                response.quality_status = AIQualityStatus.VALID

            await self.audit.record(
                trace_id=trace_id,
                session_id=session_id,
                request_type="report_explanation",
                provider=provider_name,
                model=provider_model,
                prompt_version=prompt_ver,
                language=lang,
                literacy_level=lit.value,
                input_context=input_context,
                output_str=raw,
                status=response.quality_status.value,
            )
        except AIProviderError as exc:
            logger.warning("AI provider unavailable for session %s: %s", session_id, exc)
            response = UNAVAILABLE_FALLBACK.model_copy(deep=True)
            response.trace_id = trace_id
            response.retrieved_evidence = context.evidence
            response.evidence_available = context.evidence_available
            response.language = lang
            response.literacy_level = lit
            response.provider = provider_name
            response.model = provider_model
            response.transparency_notice = AI_TRANSPARENCY_NOTICE
            response.quality_status = AIQualityStatus.PROVIDER_UNAVAILABLE
            await self.audit.record(
                trace_id=trace_id,
                session_id=session_id,
                request_type="report_explanation",
                provider=provider_name,
                model=provider_model,
                prompt_version=prompt_ver,
                language=lang,
                literacy_level=lit.value,
                input_context=input_context,
                status="provider_unavailable",
                status_reason=str(exc)[:200],
            )
        except AIValidationFailure as exc:
            logger.warning("AI output invalid for session %s: %s", session_id, exc)
            response = UNAVAILABLE_FALLBACK.model_copy(deep=True)
            response.trace_id = trace_id
            response.retrieved_evidence = context.evidence
            response.evidence_available = context.evidence_available
            response.language = lang
            response.literacy_level = lit
            response.provider = provider_name
            response.model = provider_model
            response.transparency_notice = AI_TRANSPARENCY_NOTICE
            response.quality_status = AIQualityStatus.VALIDATION_FAILED
            await self.audit.record(
                trace_id=trace_id,
                session_id=session_id,
                request_type="report_explanation",
                provider=provider_name,
                model=provider_model,
                prompt_version=prompt_ver,
                language=lang,
                literacy_level=lit.value,
                input_context=input_context,
                status="validation_failed",
                status_reason=str(exc)[:200],
            )
        except Exception as exc:  # malformed/invalid AI output
            logger.warning("AI explanation invalid for session %s: %s", session_id, exc)
            response = UNAVAILABLE_FALLBACK.model_copy(deep=True)
            response.trace_id = trace_id
            response.retrieved_evidence = context.evidence
            response.evidence_available = context.evidence_available
            response.language = lang
            response.literacy_level = lit
            response.provider = provider_name
            response.model = provider_model
            response.transparency_notice = AI_TRANSPARENCY_NOTICE
            response.quality_status = AIQualityStatus.VALIDATION_FAILED
            await self.audit.record(
                trace_id=trace_id,
                session_id=session_id,
                request_type="report_explanation",
                provider=provider_name,
                model=provider_model,
                prompt_version=prompt_ver,
                language=lang,
                literacy_level=lit.value,
                input_context=input_context,
                status="validation_failed",
                status_reason=str(exc)[:200],
            )

        _explanation_cache.put(cache_key, response)
        return response

    async def _build_context(
        self,
        report: HealthAssessmentModel,
        result: AssessmentResultModel | None,
        trace_id: str | None,
        *,
        language: str = "en",
        literacy_level: LiteracyLevel = LiteracyLevel.STANDARD,
    ) -> ReportExplanationContext:
        # Body systems from the report rows (already bucketed by ReportService).
        body_systems: list[BodySystemContext] = []
        for bs in report.body_systems or []:
            score = _safe_float(bs.score)
            body_systems.append(
                BodySystemContext(
                    body_system_id=bs.body_system_id,
                    name=None,
                    category=bs.category,
                    score=score,
                )
            )

        indicators: list[IndicatorContext] = []
        conditions: list[ConditionContext] = []
        recommendations: list[RecommendationContext] = []
        lab_tests: list[LaboratoryTestContext] = []
        retrieved_evidence = []

        if result is not None:
            ind_ids = [a.indicator_id for a in result.activated_indicators or []]
            cond_ids = [a.condition_id for a in result.activated_conditions or []]
            rec_ids = [
                a.recommendation_id
                for a in result.generated_recommendations or []
            ]
            lab_ids = [
                a.laboratory_test_id
                for a in result.generated_laboratory_tests or []
            ]

            # Load names for indicators/conditions/recommendations/labs.
            ind_map = await self._load_indicators(ind_ids)
            cond_map = await self._load_conditions(cond_ids)
            rec_map = await self._load_recommendations(rec_ids)
            lab_map = await self._load_laboratory_tests(lab_ids)

            for a in result.activated_indicators or []:
                ind = ind_map.get(a.indicator_id)
                indicators.append(
                    IndicatorContext(
                        id=a.indicator_id,
                        key=ind.key if ind else "",
                        name=ind.name if ind else a.indicator_id,
                        description=ind.description if ind else None,
                        body_system_id=ind.body_system_id if ind else None,
                        severity=ind.severity if ind else None,
                        evidence_strength=ind.evidence_strength if ind else None,
                        score=a.score,
                        evidence_count=a.evidence_count,
                    )
                )

            for a in result.activated_conditions or []:
                cond = cond_map.get(a.condition_id)
                conditions.append(
                    ConditionContext(
                        id=a.condition_id,
                        code=cond.code if cond else None,
                        name=cond.name if cond else a.condition_id,
                        description=cond.description if cond else None,
                        body_system_id=cond.body_system_id if cond else None,
                        severity=cond.severity if cond else None,
                        score=a.score,
                        confidence=a.confidence,
                    )
                )

            for a in result.generated_recommendations or []:
                rec = rec_map.get(a.recommendation_id)
                recommendations.append(
                    RecommendationContext(
                        id=a.recommendation_id,
                        title=rec.title if rec else a.recommendation_id,
                        text=rec.text if rec else "",
                        category=rec.category if rec else None,
                        priority=rec.priority if rec else None,
                        urgency=rec.urgency if rec else None,
                        evidence_level=rec.evidence_level if rec else None,
                    )
                )

            for a in result.generated_laboratory_tests or []:
                lab = lab_map.get(a.laboratory_test_id)
                lab_tests.append(
                    LaboratoryTestContext(
                        id=a.laboratory_test_id,
                        name=lab.name if lab else a.laboratory_test_id,
                        description=lab.description if lab else None,
                        reason=a.reason,
                    )
                )

            # Phase 2: evidence-grounded retrieval over the knowledge graph.
            # Retrieval is derived ONLY from this user's deterministic result
            # (their activated indicators/conditions/recommendations), so a
            # user can never receive evidence from another patient's context.
            ind_labels = {i.id: i.name for i in indicators}
            cond_labels = {c.id: c.name for c in conditions}
            rec_labels = {r.id: r.title for r in recommendations}
            try:
                retrieval = await self.retrieval.retrieve(
                    indicator_ids=ind_ids,
                    condition_ids=cond_ids,
                    recommendation_ids=rec_ids,
                    indicator_labels=ind_labels,
                    condition_labels=cond_labels,
                    recommendation_labels=rec_labels,
                )
                retrieved_evidence = retrieval.evidence
            except Exception as exc:
                # Retrieval failure must never break the report: explain with
                # no evidence and let the AI state that none was available.
                logger.warning(
                    "Evidence retrieval failed for session %s: %s",
                    report.session_id,
                    exc,
                )
                retrieved_evidence = []

        severity = self._derive_severity(body_systems, conditions)

        return ReportExplanationContext(
            trace_id=trace_id,
            severity=severity,
            body_systems=body_systems,
            activated_indicators=indicators,
            possible_conditions=conditions,
            recommendations=recommendations,
            laboratory_tests=lab_tests,
            evidence=retrieved_evidence,
            evidence_available=bool(retrieved_evidence),
            prompt_version=PROMPT_VERSION,
            language=language,
            literacy_level=literacy_level,
        )

    @staticmethod
    def _derive_severity(
        body_systems: list[BodySystemContext],
        conditions: list[ConditionContext],
    ) -> str | None:
        # Use the highest-severity body-system category from the report if
        # present; otherwise the highest condition severity. This only READS
        # deterministic output — it never computes a new severity.
        order = [
            "critical",
            "Urgent Medical Review",
            "severe",
            "high",
            "Recommend Screening",
            "moderate",
            "Needs Attention",
            "mild",
            "Monitor",
            "Normal",
            "none",
        ]
        cats = [b.category for b in body_systems if b.category]
        for label in order:
            if label in cats:
                return label
        sevs = [c.severity for c in conditions if c.severity]
        for label in order:
            if label in sevs:
                return label
        return None

    def _parse_and_validate(
        self, raw: str, context: ReportExplanationContext
    ) -> AIExplanationResponse:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIValidationFailure("non-JSON AI output") from exc
        if not isinstance(data, dict):
            raise AIValidationFailure("AI output is not a JSON object")
        # Bounded copy to avoid huge payloads.
        if len(json.dumps(data)) > 50000:
            raise AIValidationFailure("AI output too large")
        response = AIExplanationResponse(
            summary=str(data.get("summary", "")).strip(),
            key_findings=data.get("key_findings", []) or [],
            severity_explanation=str(data.get("severity_explanation", "") or ""),
            recommendation_explanations=data.get(
                "recommendation_explanations", []
            )
            or [],
            evidence_notes=data.get("evidence_notes", []) or [],
            limitations=str(data.get("limitations", "") or ""),
            disclaimer=str(data.get("disclaimer", "") or ""),
            available=True,
        )
        # Bind the deterministic allow-lists and re-validate referenced ids.
        # The evidence allow-list is the set of ids actually retrieved — the
        # only citations the AI is permitted to use (anti-hallucination).
        response.bind_context(
            allowed_indicator_ids=context.allowed_indicator_ids,
            allowed_recommendation_ids=context.allowed_recommendation_ids,
            allowed_evidence_ids=context.allowed_evidence_ids,
        )
        return response

    # --- read-only knowledge graph loaders (names only) ---

    async def _load_indicators(
        self, ids: list[str]
    ) -> dict[str, ClinicalIndicatorModel]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(ClinicalIndicatorModel).where(
                ClinicalIndicatorModel.id.in_(ids)
            )
        )
        return {i.id: i for i in rows.scalars().all()}

    async def _load_conditions(
        self, ids: list[str]
    ) -> dict[str, PossibleConditionModel]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(PossibleConditionModel).where(
                PossibleConditionModel.id.in_(ids)
            )
        )
        return {c.id: c for c in rows.scalars().all()}

    async def _load_recommendations(
        self, ids: list[str]
    ) -> dict[str, RecommendationModel]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(RecommendationModel).where(RecommendationModel.id.in_(ids))
        )
        return {r.id: r for r in rows.scalars().all()}

    async def _load_laboratory_tests(self, ids: list[str]) -> dict[str, Any]:
        from app.infrastructure.persistence.models.laboratory_test import (
            LaboratoryTestModel,
        )

        if not ids:
            return {}
        rows = await self.session.execute(
            select(LaboratoryTestModel).where(LaboratoryTestModel.id.in_(ids))
        )
        return {l.id: l for l in rows.scalars().all()}


    @staticmethod
    def _context_hash_source(context: ReportExplanationContext) -> dict[str, Any]:
        """Build a minimal dict of entity ids + scores for the audit hash.
        Contains NO free-text PHI — only structural reference ids."""
        return {
            "trace_id": context.trace_id,
            "severity": context.severity,
            "indicator_ids": sorted(context.allowed_indicator_ids),
            "condition_ids": sorted(context.allowed_condition_ids),
            "recommendation_ids": sorted(context.allowed_recommendation_ids),
            "evidence_ids": sorted(context.allowed_evidence_ids),
            "language": context.language,
            "literacy_level": context.literacy_level.value,
            "prompt_version": context.prompt_version,
        }

    @staticmethod
    def _build_source_breakdown(
        context: ReportExplanationContext,
        trace_id: str | None,
    ) -> list[SourceBreakdownItem]:
        """Build the 'Show the source' transparency chain for each finding."""
        ev_by_indicator: dict[str, list[Any]] = {}
        for ev in context.evidence:
            if ev.linked_entity_type == "indicator":
                ev_by_indicator.setdefault(ev.linked_entity_id, []).append(ev)

        items: list[SourceBreakdownItem] = []
        for ind in context.activated_indicators:
            linked = ev_by_indicator.get(ind.id, [])
            has_conditions = bool(context.possible_conditions)
            items.append(
                SourceBreakdownItem(
                    clinical_finding=ind.name or ind.id,
                    contributing_answer_refs=[],
                    knowledge_graph_relationship=(
                        "Indicator → Possible Condition"
                        if has_conditions
                        else "Indicator (activated by CDSE)"
                    ),
                    evidence_ids=[ev.id for ev in linked],
                    deterministic_score=ind.score,
                    trace_id=trace_id,
                )
            )
        return items


def _safe_float(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
