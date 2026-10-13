"""Phase 6 — Population Health + SDG Analytics DTOs.

All responses are de-identified, aggregated, and small-cell suppressed.
No patient identifiers (user_id, email, session_id, trace_id) ever appear
in these DTOs. Only aggregate counts, rates, and distributions.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TimeBucket = Literal["day", "week", "month"]

#: Whether a value was suppressed for privacy (k-anonymity).
#: When suppressed, the actual count is replaced with None and the dimension
#: is reported as "Suppressed" so the dashboard can display the suppression
#: rather than a misleading zero or small number.


class AnalyticsFilters(BaseModel):
    """Validated filter parameters for analytics queries.

    All filters are optional. Every filtered result passes small-cell
    suppression at the cohort level (see PopulationAnalyticsService).
    """

    start_date: date | None = Field(
        default=None, description="Inclusive start date (UTC)."
    )
    end_date: date | None = Field(
        default=None, description="Inclusive end date (UTC)."
    )
    body_system_id: str | None = Field(
        default=None, description="Filter to a single body system (canonical ID)."
    )
    language: str | None = Field(
        default=None,
        description="Filter by intake language (en/si/ta). Requires session metadata.",
    )
    input_type: str | None = Field(
        default=None,
        description="Filter by input type (text/voice). Requires session metadata.",
    )


class SuppressedValue(BaseModel):
    """A value that may be suppressed if the cohort is too small."""

    value: float | None
    suppressed: bool = False

    @classmethod
    def from_count(cls, count: int, min_group_size: int) -> SuppressedValue:
        if count < min_group_size:
            return cls(value=None, suppressed=True)
        return cls(value=float(count), suppressed=False)


class TimeSeriesPoint(BaseModel):
    """One bucket in a time series."""

    bucket: str = Field(description="Date label, e.g. '2026-01' or '2026-01-15'.")
    count: int
    suppressed: bool = False


class OverviewMetrics(BaseModel):
    """Top-level population-health overview.

    All counts are de-identified. ``unique_participants`` counts distinct
    users; ``assessment_sessions`` counts sessions (a user may have many).
    """

    period_start: date
    period_end: date
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    unique_participants: int
    completion_rate: float | None
    completion_rate_suppressed: bool = False


class SeverityBucket(BaseModel):
    """One severity category distribution entry.

    These are distributions of MediCheck assessment findings (body-system
    categories from the deterministic CDSE), NOT population prevalence
    estimates.
    """

    category: str
    count: int
    percentage: float | None
    suppressed: bool = False


class BodySystemMetric(BaseModel):
    """Aggregated metric for one body system."""

    body_system_id: str
    name: str
    code: str
    assessment_count: int
    suppressed: bool = False


class IndicatorTrendEntry(BaseModel):
    """One indicator's activation count over the period.

    Indicator activation is NOT confirmed diagnosis. This metric counts
    how many assessments activated an indicator, not disease prevalence.
    """

    indicator_id: str
    name: str
    body_system_id: str
    activation_count: int
    suppressed: bool = False


class TrajectoryBucket(BaseModel):
    """One trajectory classification distribution entry.

    Trajectory classifications reuse Phase 4's TrendLabel values
    (improving/stable/worsening/new/resolved). A worsening MediCheck
    trajectory is an assessment trend, not proof of disease progression.
    """

    trend: str
    count: int
    percentage: float | None
    suppressed: bool = False


class LanguageMetric(BaseModel):
    """Accessibility metric broken down by intake language (Phase 5)."""

    language: str
    assessment_count: int
    completion_rate: float | None
    suppressed: bool = False


class AccessibilityMetrics(BaseModel):
    """Multilingual + voice accessibility metrics (Phase 5 integration)."""

    by_language: list[LanguageMetric]
    voice_intake_count: int
    text_intake_count: int
    voice_completion_rate: float | None
    voice_suppressed: bool = False


class AnalyticsOverviewResponse(BaseModel):
    """Response for GET /analytics/overview."""

    overview: OverviewMetrics
    trend: list[TimeSeriesPoint]
    generated_at: date


class SeverityDistributionResponse(BaseModel):
    """Response for GET /analytics/severity.

    Distribution of MediCheck body-system assessment categories. NOT
    population disease prevalence.
    """

    period_start: date
    period_end: date
    distribution: list[SeverityBucket]
    total_assessments: int
    disclaimer: str = (
        "Distribution of MediCheck assessment findings, not population prevalence."
    )


class BodySystemsResponse(BaseModel):
    """Response for GET /analytics/body-systems."""

    period_start: date
    period_end: date
    body_systems: list[BodySystemMetric]


class IndicatorsResponse(BaseModel):
    """Response for GET /analytics/indicators.

    Counts of assessments activating each clinical indicator. Indicator
    activation is NOT confirmed diagnosis.
    """

    period_start: date
    period_end: date
    indicators: list[IndicatorTrendEntry]
    disclaimer: str = (
        "Number of assessments activating each indicator. Indicator activation "
        "is not confirmed diagnosis."
    )


class TrajectoryResponse(BaseModel):
    """Response for GET /analytics/trajectory.

    Distribution of Phase 4 trend classifications across patients with
    multiple completed assessments.
    """

    period_start: date
    period_end: date
    distribution: list[TrajectoryBucket]
    patients_with_trajectory: int
    disclaimer: str = (
        "Distribution of reported trajectories. A worsening trajectory is an "
        "assessment trend, not proof of disease progression."
    )


class AccessibilityResponse(BaseModel):
    """Response for GET /analytics/accessibility (Phase 5 integration)."""

    period_start: date
    period_end: date
    accessibility: AccessibilityMetrics
    disclaimer: str = (
        "Language selection is an interaction metric. Do not infer demographics "
        "from language."
    )


class SDGMetric(BaseModel):
    """One SDG-aligned digital health indicator."""

    label: str
    value: float | None
    suppressed: bool = False
    definition: str


class SDGSection(BaseModel):
    """One SDG goal section on the dashboard."""

    goal: str
    title: str
    metrics: list[SDGMetric]
    note: str = "MediCheck-derived digital health indicators aligned with SDG targets."


class SDGDashboardResponse(BaseModel):
    """Response for GET /analytics/sdg."""

    period_start: date
    period_end: date
    sections: list[SDGSection]
    disclaimer: str = (
        "These are platform-derived monitoring indicators. They do not prove "
        "an SDG target has been achieved."
    )
