"""Phase 10 — SDG export + care-continuity DTOs.

All responses are de-identified, aggregated, and small-cell-suppressed (k=10).
No patient identifiers (user_id, email, session_id, trace_id) appear in any
response. Only aggregate counts, rates, and funnel metrics.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

SdgExportFormat = Literal["json", "csv"]

#: SDG indicator row (machine-readable export).
SdgIndicatorId = Literal[
    "sdg-3-4-assessment-coverage",
    "sdg-3-4-ncd-risk-distribution",
    "sdg-3-4-screening-completion",
    "sdg-3-4-referral-rate",
    "sdg-3-8-screening-coverage",
    "sdg-3-8-referral-completion",
    "sdg-3-8-time-to-care",
    "sdg-3-8-care-funnel",
    "sdg-3-8-language-accessibility",
    "sdg-3-8-chw-assisted-assessments",
    "sdg-10-completion-equity",
    "sdg-10-modality-equity",
]


class SdgExportRow(BaseModel):
    """One row of the SDG export. Structured around SDG indicators, not DB tables."""
    indicator: str
    sdg_target: str
    indicator_type: Literal["official", "medicheck-aligned-proxy"]
    period: str
    geography: str | None = None
    population_group: str | None = None
    value: float | None
    numerator: int | None = None
    denominator: int | None = None
    suppression_status: Literal["released", "suppressed"] = "released"
    unit: str = "count"
    methodology: str
    limitations: str


class SdgExportResponse(BaseModel):
    format: SdgExportFormat = "json"
    period_start: date
    period_end: date
    generated_at: date
    rows: list[SdgExportRow]
    disclaimer: str = (
        "These are platform-derived monitoring indicators aligned with SDG "
        "targets. They do not prove an SDG target has been achieved and are "
        "not official UN SDG indicators unless explicitly marked 'official'."
    )


# ── Care continuity funnel ─────────────────────────────────────────────


class CareFunnelStage(BaseModel):
    stage: str
    count: int
    suppressed: bool = False


class CareContinuityMetrics(BaseModel):
    screened: int
    flagged: int
    referred: int
    referral_received: int
    appointment_scheduled: int
    care_received: int
    followup_completed: int
    lost_to_followup: int
    referral_completion_rate: float | None
    followup_completion_rate: float | None
    drop_off_rate: float | None
    median_time_to_care_days: float | None
    chw_assisted_completion_rate: float | None
    # Suppression flags (k-anonymity).
    suppressed_stages: list[CareFunnelStage] = []


class CareContinuityResponse(BaseModel):
    period_start: date
    period_end: date
    funnel: list[CareFunnelStage]
    metrics: CareContinuityMetrics
    disclaimer: str = (
        "Care-continuity metrics are de-identified and small-cell-suppressed. "
        "Outcome data does not modify clinical scoring."
    )
