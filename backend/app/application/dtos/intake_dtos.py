"""Phase 3 — AI Clinical Intake DTOs.

Strongly-typed contracts for AI-assisted natural-language intake and candidate
clinical-indicator extraction.

Architectural boundary (Phase 3): the AI is an INPUT INTERPRETATION layer
only. It extracts structured observations from patient free text and maps them
to EXISTING clinical indicators in the knowledge graph. It never diagnoses,
scores, sets severity, activates indicators, creates recommendations/evidence,
or invents clinical entities. The deterministic CDSE remains the clinical
decision layer.

All AI output is session-scoped and validated against the authoritative
knowledge graph before it can influence question selection or the assessment
pipeline. Unknown / hallucinated indicator IDs are rejected (allow-list
validation, same pattern as Phase 1/2).
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constrained vocabularies
# ---------------------------------------------------------------------------

Polarity = Literal["positive", "negative", "uncertain"]
Certainty = Literal["reported", "suspected", "uncertain"]
Temporality = Literal["current", "recent", "historical", "recurring", "unknown"]
ObservationType = Literal[
    "symptom", "history", "behavior", "measurement", "context", "other"
]

# A safe fallback shown when AI intake is unavailable. The standard questionnaire
# remains fully functional regardless of AI availability.
INTAKE_UNAVAILABLE_MESSAGE = (
    "AI-assisted intake is currently unavailable. You can continue with the "
    "standard questionnaire."
)

#: Markers indicating a clarification question was synthesized rather than
#: sourced from the CMS knowledge graph. Only informational clarifications are
#: permitted; never diagnostic, never suggesting an answer.
CLARIFICATION_SOURCE_AI = "ai_generated"
CLARIFICATION_SOURCE_CMS = "cms"


# ---------------------------------------------------------------------------
# Indicator catalog (bounded view passed to the provider)
# ---------------------------------------------------------------------------


class IndicatorCatalogEntry(BaseModel):
    """A single active, non-deleted clinical indicator in the bounded catalog.

    The catalog is the controlled vocabulary the AI may reference. The AI may
    ONLY cite ``indicator_id`` values present in the supplied catalog — it can
    never invent an indicator.
    """

    model_config = ConfigDict(frozen=True)

    indicator_id: str
    key: str
    name: str
    body_system_id: str
    description: str | None = None


class IndicatorCatalog(BaseModel):
    """Bounded catalog of active, non-deleted clinical indicators.

    The catalog is retrieved deterministically (Phase 3 first implementation)
    and bounded so the entire knowledge graph is never dumped blindly into a
    provider request. A coarse deterministic candidate sub-selection may trim
    the catalog before the AI sees it; the provider still cannot cite IDs
    outside it.
    """

    entries: list[IndicatorCatalogEntry] = Field(default_factory=list)

    def allowed_ids(self) -> set[str]:
        return {e.indicator_id for e in self.entries}

    def by_id(self) -> dict[str, IndicatorCatalogEntry]:
        return {e.indicator_id: e for e in self.entries}


# ---------------------------------------------------------------------------
# Structured observation
# ---------------------------------------------------------------------------


class ObservationDTO(BaseModel):
    """A structured observation extracted from patient free text.

    Observations are NOT diagnoses. They are normalized representations of what
    the patient reported, including polarity (negation), temporality, and
    certainty — so the deterministic engine never treats a negated or
    historical mention as a current positive finding.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    source_text: str = Field(..., min_length=1, description="verbatim patient span")
    normalized_concept: str = Field(..., min_length=1, description="e.g. exertional fatigue")
    observation_type: ObservationType = "symptom"
    certainty: Certainty = "reported"
    temporality: Temporality = "current"
    polarity: Polarity = "positive"
    severity_description: str | None = Field(
        default=None,
        description="patient-described severity wording, NOT a clinical severity",
    )
    duration: str | None = None
    frequency: str | None = None
    context: str | None = None
    body_system: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("source_text", "normalized_concept")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be non-empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Candidate indicator
# ---------------------------------------------------------------------------


class CandidateIndicatorDTO(BaseModel):
    """A candidate mapping from observations to an EXISTING indicator.

    Rules enforced structurally + by the validation service:
    - ``indicator_id`` MUST exist in the active, non-deleted catalog.
    - ``confidence`` is an EXTRACTION confidence, bounded [0,1]. It is NOT a
      clinical probability and MUST NOT be used as a CDSE score.
    - ``observation_ids`` MUST reference observations from the same intake.
    - The AI cannot assign deterministic score values or clinical severity.
    """

    model_config = ConfigDict(extra="forbid")

    indicator_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    observation_ids: list[str] = Field(default_factory=list)
    reason: str = ""
    uncertainty: str | None = None
    source: str = "ai_extraction"


# ---------------------------------------------------------------------------
# Question / clarification discovery output
# ---------------------------------------------------------------------------


class CandidateQuestionDTO(BaseModel):
    """An EXISTING question discovered from candidate indicators via the
    knowledge graph. The AI never invents these; they come from the CMS graph.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str
    question_code: str
    text: str
    question_group_id: str
    question_group_name: str
    body_system_id: str | None = None
    linked_indicator_ids: list[str] = Field(default_factory=list)
    source: Literal["cms"] = "cms"


class CandidateQuestionGroupDTO(BaseModel):
    """An EXISTING question group discovered from candidate indicators.

    Used by the frontend to recommend a matching assessment / entry point. The
    deterministic branching engine still owns final question order.
    """

    model_config = ConfigDict(extra="forbid")

    question_group_id: str
    code: str
    name: str
    body_system_id: str | None = None
    linked_indicator_ids: list[str] = Field(default_factory=list)
    question_count: int = 0
    source: Literal["cms"] = "cms"


class ClarificationDTO(BaseModel):
    """A clarification prompt.

    ``source="cms"`` when drawn from an existing question; ``source="ai_generated"``
    when synthesized as informational clarification. Generated clarifications
    must be informational only — never diagnostic, never suggesting an answer.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    source: Literal["ai_generated", "cms"] = "ai_generated"
    observation_id: str | None = None
    linked_indicator_id: str | None = None
    linked_question_id: str | None = None


# ---------------------------------------------------------------------------
# Provider raw output (validated by the service)
# ---------------------------------------------------------------------------


class ProviderObservationRaw(BaseModel):
    """Raw observation as emitted by the provider, before service validation."""

    model_config = ConfigDict(extra="ignore")

    source_text: str
    normalized_concept: str
    observation_type: ObservationType = "symptom"
    certainty: Certainty = "reported"
    temporality: Temporality = "current"
    polarity: Polarity = "positive"
    severity_description: str | None = None
    duration: str | None = None
    frequency: str | None = None
    context: str | None = None
    body_system: str | None = None
    confidence: float = 0.5


class ProviderCandidateRaw(BaseModel):
    """Raw candidate indicator as emitted by the provider, before validation."""

    model_config = ConfigDict(extra="ignore")

    indicator_id: str
    confidence: float = 0.5
    observation_ids: list[str] = Field(default_factory=list)
    reason: str = ""
    uncertainty: str | None = None
    source: str = "ai_extraction"


class ProviderOutput(BaseModel):
    """Parsed (but not yet knowledge-graph-validated) provider output.

    The service layer parses the provider's JSON string into this model. Any
    malformed structure raises here → safe fallback. Unknown indicator IDs
    are filtered by the validation service next.
    """

    model_config = ConfigDict(extra="ignore")

    observations: list[ProviderObservationRaw] = Field(default_factory=list)
    candidates: list[ProviderCandidateRaw] = Field(default_factory=list)
    clarifications: list[ClarificationDTO] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        # Accept a bare list as the candidate observations list for robustness.
        if isinstance(v, list):
            return {"observations": v, "candidates": [], "clarifications": []}
        return v


# ---------------------------------------------------------------------------
# Intake context (input to the provider)
# ---------------------------------------------------------------------------


class IntakeRequestContext(BaseModel):
    """Input context handed to the provider. Contains only what is necessary:
    the patient message, a pseudonymous session reference, and a bounded
    indicator catalog. No PHI beyond the patient's own message, no auth tokens,
    no unrelated patient records, no internal DB credentials.
    """

    model_config = ConfigDict(extra="forbid")

    session_ref: str = Field(..., description="pseudonymous/session identifier")
    patient_message: str = Field(..., min_length=1)
    catalog: IndicatorCatalog
    prompt_version: str
    available_question_group_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Final API response
# ---------------------------------------------------------------------------


class IntakeResponse(BaseModel):
    """Final validated intake response returned by the API.

    ``available=false`` on any provider/parse failure — the standard
    questionnaire remains functional. Unknown / hallucinated indicator IDs are
    absent from ``candidate_indicators`` (rejected by validation). Every
    candidate references only validated observations from this intake.
    """

    model_config = ConfigDict(from_attributes=True)

    trace_id: str
    prompt_version: str
    observations: list[ObservationDTO] = Field(default_factory=list)
    candidate_indicators: list[CandidateIndicatorDTO] = Field(default_factory=list)
    candidate_question_groups: list[CandidateQuestionGroupDTO] = Field(default_factory=list)
    candidate_questions: list[CandidateQuestionDTO] = Field(default_factory=list)
    clarifications: list[ClarificationDTO] = Field(default_factory=list)
    available: bool = True
    message: str | None = None

    @field_validator("candidate_indicators")
    @classmethod
    def _no_diagnostic_language(cls, v: list[CandidateIndicatorDTO]) -> list[CandidateIndicatorDTO]:
        # Defensive: candidate reasons must not read as diagnoses. The provider
        # prompt forbids this; this is a belt-and-braces guard.
        forbidden = ("diagnosed", "you have", "confirmed condition", "disease confirmed")
        for c in v:
            low = (c.reason or "").lower()
            if any(p in low for p in forbidden):
                raise ValueError(f"candidate reason must not read as a diagnosis: {c.reason!r}")
        return v

    @model_validator(mode="after")
    def _unavailable_consistency(self) -> IntakeResponse:
        if not self.available and self.candidate_indicators:
            # When unavailable, never surface candidates.
            raise ValueError("available=false must not carry candidate indicators")
        return self


def safe_intake_response(trace_id: str, prompt_version: str) -> IntakeResponse:
    """Build the safe fallback response used on any provider failure."""
    return IntakeResponse(
        trace_id=trace_id,
        prompt_version=prompt_version,
        available=False,
        message=INTAKE_UNAVAILABLE_MESSAGE,
    )


def new_trace_id() -> str:
    """Generate a new intake trace id."""
    return uuid.uuid4().hex


def parse_provider_json(raw: str) -> ProviderOutput:
    """Parse a provider JSON string into ProviderOutput.

    Accepts either a ``{"observations": [...], "candidates": [...]}`` object
    or a bare ``[...]`` array of observations (robustness). Raises on
    malformed JSON or schema violations so the service can fall back safely.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"provider returned malformed JSON: {exc}") from exc
    # Pydantic will coerce acceptable shapes and reject unacceptable ones.
    return ProviderOutput.model_validate(data)


# Regex guard for the candidate-reason diagnostic-language check; kept as a
# module-level constant so tests / prompts can reference the same rule.
DIAGNOSTIC_LANGUAGE_RE = re.compile(
    r"\b(diagnos(ed|is|tic)|you (have|are)|confirmed (condition|disease))\b",
    re.IGNORECASE,
)
