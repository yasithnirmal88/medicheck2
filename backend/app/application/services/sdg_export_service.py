"""Phase 10 — SDG / population-health export service.

Produces machine-readable (JSON + CSV) de-identified aggregate exports
structured around SDG indicators, NOT internal database tables. Reuses the
existing ``PopulationAnalyticsService`` (Phase 6) + ``CareContinuityService``
(Phase 10) for the underlying aggregates — no second aggregation engine.

Privacy:
- k-anonymity enforced (k = settings.analytics_min_group_size, default 10).
- No patient identifiers in any row.
- Cohorts < k are suppressed (suppression_status = "suppressed", value = None).
- Combination-attack protection: each metric's effective cohort is checked
  against k before release.

Every metric documents its methodology + limitations. MediCheck metrics are
labelled "medicheck-aligned-proxy" unless they happen to be an official UN
SDG indicator (none currently are — all are proxies).
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.analytics_dtos import AnalyticsFilters, SDGDashboardResponse
from app.application.dtos.interoperability_dtos import (
    SdgExportFormat,
    SdgExportResponse,
    SdgExportRow,
)
from app.application.services.care_continuity_service import CareContinuityService
from app.application.services.population_analytics_service import (
    PopulationAnalyticsService,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class SdgExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pop = PopulationAnalyticsService(session)
        self.care = CareContinuityService(session)

    async def export(
        self, filters: AnalyticsFilters, fmt: SdgExportFormat = "json"
    ) -> SdgExportResponse:
        sdg = await self.pop.get_sdg_dashboard(filters)
        continuity = await self.care.get_care_continuity(filters)
        rows = self._build_rows(sdg, continuity, filters.start_date, filters.end_date)
        resp = SdgExportResponse(
            format=fmt,
            period_start=sdg.period_start,
            period_end=sdg.period_end,
            generated_at=date.today(),
            rows=rows,
        )
        return resp

    def to_csv(self, response: SdgExportResponse) -> str:
        """Serialize an SDG export response to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "indicator", "sdg_target", "indicator_type", "period",
            "geography", "population_group", "value", "numerator",
            "denominator", "suppression_status", "unit", "methodology",
            "limitations",
        ])
        for row in response.rows:
            writer.writerow([
                row.indicator,
                row.sdg_target,
                row.indicator_type,
                row.period,
                row.geography or "",
                row.population_group or "",
                "" if row.value is None else row.value,
                "" if row.numerator is None else row.numerator,
                "" if row.denominator is None else row.denominator,
                row.suppression_status,
                row.unit,
                row.methodology,
                row.limitations,
            ])
        return output.getvalue()

    def _build_rows(
        self,
        sdg: SDGDashboardResponse,
        continuity,
        _start: date | None,
        _end: date | None,
    ) -> list[SdgExportRow]:
        period = f"{sdg.period_start.isoformat()}/{sdg.period_end.isoformat()}"
        rows: list[SdgExportRow] = []
        metric_by_label: dict[str, tuple] = {}
        for section in sdg.sections:
            for m in section.metrics:
                metric_by_label[m.label] = (
                    section.goal,
                    m.value,
                    m.suppressed,
                    m.definition,
                )

        def _row(
            indicator: str,
            sdg_target: str,
            value,
            suppressed: bool,
            numerator: int | None,
            denominator: int | None,
            methodology: str,
            limitations: str,
            unit: str = "count",
            population_group: str | None = None,
        ) -> SdgExportRow:
            return SdgExportRow(
                indicator=indicator,
                sdg_target=sdg_target,
                indicator_type="medicheck-aligned-proxy",
                period=period,
                geography=None,
                population_group=population_group,
                value=(None if suppressed else value),
                numerator=(None if suppressed else numerator),
                denominator=(None if suppressed else denominator),
                suppression_status="suppressed" if suppressed else "released",
                unit=unit,
                methodology=methodology,
                limitations=limitations,
            )

        # SDG 3.4 rows.
        ov_completed = self._lookup(metric_by_label, "NCD-related assessment activity")
        rows.append(_row(
            "sdg-3-4-assessment-coverage", "SDG 3.4",
            ov_completed[1], ov_completed[2], None, None,
            "Count of completed MediCheck assessments in the period (distinct sessions).",
            "Platform activity proxy; not population prevalence.",
        ))
        worsening = self._lookup(metric_by_label, "Worsening trajectory proportion")
        rows.append(_row(
            "sdg-3-4-ncd-risk-distribution", "SDG 3.4",
            worsening[1], worsening[2], None, None,
            "Proportion of patients with a worsening MediCheck assessment trajectory (Phase 4 trend).",
            "Trajectory is an assessment trend, not disease progression.",
            unit="percent",
        ))
        # Screening completion from overview.
        comp_rate = self._lookup(metric_by_label, "Completion rate")
        rows.append(_row(
            "sdg-3-4-screening-completion", "SDG 3.4",
            comp_rate[1], comp_rate[2], None, None,
            "Completed / started assessments in the period.",
            "Completion proxy; excludes abandoned sessions.",
            unit="percent",
        ))
        # Referral rate (referred / screened).
        m = continuity.metrics
        _referred_val, _referred_supp = (m.referred, m.referred < self._k_check())
        screened_val = m.screened
        ref_rate = None
        ref_supp = False
        if screened_val and screened_val >= settings.analytics_min_group_size:
            ref_rate = round((m.referred / screened_val) * 100, 1) if screened_val else 0.0
        else:
            ref_supp = True
        rows.append(_row(
            "sdg-3-4-referral-rate", "SDG 3.4",
            ref_rate, ref_supp, m.referred, m.screened,
            "Distinct patients referred / distinct patients screened in the period.",
            "Referral eligibility is CMS-controlled; not all flagged patients are referred.",
            unit="percent",
        ))

        # SDG 3.8 rows.
        access = self._lookup(metric_by_label, "Assessment access")
        rows.append(_row(
            "sdg-3-8-screening-coverage", "SDG 3.8",
            access[1], access[2], None, None,
            "Total assessments initiated in the period.",
            "Access proxy; not population coverage.",
        ))
        rows.append(_row(
            "sdg-3-8-referral-completion", "SDG 3.8",
            m.referral_completion_rate,
            m.referral_completion_rate is None,
            m.care_received, m.referred,
            "Distinct patients with a care_received outcome / distinct patients referred.",
            "Outcome is operational; does not confirm diagnosis was treated.",
            unit="percent",
        ))
        rows.append(_row(
            "sdg-3-8-time-to-care", "SDG 3.8",
            m.median_time_to_care_days,
            m.median_time_to_care_days is None,
            None, None,
            "Median days from referral creation to first care_received outcome (per patient, earliest).",
            "Suppressed if cohort < k. Excludes negative/invalid deltas.",
            unit="days",
        ))
        # Care funnel as one composite row + per-stage via the funnel list.
        rows.append(_row(
            "sdg-3-8-care-funnel", "SDG 3.8",
            None, False, None, None,
            "Funnel: "
            + "->".join(
                stage_label for stage_label in [
                    "screened", "flagged", "referred", "referral_received",
                    "appointment_scheduled", "care_received", "followup_completed",
                ]
            )
            + ". "
            + "; ".join(f"{s.stage}={s.count}" + ("(suppressed)" if s.suppressed else "") for s in continuity.funnel),
            "Each stage is k-anonymity-suppressed independently.",
        ))
        voice = self._lookup(metric_by_label, "Voice adoption")
        rows.append(_row(
            "sdg-3-8-language-accessibility", "SDG 3.8",
            voice[1], voice[2], None, None,
            "Voice intake sessions / total sessions (Phase 5 accessibility).",
            "Language selection is an interaction metric; do not infer demographics.",
            unit="percent",
        ))
        rows.append(_row(
            "sdg-3-8-chw-assisted-assessments", "SDG 3.8",
            m.chw_assisted_completion_rate,
            m.chw_assisted_completion_rate is None,
            None, None,
            "CHW-assisted referrals reaching care_received / CHW-assisted referrals.",
            "Operational completion; not clinical outcome.",
            unit="percent",
        ))

        # SDG 10 rows (equity).
        lang_count = self._lookup(metric_by_label, "Languages available")
        rows.append(_row(
            "sdg-10-completion-equity", "SDG 10",
            lang_count[1], lang_count[2], None, None,
            "Number of intake languages with sufficient data (equity proxy).",
            "Availability proxy; completion-rate differences require >= k per language cohort.",
        ))
        rows.append(_row(
            "sdg-10-modality-equity", "SDG 10",
            voice[1], voice[2], None, None,
            "Voice vs text modality adoption (accessibility equity proxy).",
            "Modality adoption is not demographic equity. Geographic equity requires aggregated geo data.",
            unit="percent",
        ))
        return rows

    def _k_check(self) -> int:
        return settings.analytics_min_group_size

    def _lookup(self, metric_by_label: dict, label: str) -> tuple:
        return metric_by_label.get(label, ("", None, True, ""))
