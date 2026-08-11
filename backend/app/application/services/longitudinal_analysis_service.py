"""Phase 4 — Deterministic longitudinal analysis service.

This service is INDEPENDENT of any LLM. It loads a patient's completed
deterministic assessments, orders them chronologically, and computes the
deterministic differences between adjacent assessments:

- body-system score + category changes (trend via ordered-category transition
  + conservative numeric delta),
- newly-activated / persistent / resolved indicators,
- newly-appearing / persistent / removed possible conditions,
- new / persistent / removed recommendations.

It READS ONLY from existing immutable, timestamped, trace-ID-bearing
deterministic results/reports. It never writes, never diagnoses, never
calculates a new clinical score, and never invents an overall "health score".

A trajectory requires >= 2 completed assessments; with 1 it reports
insufficient data; with 0 it reports the empty state.
"""

from __future__ import annotations

import ast
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.longitudinal_dtos import (
    BodySystemPoint,
    ChangeEvent,
    ConditionChanges,
    HealthTrajectory,
    IndicatorChanges,
    LongitudinalAssessmentPoint,
    RecommendationChanges,
    SCORE_DELTA_THRESHOLD,
    SEVERITY_ORDER,
    TrendLabel,
    TrajectoryComparison,
)
from app.core.logging import get_logger
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.models.decision import AssessmentResultModel
from app.infrastructure.persistence.models.report import HealthAssessmentModel
from app.infrastructure.persistence.repositories.sql_decision_repository import (
    SQLDecisionRepository,
)
from app.infrastructure.persistence.repositories.sql_report_repository import (
    SQLReportRepository,
)

logger = get_logger(__name__)


def _severity_rank(category: str | None) -> int:
    """Lower rank = lower severity. Unknown categories rank below Normal."""
    if not category:
        return -1
    try:
        return SEVERITY_ORDER.index(category)
    except ValueError:
        return -1


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_trace_id(result: AssessmentResultModel | None) -> str | None:
    """Recover the CDSE trace_id from the persisted result summary."""
    if not result:
        return None
    summary = getattr(result, "summary", None)
    if not summary:
        return None
    try:
        parsed = ast.literal_eval(summary)
        if isinstance(parsed, dict) and parsed.get("trace_id"):
            return str(parsed["trace_id"])
    except Exception:
        pass
    return None


class LongitudinalAnalysisService:
    """Deterministic trajectory computation. No LLM, no writes."""

    DEFAULT_LIMIT = 20

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.report_repo = SQLReportRepository(session)
        self.dec_repo = SQLDecisionRepository(session)

    async def get_trajectory(
        self,
        user_id: str,
        *,
        limit: int = DEFAULT_LIMIT,
    ) -> HealthTrajectory:
        """Build the deterministic trajectory for the caller's assessments.

        Loads at most ``limit`` most-recent completed assessments (bounded, no
        full-history scan), orders them chronologically (oldest→newest), and
        computes adjacent comparisons.
        """
        limit = max(1, min(limit, 100))
        points = await self._load_points(user_id, limit=limit)
        if not points:
            return HealthTrajectory(
                assessments=[],
                comparisons=[],
                sufficient_data=False,
                summary="Complete an assessment to begin your health timeline.",
            )
        if len(points) == 1:
            return HealthTrajectory(
                assessments=points,
                comparisons=[],
                sufficient_data=False,
                summary=(
                    "Your first assessment is recorded. Complete another "
                    "assessment to compare changes over time."
                ),
            )
        comparisons = [
            self._compare(points[i - 1], points[i])
            for i in range(1, len(points))
        ]
        return HealthTrajectory(
            assessments=points,
            comparisons=comparisons,
            sufficient_data=True,
            summary=self._trajectory_summary(points, comparisons),
        )

    async def compare_specific(
        self,
        user_id: str,
        previous_session_id: str,
        current_session_id: str,
    ) -> TrajectoryComparison | None:
        """Compare two specific owned assessments (adjacent or not)."""
        prev = await self._load_point_by_session(user_id, previous_session_id)
        curr = await self._load_point_by_session(user_id, current_session_id)
        if prev is None or curr is None:
            return None
        return self._compare(prev, curr)

    # ------------------------------------------------------------------
    # Loading (batched, bounded, ownership-scoped)
    # ------------------------------------------------------------------

    async def _load_points(
        self, user_id: str, *, limit: int
    ) -> list[LongitudinalAssessmentPoint]:
        # Bounded: most recent N reports for this user.
        reports = await self.report_repo.list_reports_by_user(
            user_id, limit=limit, offset=0
        )
        if not reports:
            return []
        # Chronological oldest→newest for comparison ordering.
        reports = sorted(
            reports,
            key=lambda r: r.created_at or datetime.min,
        )
        # Batch-load body-system names.
        bs_ids = {
            bs.body_system_id
            for r in reports
            for bs in (r.body_systems or [])
            if bs.body_system_id
        }
        bs_map = await self._load_body_system_names(list(bs_ids))

        points: list[LongitudinalAssessmentPoint] = []
        for r in reports:
            result = await self.dec_repo.get_result_by_session(r.session_id)
            points.append(self._to_point(r, result, bs_map))
        return points

    async def _load_point_by_session(
        self, user_id: str, session_id: str
    ) -> LongitudinalAssessmentPoint | None:
        r = await self.report_repo.get_report_by_session(session_id)
        if not r or r.user_id != user_id:
            return None
        bs_ids = [bs.body_system_id for bs in (r.body_systems or []) if bs.body_system_id]
        bs_map = await self._load_body_system_names(bs_ids)
        result = await self.dec_repo.get_result_by_session(session_id)
        return self._to_point(r, result, bs_map)

    async def _load_body_system_names(
        self, ids: list[str]
    ) -> dict[str, str]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(BodySystemModel.id, BodySystemModel.name).where(
                BodySystemModel.id.in_(ids)
            )
        )
        return {row.id: row.name for row in rows.all()}

    def _to_point(
        self,
        report: HealthAssessmentModel,
        result: AssessmentResultModel | None,
        bs_map: dict[str, str],
    ) -> LongitudinalAssessmentPoint:
        body_systems = [
            BodySystemPoint(
                body_system_id=bs.body_system_id,
                name=bs_map.get(bs.body_system_id) if bs.body_system_id else None,
                score=_safe_float(bs.score),
                category=bs.category,
            )
            for bs in (report.body_systems or [])
        ]
        # Overall severity = highest-severity body-system category (READ-ONLY).
        overall = None
        if body_systems:
            ranked = sorted(
                body_systems,
                key=lambda b: _severity_rank(b.category),
                reverse=True,
            )
            overall = ranked[0].category

        ind_ids: list[str] = []
        cond_ids: list[str] = []
        rec_ids: list[str] = []
        if result is not None:
            ind_ids = [a.indicator_id for a in (result.activated_indicators or [])]
            cond_ids = [a.condition_id for a in (result.activated_conditions or [])]
            rec_ids = [
                a.recommendation_id
                for a in (result.generated_recommendations or [])
            ]
        return LongitudinalAssessmentPoint(
            assessment_id=report.id,
            session_id=report.session_id,
            trace_id=_extract_trace_id(result),
            template_id=None,
            completed_at=report.created_at,
            overall_severity=overall,
            body_systems=body_systems,
            activated_indicators=ind_ids,
            possible_conditions=cond_ids,
            recommendations=rec_ids,
        )

    # ------------------------------------------------------------------
    # Deterministic comparison
    # ------------------------------------------------------------------

    def _compare(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> TrajectoryComparison:
        body_changes = self._body_system_changes(previous, current)
        ind_changes = self._indicator_changes(previous, current)
        cond_changes = self._condition_changes(previous, current)
        rec_changes = self._recommendation_changes(previous, current)
        overall = self._overall_change(previous, current)
        events: list[ChangeEvent] = []
        if overall is not None:
            events.append(overall)
        events.extend(body_changes)
        return TrajectoryComparison(
            previous=previous,
            current=current,
            overall_change=overall,
            body_system_changes=body_changes,
            indicator_changes=ind_changes,
            condition_changes=cond_changes,
            recommendation_changes=rec_changes,
            change_events=events,
        )

    def _overall_change(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> ChangeEvent | None:
        prev_rank = _severity_rank(previous.overall_severity)
        curr_rank = _severity_rank(current.overall_severity)
        if prev_rank == curr_rank and previous.overall_severity == current.overall_severity:
            return ChangeEvent(
                scope="overall",
                ref_id=None,
                label="Overall severity",
                previous_value=previous.overall_severity,
                current_value=current.overall_severity,
                trend=TrendLabel.STABLE,
            )
        trend = (
            TrendLabel.IMPROVING
            if curr_rank < prev_rank
            else TrendLabel.WORSENING
        )
        return ChangeEvent(
            scope="overall",
            ref_id=None,
            label="Overall severity",
            previous_value=previous.overall_severity,
            current_value=current.overall_severity,
            trend=trend,
        )

    def _body_system_changes(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> list[ChangeEvent]:
        prev_by_id = {b.body_system_id: b for b in previous.body_systems}
        curr_by_id = {b.body_system_id: b for b in current.body_systems}
        all_ids = sorted(set(prev_by_id) | set(curr_by_id))
        changes: list[ChangeEvent] = []
        for bs_id in all_ids:
            p = prev_by_id.get(bs_id)
            c = curr_by_id.get(bs_id)
            label = (c.name if c else p.name if p else bs_id) or bs_id
            if p is None and c is not None:
                changes.append(ChangeEvent(
                    scope="body_system", ref_id=bs_id, label=label,
                    previous_value=None, current_value=c.category,
                    previous_score=None, current_score=c.score,
                    trend=TrendLabel.NEW,
                ))
                continue
            if p is not None and c is None:
                changes.append(ChangeEvent(
                    scope="body_system", ref_id=bs_id, label=label,
                    previous_value=p.category, current_value=None,
                    previous_score=p.score, current_score=None,
                    trend=TrendLabel.REMOVED,
                ))
                continue
            assert p is not None and c is not None
            prev_rank = _severity_rank(p.category)
            curr_rank = _severity_rank(c.category)
            delta = None
            if p.score is not None and c.score is not None:
                delta = c.score - p.score
            if prev_rank == curr_rank and (delta is None or abs(delta) < SCORE_DELTA_THRESHOLD):
                trend = TrendLabel.STABLE
            elif curr_rank < prev_rank:
                trend = TrendLabel.IMPROVING
            elif curr_rank > prev_rank:
                trend = TrendLabel.WORSENING
            else:
                # Same category rank but a meaningful numeric delta: classify
                # by direction without changing the severity label.
                trend = (
                    TrendLabel.IMPROVING
                    if delta is not None and delta < 0
                    else TrendLabel.WORSENING
                    if delta is not None and delta > 0
                    else TrendLabel.STABLE
                )
            changes.append(ChangeEvent(
                scope="body_system", ref_id=bs_id, label=label,
                previous_value=p.category, current_value=c.category,
                previous_score=p.score, current_score=c.score,
                delta=delta, trend=trend,
            ))
        return changes

    def _indicator_changes(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> IndicatorChanges:
        prev = set(previous.activated_indicators)
        curr = set(current.activated_indicators)
        return IndicatorChanges(
            new=sorted(curr - prev),
            resolved=sorted(prev - curr),
            persistent=sorted(prev & curr),
        )

    def _condition_changes(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> ConditionChanges:
        prev = set(previous.possible_conditions)
        curr = set(current.possible_conditions)
        return ConditionChanges(
            new=sorted(curr - prev),
            removed=sorted(prev - curr),
            persistent=sorted(prev & curr),
        )

    def _recommendation_changes(
        self,
        previous: LongitudinalAssessmentPoint,
        current: LongitudinalAssessmentPoint,
    ) -> RecommendationChanges:
        prev = set(previous.recommendations)
        curr = set(current.recommendations)
        return RecommendationChanges(
            new=sorted(curr - prev),
            removed=sorted(prev - curr),
            persistent=sorted(prev & curr),
        )

    def _trajectory_summary(
        self,
        points: list[LongitudinalAssessmentPoint],
        comparisons: list[TrajectoryComparison],
    ) -> str:
        if not comparisons:
            return "Not enough historical data for a trajectory."
        last = comparisons[-1]
        worsening = sum(
            1 for c in last.body_system_changes if c.trend == TrendLabel.WORSENING
        )
        improving = sum(
            1 for c in last.body_system_changes if c.trend == TrendLabel.IMPROVING
        )
        parts = [f"{len(points)} assessments compared over time."]
        if worsening:
            parts.append(f"{worsening} body system(s) showed higher-severity findings in the latest assessment.")
        if improving:
            parts.append(f"{improving} body system(s) showed lower-severity findings.")
        if not worsening and not improving:
            parts.append("Findings were largely stable across recent assessments.")
        parts.append("These are assessment findings, not confirmed diagnoses.")
        return " ".join(parts)
