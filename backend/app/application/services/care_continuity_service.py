"""Phase 10 — Care-continuity analytics service.

Computes the screening -> flagged -> referred -> received -> appointment ->
care -> followup funnel from deterministic assessment sessions + referrals +
care outcomes. All outputs are de-identified and small-cell-suppressed (k=10).

INVARIANT: outcome data NEVER feeds back into CDSE scoring. This service is
read-only over the operational referral/outcome tables. It does not alter
clinical rules, scores, severity, or recommendation generation.
"""

from __future__ import annotations

import datetime
import logging
import statistics
from zoneinfo import ZoneInfo

from sqlalchemy import false, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.interoperability_dtos import (
    CareContinuityMetrics,
    CareContinuityResponse,
    CareFunnelStage,
)
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.core.config import settings
from app.identity import get_user_ids
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.care_outcome import CareOutcomeModel
from app.infrastructure.persistence.models.decision import (
    AssessmentResultModel,
    GeneratedRecommendationModel,
)
from app.infrastructure.persistence.models.referral import ReferralModel

logger = logging.getLogger(__name__)
_UTC = ZoneInfo("UTC")


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(_UTC)


def _date_range(start, end):
    if start and end:
        return start, end
    today = _utc_now().date()
    return start or (today - datetime.timedelta(days=90)), end or today


class CareContinuityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._k = settings.analytics_min_group_size

    def _suppress(self, count: int) -> tuple[int | None, bool]:
        if count < self._k:
            return None, True
        return count, False

    def _rate(self, num: int, denom: int) -> tuple[float | None, bool]:
        if denom < self._k:
            return None, True
        return round((num / denom) * 100, 1) if denom > 0 else 0.0, False

    async def get_care_continuity(
        self, filters: AnalyticsFilters
    ) -> CareContinuityResponse:
        start, end = _date_range(filters.start_date, filters.end_date)
        start_dt = datetime.datetime.combine(start, datetime.time.min, tzinfo=_UTC)
        end_dt = datetime.datetime.combine(end, datetime.time.max, tzinfo=_UTC)
        active_user_ids = await get_user_ids(self.session)

        # Screened: completed assessment sessions in period.
        screened_stmt = (
            select(func.count(func.distinct(AssessmentSessionModel.user_id)))
            .where(
                AssessmentSessionModel.deleted_at.is_(None),
                (
                    AssessmentSessionModel.user_id.in_(active_user_ids)
                    if active_user_ids
                    else false()
                ),
                AssessmentSessionModel.status == "completed",
                AssessmentSessionModel.completed_at.between(start_dt, end_dt),
            )
        )
        screened = (await self.session.execute(screened_stmt)).scalar() or 0

        # Flagged: distinct users with an assessment result that generated
        # at least one recommendation in period.
        flagged_stmt = (
            select(func.count(func.distinct(AssessmentResultModel.user_id)))
            .select_from(AssessmentResultModel)
            .join(
                GeneratedRecommendationModel,
                GeneratedRecommendationModel.result_id == AssessmentResultModel.id,
            )
            .where(
                AssessmentResultModel.deleted_at.is_(None),
                GeneratedRecommendationModel.deleted_at.is_(None),
                AssessmentResultModel.created_at.between(start_dt, end_dt),
            )
        )
        flagged = (await self.session.execute(flagged_stmt)).scalar() or 0

        # Referred: distinct patients with a referral created in period.
        referred_stmt = (
            select(func.count(func.distinct(ReferralModel.patient_user_id)))
            .where(
                ReferralModel.deleted_at.is_(None),
                ReferralModel.created_at.between(start_dt, end_dt),
            )
        )
        referred = (await self.session.execute(referred_stmt)).scalar() or 0

        # Outcome-based funnel stages (distinct patients per outcome category).
        outcome_categories = [
            "referral_received",
            "appointment_scheduled",
            "care_received",
            "followup_completed",
            "lost_to_followup",
        ]
        outcome_counts: dict[str, int] = {}
        for cat in outcome_categories:
            stmt = (
                select(func.count(func.distinct(CareOutcomeModel.patient_user_id)))
                .where(
                    CareOutcomeModel.deleted_at.is_(None),
                    CareOutcomeModel.outcome_category == cat,
                    CareOutcomeModel.recorded_at.between(start_dt, end_dt),
                )
            )
            outcome_counts[cat] = (await self.session.execute(stmt)).scalar() or 0

        referral_received = outcome_counts["referral_received"]
        appointment_scheduled = outcome_counts["appointment_scheduled"]
        care_received = outcome_counts["care_received"]
        followup_completed = outcome_counts["followup_completed"]
        lost_to_followup = outcome_counts["lost_to_followup"]

        # Build funnel with suppression per stage.
        stages_raw = [
            ("screened", screened),
            ("flagged", flagged),
            ("referred", referred),
            ("referral_received", referral_received),
            ("appointment_scheduled", appointment_scheduled),
            ("care_received", care_received),
            ("followup_completed", followup_completed),
        ]
        funnel: list[CareFunnelStage] = []
        for stage, count in stages_raw:
            val, supp = self._suppress(count)
            funnel.append(
                CareFunnelStage(
                    stage=stage,
                    count=val if val is not None else 0,
                    suppressed=supp,
                )
            )

        # Rates.
        comp_rate, comp_supp = self._rate(care_received, referred)
        foll_rate, foll_supp = self._rate(followup_completed, care_received)
        drop_rate, drop_supp = self._rate(lost_to_followup, referred)

        # Median time-to-care (days) from referral creation to first
        # care_received outcome, per patient. Privacy-safe: only computed if
        # cohort >= k.
        time_to_care = await self._median_time_to_care(start_dt, end_dt)

        # CHW-assisted completion: referrals with an assigned CHW that reached
        # care_received.
        chw_assisted_stmt = (
            select(
                func.count(func.distinct(CareOutcomeModel.patient_user_id))
            )
            .select_from(CareOutcomeModel)
            .join(ReferralModel, ReferralModel.id == CareOutcomeModel.referral_id)
            .where(
                CareOutcomeModel.deleted_at.is_(None),
                CareOutcomeModel.outcome_category == "care_received",
                ReferralModel.assigned_chw_user_id.isnot(None),
                CareOutcomeModel.recorded_at.between(start_dt, end_dt),
            )
        )
        chw_care = (await self.session.execute(chw_assisted_stmt)).scalar() or 0
        chw_total_stmt = (
            select(func.count(func.distinct(ReferralModel.patient_user_id)))
            .where(
                ReferralModel.deleted_at.is_(None),
                ReferralModel.assigned_chw_user_id.isnot(None),
                ReferralModel.created_at.between(start_dt, end_dt),
            )
        )
        chw_total = (await self.session.execute(chw_total_stmt)).scalar() or 0
        chw_rate, chw_supp = self._rate(chw_care, chw_total)

        metrics = CareContinuityMetrics(
            screened=screened,
            flagged=flagged,
            referred=referred,
            referral_received=referral_received,
            appointment_scheduled=appointment_scheduled,
            care_received=care_received,
            followup_completed=followup_completed,
            lost_to_followup=lost_to_followup,
            referral_completion_rate=comp_rate,
            followup_completion_rate=foll_rate,
            drop_off_rate=drop_rate,
            median_time_to_care_days=time_to_care,
            chw_assisted_completion_rate=chw_rate,
            suppressed_stages=[s for s in funnel if s.suppressed],
        )
        return CareContinuityResponse(
            period_start=start,
            period_end=end,
            funnel=funnel,
            metrics=metrics,
        )

    async def _median_time_to_care(
        self, start_dt, end_dt
    ) -> float | None:
        """Median days from referral creation to first care_received outcome."""
        # Pair each care_received outcome with its referral's created_at.
        stmt = (
            select(
                CareOutcomeModel.patient_user_id,
                ReferralModel.created_at.label("ref_created"),
                CareOutcomeModel.recorded_at.label("care_at"),
            )
            .select_from(CareOutcomeModel)
            .join(ReferralModel, ReferralModel.id == CareOutcomeModel.referral_id)
            .where(
                CareOutcomeModel.deleted_at.is_(None),
                CareOutcomeModel.outcome_category == "care_received",
                CareOutcomeModel.recorded_at.between(start_dt, end_dt),
            )
        )
        rows = (await self.session.execute(stmt)).all()
        # Dedup per patient: keep earliest care_at.
        per_patient: dict[str, tuple[datetime.datetime, datetime.datetime]] = {}
        for r in rows:
            ref_created = r.ref_created
            care_at = r.care_at
            if ref_created is None or care_at is None:
                continue
            if ref_created.tzinfo is None:
                ref_created = ref_created.replace(tzinfo=_UTC)
            if care_at.tzinfo is None:
                care_at = care_at.replace(tzinfo=_UTC)
            delta_days = (care_at - ref_created).total_seconds() / 86400.0
            if delta_days < 0:
                # Sub-second negative deltas are timestamp-precision
                # skew (server_default CURRENT_TIMESTAMP is
                # second-granular on SQLite, while recorded_at keeps
                # microseconds), not genuinely impossible timelines.
                # Treat as same-instant; discard only materially
                # negative deltas (outcome clearly predates referral).
                if delta_days > -1.0 / 86400.0:
                    delta_days = 0.0
                else:
                    continue
            prev = per_patient.get(r.patient_user_id)
            if prev is None or care_at < prev[1]:
                per_patient[r.patient_user_id] = (ref_created, care_at)
        cohort = len(per_patient)
        if cohort < self._k:
            return None
        deltas = [
            (care - ref).total_seconds() / 86400.0
            for ref, care in per_patient.values()
        ]
        return round(statistics.median(deltas), 1)
