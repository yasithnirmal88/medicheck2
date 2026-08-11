"""Phase 1 AI explanation contracts (input + output).

These DTOs are the ONLY data that crosses into and out of the AI explanation
layer. They deliberately exclude authentication tokens, unrelated patient
records, database internals, and any field the AI does not need to explain an
already-generated deterministic report.

The deterministic CDSE / ReportService remain the source of truth; the AI only
explains their output. See MEDICHECK_AI_BASELINE.md §12-13 and
MEDICHECK_AI_PHASE1_REPORT.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Input contract: the minimal report context sent to the AI provider.
# ---------------------------------------------------------------------------


class IndicatorContext(BaseModel):
    id: str
    key: str = ""
    name: str
    description: str | None = None
    body_system_id: str | None = None
    severity: str | None = None
    evidence_strength: str | None = None
    score: float | None = None
    evidence_count: int | None = None


class ConditionContext(BaseModel):
    id: str
    code: str | None = None
    name: str
    description: str | None = None
    body_system_id: str | None = None
    severity: str | None = None
    score: float | None = None
    confidence: float | None = None


class RecommendationContext(BaseModel):
    id: str
    title: str
    text: str = ""
    category: str | None = None
    priority: int | None = None
    urgency: str | None = None
    evidence_level: str | None = None


class LaboratoryTestContext(BaseModel):
    id: str
    name: str
    description: str | None = None
    reason: str | None = None


class BodySystemContext(BaseModel):
    body_system_id: str | None = None
    name: str | None = None
    category: str | None = None
    score: float | None = None


class EvidenceContext(BaseModel):
    id: str
    title: str
    source: str | None = None
    url: str | None = None
    evidence_level: str | None = None
    summary: str | None = None


class RetrievedEvidenceContext(EvidenceContext):
    """Phase 2: an evidence record retrieved via the knowledge graph.

    Adds the deterministic retrieval metadata (relevance tier/score, the
    entity it was linked to, a bounded excerpt) so the AI and the patient can
    tell WHY this evidence was supplied. The ``id`` is the only citation id the
    AI is ever allowed to reference; the output validator enforces this.
    """

    relevance: float = 0.0
    retrieval_tier: int = 0  # 1=indicator-direct, 2=condition-transitive, 3=rec-transitive
    linked_entity_type: str = ""  # "indicator" | "condition" | "recommendation"
    linked_entity_id: str = ""
    excerpt: str = ""
    publication_year: int | None = None


class ReportExplanationContext(BaseModel):
    """Minimal, PHI-scrubbed context derived from the deterministic report.

    Every entity id in this context is the allow-list the AI may reference in
    its output. The output validator (see ``AIExplanationResponse``) rejects
    any id not present here.
    """

    trace_id: str | None = None
    severity: str | None = None
    body_systems: list[BodySystemContext] = Field(default_factory=list)
    activated_indicators: list[IndicatorContext] = Field(default_factory=list)
    possible_conditions: list[ConditionContext] = Field(default_factory=list)
    recommendations: list[RecommendationContext] = Field(default_factory=list)
    laboratory_tests: list[LaboratoryTestContext] = Field(default_factory=list)
    evidence: list[RetrievedEvidenceContext] = Field(default_factory=list)
    # True when the retrieval service found >=1 eligible evidence record. When
    # False the AI must state that no supporting evidence was available rather
    # than fabricating any.
    evidence_available: bool = False
    prompt_version: str = ""

    model_config = {"from_attributes": True}

    @property
    def allowed_indicator_ids(self) -> set[str]:
        return {i.id for i in self.activated_indicators}

    @property
    def allowed_recommendation_ids(self) -> set[str]:
        return {r.id for r in self.recommendations}

    @property
    def allowed_condition_ids(self) -> set[str]:
        return {c.id for c in self.possible_conditions}

    @property
    def allowed_evidence_ids(self) -> set[str]:
        return {e.id for e in self.evidence}


# ---------------------------------------------------------------------------
# Output contract: the validated structured explanation returned to the patient.
# ---------------------------------------------------------------------------


class KeyFinding(BaseModel):
    title: str
    explanation: str
    source_indicator_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("title", "explanation")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("finding title/explanation must not be empty")
        return v.strip()


class RecommendationExplanation(BaseModel):
    recommendation_id: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("explanation")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("recommendation explanation must not be empty")
        return v.strip()


class AIExplanationResponse(BaseModel):
    """Validated AI explanation. Raw LLM output is never trusted directly.

    The ``_validate_referenced_ids`` validator enforces the safety boundary:
    any indicator or recommendation id referenced by the AI MUST already exist
    in the supplied deterministic context. Hallucinated ids are rejected.
    """

    summary: str
    key_findings: list[KeyFinding] = Field(default_factory=list)
    severity_explanation: str = ""
    recommendation_explanations: list[RecommendationExplanation] = Field(
        default_factory=list
    )
    evidence_notes: list[str] = Field(default_factory=list)
    limitations: str = ""
    disclaimer: str
    available: bool = True
    prompt_version: str = ""
    trace_id: str | None = None
    # Phase 2 traceability / transparency: the evidence actually retrieved and
    # supplied to the AI, returned to the patient so citations are verifiable.
    retrieved_evidence: list[RetrievedEvidenceContext] = Field(default_factory=list)
    evidence_available: bool = True

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _validate_referenced_ids(self) -> "AIExplanationResponse":
        # The allow-lists are injected by the service via context. When this
        # model is constructed directly (e.g. the unavailable fallback) there
        # is nothing to validate, so we only enforce when sets were attached.
        allowed_ind = getattr(self, "_allowed_indicator_ids", None)
        allowed_rec = getattr(self, "_allowed_recommendation_ids", None)
        allowed_ev = getattr(self, "_allowed_evidence_ids", None)
        if allowed_ind is not None:
            for kf in self.key_findings:
                bad = [i for i in kf.source_indicator_ids if i not in allowed_ind]
                if bad:
                    raise ValueError(
                        f"AI referenced unknown indicator id(s): {bad}"
                    )
        if allowed_rec is not None:
            for re_ in self.recommendation_explanations:
                if re_.recommendation_id not in allowed_rec:
                    raise ValueError(
                        f"AI referenced unknown recommendation id: "
                        f"{re_.recommendation_id}"
                    )
        # Anti-hallucination: every cited evidence_id MUST be in the retrieved
        # allow-list. Hallucinated citations (e.g. "EV-999") are rejected.
        if allowed_ev is not None:
            for kf in self.key_findings:
                bad = [e for e in kf.evidence_ids if e not in allowed_ev]
                if bad:
                    raise ValueError(
                        f"AI referenced unsupplied evidence id(s): {bad}"
                    )
            for re_ in self.recommendation_explanations:
                bad = [e for e in re_.evidence_ids if e not in allowed_ev]
                if bad:
                    raise ValueError(
                        f"AI referenced unsupplied evidence id(s): {bad}"
                    )
        return self

    def bind_context(
        self,
        *,
        allowed_indicator_ids: set[str],
        allowed_recommendation_ids: set[str],
        allowed_evidence_ids: set[str] | None = None,
    ) -> "AIExplanationResponse":
        """Attach the deterministic allow-lists so the validator can run.

        Called by the service after parsing raw provider output. The evidence
        allow-list is the set of ids actually retrieved — the only citations
        the AI is permitted to use.
        """
        object.__setattr__(
            self, "_allowed_indicator_ids", allowed_indicator_ids
        )
        object.__setattr__(
            self, "_allowed_recommendation_ids", allowed_recommendation_ids
        )
        object.__setattr__(
            self, "_allowed_evidence_ids", allowed_evidence_ids or set()
        )
        # Re-run the cross-field validation now that allow-lists exist.
        return self._validate_referenced_ids()

    @field_validator("summary", "disclaimer")
    @classmethod
    def _bounded_text(cls, v: str, info: Any) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        if len(v) > 5000:
            raise ValueError(f"{info.field_name} exceeds maximum length")
        return v.strip()

    @field_validator("evidence_notes")
    @classmethod
    def _bounded_notes(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("too many evidence_notes")
        for n in v:
            if not isinstance(n, str) or len(n) > 2000:
                raise ValueError("evidence_note malformed")
        return v


# Standard fallback returned when the AI is unavailable or invalid. The
# clinical report itself remains fully available to the patient.
UNAVAILABLE_FALLBACK = AIExplanationResponse(
    summary=(
        "We couldn't generate an AI explanation for this report right now. "
        "Your clinical assessment below is unaffected and still available."
    ),
    key_findings=[],
    severity_explanation="",
    recommendation_explanations=[],
    evidence_notes=[],
    limitations=(
        "The AI explanation service is currently unavailable. This does not "
        "affect your clinical assessment, which was produced by MediCheck's "
        "deterministic clinical decision-support engine."
    ),
    disclaimer=(
        "This AI-generated explanation is based on your MediCheck assessment "
        "and does not constitute a diagnosis. The underlying assessment is "
        "generated by the deterministic clinical engine."
    ),
    available=False,
    evidence_available=False,
)

# Standard message the AI/stub must use when retrieval found no eligible
# evidence, so the patient is never led to believe supporting evidence exists.
NO_EVIDENCE_AVAILABLE_MESSAGE = (
    "No supporting evidence was available from the MediCheck evidence "
    "repository for this explanation."
)
