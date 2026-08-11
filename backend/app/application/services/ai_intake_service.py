"""AI clinical-intake extraction service (Phase 3).

Orchestrates the Phase 3 intake pipeline:

    patient text
        → bounded indicator catalog (deterministic, active+non-deleted)
        → AIClinicalIntakeProvider (stub by default)
        → parse provider JSON
        → build ObservationDTO list (negation/temporality preserved)
        → CandidateValidationService (reject unknown/inactive/deleted IDs)
        → AIIntakeQuestionService (existing questions/groups from the graph)
        → IntakeResponse (session-scoped, never persisted to the global graph)

The AI is an INPUT INTERPRETATION layer. It never diagnoses, scores, sets
severity, activates indicators, or creates clinical content. The deterministic
CDSE remains the clinical decision layer; intake output converges on the
existing questionnaire/CDSE pipeline, it does not replace it.

Traceability: every run carries a ``trace_id``. Safe metrics are recorded via
the logger; raw patient text is NOT logged by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ai.intake_prompts import INTAKE_PROMPT_VERSION
from app.application.ai.intake_provider import (
    AIIntakeProviderError,
    get_intake_provider,
)
from app.application.dtos.intake_dtos import (
    CandidateIndicatorDTO,
    CandidateQuestionDTO,
    CandidateQuestionGroupDTO,
    ClarificationDTO,
    IndicatorCatalog,
    IndicatorCatalogEntry,
    IntakeRequestContext,
    IntakeResponse,
    ObservationDTO,
    ProviderObservationRaw,
    ProviderOutput,
    new_trace_id,
    parse_provider_json,
    safe_intake_response,
)
from app.application.services.intake_question_service import AIIntakeQuestionService
from app.application.services.intake_validation_service import (
    CandidateValidationService,
    ValidationTrace,
)
from app.core.logging import get_logger
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)

logger = get_logger(__name__)

#: Bound on the indicator catalog handed to the provider. Keeps prompts bounded
#: even as the knowledge graph grows. Deterministic sub-selection; no vector DB.
CATALOG_LIMIT = 60


@dataclass
class IntakeTrace:
    trace_id: str
    prompt_version: str
    provider: str
    model: str
    observations_count: int = 0
    candidate_count: int = 0
    validated_count: int = 0
    rejected: ValidationTrace | None = None
    question_groups_count: int = 0
    questions_count: int = 0
    clarifications_count: int = 0
    available: bool = True
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_log_dict(self) -> dict[str, Any]:
        # Raw patient text is intentionally NOT included.
        return {
            "trace_id": self.trace_id,
            "prompt_version": self.prompt_version,
            "provider": self.provider,
            "model": self.model,
            "observations": self.observations_count,
            "candidates": self.candidate_count,
            "validated": self.validated_count,
            "rejected_total": (self.rejected.total_rejected if self.rejected else 0),
            "question_groups": self.question_groups_count,
            "questions": self.questions_count,
            "clarifications": self.clarifications_count,
            "available": self.available,
            "error": self.error,
        }


class AIIntakeService:
    """Orchestrates the Phase 3 intake pipeline. Session-scoped, never writes
    to the global knowledge graph.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        provider: Any | None = None,
        validator: CandidateValidationService | None = None,
        question_service: AIIntakeQuestionService | None = None,
        catalog_limit: int = CATALOG_LIMIT,
    ) -> None:
        self.session = session
        self.provider = provider or get_intake_provider()
        self.validator = validator or CandidateValidationService()
        self.question_service = question_service or AIIntakeQuestionService(session)
        self.catalog_limit = max(1, int(catalog_limit))
        self.trace: IntakeTrace | None = None

    async def extract(self, text: str, *, session_ref: str) -> IntakeResponse:
        trace_id = new_trace_id()
        if not text or not text.strip():
            self.trace = IntakeTrace(
                trace_id=trace_id,
                prompt_version=INTAKE_PROMPT_VERSION,
                provider=self.provider.name,
                model="",
                available=False,
                error="empty patient text",
            )
            logger.info("intake empty text: %s", self.trace.to_log_dict())
            return safe_intake_response(trace_id, INTAKE_PROMPT_VERSION)

        catalog = await self._build_catalog()
        ctx = IntakeRequestContext(
            session_ref=session_ref,
            patient_message=text.strip(),
            catalog=catalog,
            prompt_version=INTAKE_PROMPT_VERSION,
        )

        trace = IntakeTrace(
            trace_id=trace_id,
            prompt_version=INTAKE_PROMPT_VERSION,
            provider=getattr(self.provider, "name", "unknown"),
            model="",
        )

        # 1. Provider extraction (failure → safe fallback).
        try:
            raw = await self.provider.extract_candidates(ctx)
            parsed = parse_provider_json(raw)
        except (AIIntakeProviderError, ValueError) as exc:
            trace.available = False
            trace.error = f"provider/parse failure: {exc}"
            self.trace = trace
            logger.warning("intake provider failure: %s", trace.to_log_dict())
            return safe_intake_response(trace_id, INTAKE_PROMPT_VERSION)
        except Exception as exc:  # pragma: no cover - defensive
            trace.available = False
            trace.error = f"unexpected: {exc}"
            self.trace = trace
            logger.warning("intake unexpected failure: %s", trace.to_log_dict())
            return safe_intake_response(trace_id, INTAKE_PROMPT_VERSION)

        trace.observations_count = len(parsed.observations)
        trace.candidate_count = len(parsed.candidates)

        # 2. Build validated ObservationDTO list.
        observations = _build_observations(parsed)
        # Clarifications: carry through (already informational-only DTOs).
        clarifications = list(parsed.clarifications)

        # 3. Validate candidate indicators against the authoritative catalog.
        vtrace = self.validator.validate(parsed, catalog, observations)
        trace.rejected = vtrace
        trace.validated_count = len(vtrace.accepted)
        candidates = vtrace.accepted

        # 4. Discover existing questions/groups from validated candidates.
        discovery = await self.question_service.discover([c.indicator_id for c in candidates])
        trace.question_groups_count = len(discovery.question_groups)
        trace.questions_count = len(discovery.questions)
        trace.clarifications_count = len(clarifications)

        self.trace = trace
        logger.info("intake completed: %s", trace.to_log_dict())

        return IntakeResponse(
            trace_id=trace_id,
            prompt_version=INTAKE_PROMPT_VERSION,
            observations=observations,
            candidate_indicators=candidates,
            candidate_question_groups=discovery.question_groups,
            candidate_questions=discovery.questions,
            clarifications=clarifications,
            available=True,
            message=None,
        )

    async def _build_catalog(self) -> IndicatorCatalog:
        """Bounded catalog of active, non-deleted indicators.

        Deterministic retrieval (no vector DB). Ordered by name for stable,
        reproducible output. The provider may only cite IDs in this catalog.
        """
        stmt = (
            select(ClinicalIndicatorModel)
            .where(
                ClinicalIndicatorModel.is_active.is_(True),
                ClinicalIndicatorModel.deleted_at.is_(None),
            )
            .order_by(ClinicalIndicatorModel.name)
            .limit(self.catalog_limit)
        )
        result = await self.session.execute(stmt)
        entries = [
            IndicatorCatalogEntry(
                indicator_id=m.id,
                key=m.key,
                name=m.name,
                body_system_id=m.body_system_id,
                description=m.description,
            )
            for m in result.scalars().all()
        ]
        return IndicatorCatalog(entries=entries)


def _build_observations(parsed: ProviderOutput) -> list[ObservationDTO]:
    """Convert raw provider observations into validated DTOs, preserving
    negation, temporality, and certainty. Bounded to avoid runaway output.
    """
    out: list[ObservationDTO] = []
    for raw in parsed.observations[:30]:
        if not isinstance(raw, ProviderObservationRaw):
            continue
        try:
            out.append(
                ObservationDTO(
                    source_text=raw.source_text,
                    normalized_concept=raw.normalized_concept,
                    observation_type=raw.observation_type,
                    certainty=raw.certainty,
                    temporality=raw.temporality,
                    polarity=raw.polarity,
                    severity_description=raw.severity_description,
                    duration=raw.duration,
                    frequency=raw.frequency,
                    context=raw.context,
                    body_system=raw.body_system,
                    confidence=raw.confidence,
                )
            )
        except Exception:  # pragma: no cover - defensive drop
            continue
    return out
