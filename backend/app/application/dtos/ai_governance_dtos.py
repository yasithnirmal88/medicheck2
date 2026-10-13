"""Phase 11 — Governed AI care-coordination & equity intelligence DTOs.

All population/equity/SDG DTOs are de-identified and operate ONLY on
already-aggregated, k-anonymity-suppressed metrics. No patient identifiers
(user_id, email, session_id, trace_id, names, phone numbers, addresses,
emergency contacts, or raw questionnaire answers) appear in any AI context.

The AI never determines clinical priority, severity, probability, or urgency.
``operational_priority_score`` has NO clinical meaning — it only ranks
administrative workload and is documented as such.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Quality + review lifecycle enums (mirror the model string columns) ──

AiInsightQualityStatus = Literal[
    "valid",
    "insufficient_data",
    "validation_failed",
    "provider_unavailable",
    "review_required",
    "rejected",
]

ReviewStatus = Literal[
    "generated",
    "pending_review",
    "approved",
    "rejected",
    "edited",
    "published",
]

ReviewAction = Literal["approve", "reject", "edit"]

InsightType = Literal["equity", "sdg_narrative"]

# Operational reason codes the AI may emit. Closed set — anything else is
# rejected by the provider.
OperationalReasonCode = Literal[
    "overdue",
    "missing_follow_up",
    "aged_referral",
    "appointment_window",
    "unresolved_admin",
    "unsuccessful_contact",
    "facility_unresponsive",
    "offline_pending_sync",
    "no_outstanding_flags",
]

# ── Feature A: Operational CHW coordination ─────────────────────────────


class OperationalQueueContext(BaseModel):
    """PHI-scrubbed operational context for ONE follow-up task.

    Contains ONLY operational/administrative factors. Clinical fields (severity,
    probability, possible condition, score, diagnosis, urgency) are
    intentionally ABSENT. The deterministic clinical priority (if any) is
    already separately available to the CHW and is NEVER re-ranked by AI.
    """

    task_id: str
    referral_age_days: float
    overdue_days: float | None = None
    contact_attempts: int = 0
    facility_status: str | None = None
    appointment_status: str | None = None
    communication_status: str | None = None
    language: str | None = None
    offline_status: str | None = None


class OperationalQueueSuggestion(BaseModel):
    """AI suggestion for ONE task. Operational only — never clinical."""

    task_id: str
    operational_reason_codes: list[OperationalReasonCode] = []
    explanation: str
    # Operational priority in [0,1]. NO clinical meaning.
    operational_priority_score: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    requires_human_review: bool = True


class OperationalSuggestionBatchResponse(BaseModel):
    available: bool = True
    suggestions: list[OperationalQueueSuggestion] = []
    provider: str = "stub"
    model: str = ""
    prompt_version: str = "1.0-operational-phase11"
    quality_status: AiInsightQualityStatus = "valid"
    quality_reason: str | None = None
    transparency_notice: str = (
        "AI suggestions are administrative assistance only. They do not "
        "determine clinical priority, urgency, or diagnosis."
    )
    # Persisted suggestion records (with review lifecycle) for the CHW.
    records: list[OperationalSuggestionRecord] = []


class OperationalSuggestionRecord(BaseModel):
    """A persisted operational suggestion with its review lifecycle."""

    id: str
    chw_user_id: str
    task_id: str
    operational_reason_codes: list[str] = []
    explanation: str
    operational_priority_score: float
    requires_human_review: bool
    provider: str
    model: str
    prompt_version: str
    quality_status: str
    quality_reason: str | None = None
    review_status: ReviewStatus
    reviewer_id: str | None = None
    reviewer_comment: str | None = None
    edited_output: str | None = None
    approved_at: str | None = None
    created_at: str | None = None


# ── Feature B: Equity intelligence ──────────────────────────────────────


class EquityMetricContext(BaseModel):
    """One de-identified aggregate metric the AI may describe.

    ``label`` is treated as UNTRUSTED data (prompt-injection defense): the AI
    must never treat it as an instruction. ``value``/``numerator``/
    ``denominator`` are already k-suppressed.
    """

    label: str
    metric_type: str | None = None
    value: float | None = None
    numerator: int | None = None
    denominator: int | None = None
    suppressed: bool = False
    comparison: str | None = None


class EquityInsightContext(BaseModel):
    """De-identified aggregate context for equity intelligence.

    Contains ONLY already-suppressed aggregate metrics. No patient ids/names.
    """

    dimension: str  # e.g. "language", "modality", "geography", "facility"
    period_start: str | None = None
    period_end: str | None = None
    metrics: list[EquityMetricContext] = []


class EquityFinding(BaseModel):
    statement: str  # an OBSERVED fact derived only from supplied metrics
    metric_labels: list[str] = []  # allow-list: must be subset of context labels


class EquityInterpretation(BaseModel):
    # A POSSIBLE (non-causal) operational explanation. Explicitly NOT a claim
    # of disease prevalence or causation.
    interpretation: str
    is_observed: bool = False  # True = observed; False = possible explanation


class EquityInsightOutput(BaseModel):
    observed_findings: list[EquityFinding] = []
    possible_interpretations: list[EquityInterpretation] = []
    limitations: str
    requires_human_review: bool = True


# ── Feature C: SDG / population narrative ───────────────────────────────


class SdgNarrativeContext(BaseModel):
    """De-identified SDG metric rows the AI may describe.

    The AI may ONLY describe metrics supplied here. Any metric/indicator it
    references that is not in this allow-list is REJECTED.
    """

    target: str  # e.g. "3.4", "3.8", "10"
    period_start: str | None = None
    period_end: str | None = None
    rows: list[EquityMetricContext] = []  # reuse the metric shape


class SdgNarrativeOutput(BaseModel):
    target: str
    reporting_period: str | None = None
    population_scope: str = "MediCheck platform users (de-identified aggregate)"
    metrics_used: list[str] = []  # allow-list subset
    observed_trends: list[str] = []
    limitations: str
    possible_operational_interpretation: str
    requires_human_review: bool = True


# ── Feature D: Review workflow + persisted insight records ──────────────


class ReviewRequest(BaseModel):
    action: ReviewAction
    reviewer_comment: str | None = None
    edited_output: str | None = None  # required when action == "edit"


class PopulationInsightRecord(BaseModel):
    """A persisted population/equity/SDG insight with its review lifecycle."""

    id: str
    insight_type: InsightType
    target: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    narrative: str
    observed_findings: list[Any] | None = None
    possible_interpretations: list[Any] | None = None
    limitations: str | None = None
    requires_human_review: bool
    provider: str
    model: str
    prompt_version: str
    quality_status: str
    quality_reason: str | None = None
    review_status: ReviewStatus
    reviewer_id: str | None = None
    reviewer_comment: str | None = None
    edited_output: str | None = None
    approved_at: str | None = None
    created_at: str | None = None


class InsightReviewResponse(BaseModel):
    id: str
    insight_type: Literal["operational", "equity", "sdg_narrative"]
    review_status: ReviewStatus
    reviewer_id: str
    reviewer_comment: str | None = None
    edited_output: str | None = None
    approved_at: str | None = None


class EquityInsightResponse(BaseModel):
    available: bool = True
    insight: EquityInsightOutput | None = None
    record: PopulationInsightRecord | None = None
    provider: str = "stub"
    prompt_version: str = "1.0-equity-phase11"
    quality_status: AiInsightQualityStatus = "valid"
    quality_reason: str | None = None
    transparency_notice: str = (
        "AI-generated population summaries are derived from aggregated, "
        "de-identified metrics and require human review. They do not infer "
        "disease prevalence or causation."
    )


class SdgNarrativeResponse(BaseModel):
    available: bool = True
    narratives: list[SdgNarrativeOutput] = []
    records: list[PopulationInsightRecord] = []
    provider: str = "stub"
    prompt_version: str = "1.0-sdg-narrative-phase11"
    quality_status: AiInsightQualityStatus = "valid"
    quality_reason: str | None = None
    transparency_notice: str = (
        "AI-generated SDG narratives describe supplied aggregate metrics only "
        "and require human review. They do not prove an SDG target has been "
        "achieved and are not official UN SDG indicators."
    )


# Forward-reference resolution: OperationalSuggestionBatchResponse references
# OperationalSuggestionRecord which is defined later in this module.
OperationalSuggestionBatchResponse.model_rebuild()
