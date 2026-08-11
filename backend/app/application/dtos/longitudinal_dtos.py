"""Phase 4 — Longitudinal risk trajectory + change explanation DTOs.

These DTOs are the deterministic longitudinal data contract. They describe a
patient's completed assessments over time and the deterministic differences
between them. They never diagnose; they record observed changes derived from
existing immutable, timestamped, trace-ID-bearing deterministic assessment
results (``AssessmentResultModel`` + ``HealthAssessmentModel``).

AI is an EXPLANATION layer over these DTOs: it receives a context built from
the deterministic trajectory and may only reference entity ids that appear in
that context (allow-list validation, same pattern as Phase 1/2). Hallucinated
indicator/condition/recommendation/evidence ids are rejected.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TrendLabel(str):
    """Deterministic trend classification. The LLM never chooses these."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    NEW = "new"
    REMOVED = "removed"
    PERSISTENT = "persistent"
    INSUFFICIENT_DATA = "insufficient_data"


# Ordered body-system severity categories (lowest → highest severity), derived
# from the existing ``ReportService`` threshold mapping. Trend classification
# uses category transitions rather than raw numeric thresholds to avoid
# inventing incompatible score semantics.
SEVERITY_ORDER: list[str] = [
    "Normal",
    "Monitor",
    "Needs Attention",
    "Recommend Screening",
    "Urgent Medical Review",
]

#: Minimum score delta (in CDSE summed-indicator units) considered a meaningful
#: numeric change for a body system. Below this, the trend is STABLE even if
#: the category label is unchanged. Kept conservative to avoid noise.
SCORE_DELTA_THRESHOLD = 1.0


class BodySystemPoint(BaseModel):
    """A single body-system measurement at one assessment."""

    body_system_id: str | None = None
    name: str | None = None
    score: float | None = None
    category: str | None = None

    model_config = ConfigDict(extra="forbid")


class LongitudinalAssessmentPoint(BaseModel):
    """One completed assessment as a point on the trajectory.

    Derived READ-ONLY from existing deterministic results/reports.
    """

    assessment_id: str
    session_id: str
    trace_id: str | None = None
    template_id: str | None = None
    completed_at: datetime | None = None
    overall_severity: str | None = None
    body_systems: list[BodySystemPoint] = Field(default_factory=list)
    activated_indicators: list[str] = Field(default_factory=list)
    possible_conditions: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ChangeEvent(BaseModel):
    """A single deterministic change between two adjacent assessments."""

    scope: str  # body_system | indicator | condition | recommendation | overall
    ref_id: str | None = None
    label: str | None = None
    previous_value: str | None = None
    current_value: str | None = None
    previous_score: float | None = None
    current_score: float | None = None
    delta: float | None = None
    trend: str  # a TrendLabel value

    model_config = ConfigDict(extra="forbid")


class IndicatorChanges(BaseModel):
    new: list[str] = Field(default_factory=list)
    resolved: list[str] = Field(default_factory=list)
    persistent: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ConditionChanges(BaseModel):
    new: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    persistent: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class RecommendationChanges(BaseModel):
    new: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    persistent: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TrajectoryComparison(BaseModel):
    """Deterministic diff between two adjacent assessments."""

    previous: LongitudinalAssessmentPoint
    current: LongitudinalAssessmentPoint
    overall_change: ChangeEvent | None = None
    body_system_changes: list[ChangeEvent] = Field(default_factory=list)
    indicator_changes: IndicatorChanges = Field(default_factory=list)
    condition_changes: ConditionChanges = Field(default_factory=list)
    recommendation_changes: RecommendationChanges = Field(default_factory=list)
    change_events: list[ChangeEvent] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class HealthTrajectory(BaseModel):
    """The full deterministic trajectory for a patient."""

    assessments: list[LongitudinalAssessmentPoint] = Field(default_factory=list)
    comparisons: list[TrajectoryComparison] = Field(default_factory=list)
    sufficient_data: bool = False
    summary: str = ""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# AI explanation contract
# ---------------------------------------------------------------------------


class LongitudinalExplanationContext(BaseModel):
    """The deterministic context supplied to the longitudinal AI provider.

    Only entity ids present here may be referenced by the AI. The service binds
    these as allow-lists and rejects hallucinated ids.
    """

    trace_ids: list[str] = Field(default_factory=list)
    assessment_dates: list[str] = Field(default_factory=list)
    body_system_changes: list[dict[str, Any]] = Field(default_factory=list)
    indicator_changes: dict[str, list[str]] = Field(default_factory=dict)
    condition_changes: dict[str, list[str]] = Field(default_factory=dict)
    recommendation_changes: dict[str, list[str]] = Field(default_factory=dict)
    overall_change: dict[str, Any] | None = None
    retrieved_evidence: list[dict[str, Any]] = Field(default_factory=list)
    evidence_available: bool = False
    prompt_version: str = ""

    @property
    def allowed_indicator_ids(self) -> set[str]:
        return set(self.indicator_changes.get("persistent", [])) | set(
            self.indicator_changes.get("new", [])
        ) | set(self.indicator_changes.get("resolved", []))

    @property
    def allowed_condition_ids(self) -> set[str]:
        return set(self.condition_changes.get("persistent", [])) | set(
            self.condition_changes.get("new", [])
        ) | set(self.condition_changes.get("removed", []))

    @property
    def allowed_recommendation_ids(self) -> set[str]:
        return set(self.recommendation_changes.get("persistent", [])) | set(
            self.recommendation_changes.get("new", [])
        ) | set(self.recommendation_changes.get("removed", []))

    @property
    def allowed_evidence_ids(self) -> set[str]:
        return {e.get("id") for e in self.retrieved_evidence if e.get("id")}

    model_config = ConfigDict(extra="forbid")


class TrajectoryFinding(BaseModel):
    """A finding referenced by the AI explanation. Validated against allow-lists."""

    label: str
    ref_id: str | None = None
    ref_type: str | None = None  # indicator | condition | recommendation | body_system
    explanation: str = ""
    evidence_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LongitudinalExplanationResponse(BaseModel):
    """Validated AI explanation of the deterministic trajectory.

    Raw provider output is never trusted; referenced ids are validated against
    the deterministic allow-lists injected by the service.
    """

    available: bool = True
    summary: str = ""
    key_changes: list[TrajectoryFinding] = Field(default_factory=list)
    persistent_findings: list[TrajectoryFinding] = Field(default_factory=list)
    new_findings: list[TrajectoryFinding] = Field(default_factory=list)
    improved_findings: list[TrajectoryFinding] = Field(default_factory=list)
    stable_findings: list[TrajectoryFinding] = Field(default_factory=list)
    important_context: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    prompt_version: str = ""
    trace_ids: list[str] = Field(default_factory=list)
    retrieved_evidence: list[dict[str, Any]] = Field(default_factory=list)
    evidence_available: bool = False
    disclaimer: str = ""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_referenced_ids(self) -> "LongitudinalExplanationResponse":
        allowed_ind = getattr(self, "_allowed_indicator_ids", None)
        allowed_cond = getattr(self, "_allowed_condition_ids", None)
        allowed_rec = getattr(self, "_allowed_recommendation_ids", None)
        allowed_ev = getattr(self, "_allowed_evidence_ids", None)
        groups = (
            self.key_changes + self.persistent_findings + self.new_findings
            + self.improved_findings + self.stable_findings
        )
        for f in groups:
            if allowed_ind is not None and f.ref_type == "indicator" and f.ref_id:
                if f.ref_id not in allowed_ind:
                    raise ValueError(
                        f"AI referenced unknown indicator id: {f.ref_id}"
                    )
            if allowed_cond is not None and f.ref_type == "condition" and f.ref_id:
                if f.ref_id not in allowed_cond:
                    raise ValueError(
                        f"AI referenced unknown condition id: {f.ref_id}"
                    )
            if allowed_rec is not None and f.ref_type == "recommendation" and f.ref_id:
                if f.ref_id not in allowed_rec:
                    raise ValueError(
                        f"AI referenced unknown recommendation id: {f.ref_id}"
                    )
        if allowed_ev is not None:
            for f in groups:
                bad = [e for e in f.evidence_ids if e not in allowed_ev]
                if bad:
                    raise ValueError(
                        f"AI referenced unsupplied evidence id(s): {bad}"
                    )
            bad = [e for e in self.evidence_ids if e not in allowed_ev]
            if bad:
                raise ValueError(
                    f"AI referenced unsupplied evidence id(s): {bad}"
                )
        return self

    def bind_context(
        self,
        *,
        allowed_indicator_ids: set[str],
        allowed_condition_ids: set[str],
        allowed_recommendation_ids: set[str],
        allowed_evidence_ids: set[str] | None = None,
    ) -> "LongitudinalExplanationResponse":
        object.__setattr__(self, "_allowed_indicator_ids", allowed_indicator_ids)
        object.__setattr__(self, "_allowed_condition_ids", allowed_condition_ids)
        object.__setattr__(self, "_allowed_recommendation_ids", allowed_recommendation_ids)
        object.__setattr__(self, "_allowed_evidence_ids", allowed_evidence_ids or set())
        return self._validate_referenced_ids()

    @field_validator("disclaimer")
    @classmethod
    def _non_empty_disclaimer(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("disclaimer is required")
        return v


#: Diagnostic-language guard: candidate finding explanations must not read as a
#: diagnosis (same safety principle as Phase 3 intake). The AI explains observed
#: deterministic changes; it never states a disease is present/progressing.
_DIAGNOSTIC_RE = re.compile(
    r"\b(you have|diagnosed with|disease (is )?(getting worse|progressing|resolved)|"
    r"confirmed condition|will develop|chance of developing)\b",
    re.IGNORECASE,
)


def assert_non_diagnostic(text: str) -> str:
    """Raise if text reads as a diagnosis/prediction. Used by the stub provider."""
    if _DIAGNOSTIC_RE.search(text or ""):
        raise ValueError("explanation reads as a diagnosis or prediction")
    return text


def trajectory_unavailable_fallback(
    *, trace_ids: list[str], evidence: list[dict[str, Any]] | None = None
) -> LongitudinalExplanationResponse:
    """Safe fallback when the longitudinal AI is unavailable or invalid.

    The deterministic trajectory remains fully available to the caller.
    """
    return LongitudinalExplanationResponse(
        available=False,
        summary=(
            "We couldn't generate an AI explanation of your assessment changes "
            "right now. Your assessment history and deterministic results remain "
            "available."
        ),
        important_context=[
            "The AI longitudinal explanation is currently unavailable. "
            "This does not affect your clinical assessment history, which was "
            "produced by MediCheck's deterministic clinical decision-support engine."
        ],
        evidence_ids=[],
        retrieved_evidence=evidence or [],
        evidence_available=bool(evidence),
        prompt_version="",
        trace_ids=trace_ids,
        disclaimer=(
            "This AI-generated explanation summarizes changes in your assessment "
            "history and does not diagnose conditions or replace professional "
            "medical advice."
        ),
    )
