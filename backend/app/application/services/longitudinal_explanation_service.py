"""Phase 4 — Longitudinal AI explanation application service.

Builds a deterministic trajectory for the caller (via
``LongitudinalAnalysisService``), assembles a minimal, PHI-scrubbed
``LongitudinalExplanationContext`` from the deterministic changes, retrieves
approved evidence via the existing Phase 2 ``EvidenceRetrievalService``
(deterministic; the AI never chooses evidence), calls the configured
``LongitudinalExplanationProvider``, and validates the raw output against the
deterministic allow-lists (rejects hallucinated
indicator/condition/recommendation/evidence ids).

AI failure and retrieval failure NEVER break the deterministic trajectory: on
any provider/validation error the service returns the safe
``trajectory_unavailable_fallback`` (available=False). The deterministic
trajectory remains fully available to the caller.

The deterministic CDSE / ReportService are not modified or re-invoked here.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.longitudinal_prompts import LONGITUDINAL_PROMPT_VERSION
from app.application.ai.longitudinal_provider import (
    AIProviderError,
    LongitudinalExplanationProvider,
    get_longitudinal_provider,
)
from app.application.dtos.longitudinal_dtos import (
    LongitudinalExplanationContext,
    LongitudinalExplanationResponse,
    TrajectoryFinding,
    trajectory_unavailable_fallback,
)
from app.application.services.evidence_retrieval_service import (
    EvidenceRetrievalService,
)
from app.application.services.longitudinal_analysis_service import (
    LongitudinalAnalysisService,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class LongitudinalExplanationService:
    def __init__(
        self,
        session: AsyncSession,
        provider: LongitudinalExplanationProvider | None = None,
        retrieval_service: EvidenceRetrievalService | None = None,
        analysis_service: LongitudinalAnalysisService | None = None,
    ) -> None:
        self.session = session
        self.analysis = analysis_service or LongitudinalAnalysisService(session)
        self.retrieval = retrieval_service or EvidenceRetrievalService(session)
        self.provider = provider or get_longitudinal_provider()

    async def explain_trajectory(
        self,
        user_id: str,
        *,
        previous_session_id: str | None = None,
        current_session_id: str | None = None,
    ) -> LongitudinalExplanationResponse:
        """Return a validated AI explanation of the caller's trajectory.

        If specific session ids are supplied, the explanation covers that pair
        (ownership-verified); otherwise it covers the latest two completed
        assessments. With insufficient data (< 2 assessments) the AI is NOT
        called — a safe insufficient-data response is returned.
        """
        trajectory = await self.analysis.get_trajectory(user_id)
        if not trajectory.sufficient_data:
            return _insufficient_data_response(trajectory)

        # Determine which comparison to explain.
        if previous_session_id and current_session_id:
            comparison = await self.analysis.compare_specific(
                user_id, previous_session_id, current_session_id
            )
            if comparison is None:
                # Not owned / not found.
                return _insufficient_data_response(trajectory)
        else:
            comparison = trajectory.comparisons[-1]

        context = await self._build_context(comparison)
        try:
            raw = await self.provider.explain_trajectory(context)
            response = self._parse_and_validate(raw, context)
            response.trace_ids = context.trace_ids
            response.retrieved_evidence = context.retrieved_evidence
            response.evidence_available = context.evidence_available
            return response
        except AIProviderError as exc:
            logger.warning("Longitudinal AI unavailable: %s", exc)
            return trajectory_unavailable_fallback(
                trace_ids=context.trace_ids, evidence=context.retrieved_evidence
            )
        except Exception as exc:
            logger.warning("Longitudinal AI invalid: %s", exc)
            return trajectory_unavailable_fallback(
                trace_ids=context.trace_ids, evidence=context.retrieved_evidence
            )

    async def _build_context(self, comparison) -> LongitudinalExplanationContext:
        prev = comparison.previous
        curr = comparison.current
        # Collect all entity ids across both points for evidence retrieval.
        ind_ids = list(set(prev.activated_indicators) | set(curr.activated_indicators))
        cond_ids = list(set(prev.possible_conditions) | set(curr.possible_conditions))
        rec_ids = list(set(prev.recommendations) | set(curr.recommendations))

        # Phase 2 deterministic evidence retrieval (the AI never chooses).
        retrieved_evidence: list[dict[str, Any]] = []
        try:
            if ind_ids or cond_ids or rec_ids:
                result = await self.retrieval.retrieve(
                    indicator_ids=ind_ids,
                    condition_ids=cond_ids,
                    recommendation_ids=rec_ids,
                    indicator_labels={},
                    condition_labels={},
                    recommendation_labels={},
                )
                retrieved_evidence = [
                    ev.model_dump() for ev in result.evidence
                ]
        except Exception as exc:
            logger.warning("Evidence retrieval failed for trajectory: %s", exc)
            retrieved_evidence = []

        body_changes = [c.model_dump() for c in comparison.body_system_changes]
        overall = comparison.overall_change.model_dump() if comparison.overall_change else None

        return LongitudinalExplanationContext(
            trace_ids=[t for t in (prev.trace_id, curr.trace_id) if t],
            assessment_dates=[
                _fmt(prev.completed_at),
                _fmt(curr.completed_at),
            ],
            body_system_changes=body_changes,
            indicator_changes=comparison.indicator_changes.model_dump(),
            condition_changes=comparison.condition_changes.model_dump(),
            recommendation_changes=comparison.recommendation_changes.model_dump(),
            overall_change=overall,
            retrieved_evidence=retrieved_evidence,
            evidence_available=bool(retrieved_evidence),
            prompt_version=LONGITUDINAL_PROMPT_VERSION,
        )

    def _parse_and_validate(
        self, raw: str, context: LongitudinalExplanationContext
    ) -> LongitudinalExplanationResponse:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIProviderError("non-JSON AI output") from exc
        if not isinstance(data, dict):
            raise AIProviderError("AI output is not a JSON object")
        if len(json.dumps(data)) > 50000:
            raise AIProviderError("AI output too large")

        def _findings(key: str) -> list[TrajectoryFinding]:
            return [TrajectoryFinding(**f) for f in (data.get(key, []) or [])]

        response = LongitudinalExplanationResponse(
            available=bool(data.get("available", True)),
            summary=str(data.get("summary", "")).strip(),
            key_changes=_findings("key_changes"),
            persistent_findings=_findings("persistent_findings"),
            new_findings=_findings("new_findings"),
            improved_findings=_findings("improved_findings"),
            stable_findings=_findings("stable_findings"),
            important_context=[str(x) for x in (data.get("important_context", []) or [])],
            evidence_ids=[str(e) for e in (data.get("evidence_ids", []) or [])],
            prompt_version=LONGITUDINAL_PROMPT_VERSION,
            trace_ids=context.trace_ids,
            retrieved_evidence=context.retrieved_evidence,
            evidence_available=context.evidence_available,
            disclaimer=str(data.get("disclaimer", "") or ""),
        )
        response.bind_context(
            allowed_indicator_ids=context.allowed_indicator_ids,
            allowed_condition_ids=context.allowed_condition_ids,
            allowed_recommendation_ids=context.allowed_recommendation_ids,
            allowed_evidence_ids=context.allowed_evidence_ids,
        )
        return response


def _fmt(dt) -> str:
    return dt.isoformat() if dt else ""


def _insufficient_data_response(trajectory) -> LongitudinalExplanationResponse:
    return LongitudinalExplanationResponse(
        available=False,
        summary=trajectory.summary or "Not enough historical data for a trajectory.",
        important_context=[
            "At least two completed assessments are needed before the AI can "
            "explain changes over time."
        ],
        evidence_ids=[],
        retrieved_evidence=[],
        evidence_available=False,
        prompt_version=LONGITUDINAL_PROMPT_VERSION,
        trace_ids=[],
        disclaimer=(
            "This AI-generated explanation summarizes changes in your assessment "
            "history and does not diagnose conditions or replace professional "
            "medical advice."
        ),
    )
