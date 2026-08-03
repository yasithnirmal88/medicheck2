from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.recommendation import (
    RecommendationModel,
)
from app.infrastructure.persistence.models.report import (
    HealthAssessmentModel,
)
from app.infrastructure.persistence.models.severity_threshold import (
    SeverityThresholdModel,
)
from app.infrastructure.persistence.repositories.sql_decision_repository import (
    SQLDecisionRepository,
)
from app.infrastructure.persistence.repositories.sql_knowledge_graph_repository import (
    SQLKnowledgeGraphRepository,
)
from app.infrastructure.persistence.repositories.sql_profile_repository import (
    SQLProfileRepository,
)
from app.infrastructure.persistence.repositories.sql_report_repository import (
    SQLReportRepository,
)


class ReportService:
    def __init__(self, session: AsyncSession, cache: CacheService | None = None):
        self.session = session
        self.cache = cache
        self.report_repo = SQLReportRepository(session)
        self.dec_repo = SQLDecisionRepository(session)
        self.kg_repo = SQLKnowledgeGraphRepository(session)
        self.profile_repo = SQLProfileRepository(session)

    async def generate_report(
        self, session_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        # load decision result
        result = await self.dec_repo.get_result_by_session(session_id)
        if not result:
            raise ValueError("No decision result for session; run CDSE first")

        # Batch-load indicators for all activated indicators
        indicator_ids = [act.indicator_id for act in result.activated_indicators]
        indicator_map: dict[str, ClinicalIndicatorModel] = {}
        if indicator_ids:
            rows = await self.session.execute(
                select(ClinicalIndicatorModel).where(ClinicalIndicatorModel.id.in_(indicator_ids))
            )
            indicator_map = {i.id: i for i in rows.scalars().all()}

        # aggregate body system scores by scanning activated indicators
        body_scores: dict[str, float] = {}
        body_indicator_map: dict[str, list] = {}
        for act in result.activated_indicators:
            ind = indicator_map.get(act.indicator_id)
            bs = ind.body_system_id if ind else None
            score = act.score or 0.0
            if bs:
                body_scores[bs] = body_scores.get(bs, 0.0) + score
                body_indicator_map.setdefault(bs, []).append(act.indicator_id)

        # Load DB-configured thresholds; fall back to defaults if table is empty
        thresholds: list[SeverityThresholdModel] = []
        try:
            rows = await self.session.execute(
                select(SeverityThresholdModel).where(
                    SeverityThresholdModel.is_active == True  # noqa: E712
                ).order_by(SeverityThresholdModel.min_score)
            )
            thresholds = rows.scalars().all()
        except Exception:
            thresholds = []

        if thresholds:
            categories = [(t.min_score, t.label or t.name) for t in thresholds]
        else:
            categories = [
                (0.0, "Normal"),
                (1.0, "Monitor"),
                (3.0, "Needs Attention"),
                (5.0, "Recommend Screening"),
                (9999999.0, "Urgent Medical Review"),
            ]

        # create health assessment record
        assessment = await self.report_repo.create_health_assessment(
            {
                "session_id": session_id,
                "user_id": result.user_id,
                "summary": None,
                "created_at": None,
            }
        )

        # add body system assessments
        for bs_id, sc in body_scores.items():
            # determine category by thresholds
            cat = "Normal"
            for thresh, name in categories:
                if sc <= thresh:
                    cat = name
                    break
            await self.report_repo.add_body_system_assessment(
                assessment.id,
                bs_id,
                cat,
                sc,
                f"Indicators: {body_indicator_map.get(bs_id, [])}",
            )

        # add condition assessments from activated_conditions
        for cond in result.activated_conditions:
            # condition confidence provided in result
            conf = cond.confidence
            # map numeric confidence to labels (placeholder)
            conf_label = None
            try:
                cfloat = float(conf) if conf is not None else 0.0
                if cfloat < 0.25:
                    conf_label = "Very Weak"
                elif cfloat < 0.5:
                    conf_label = "Weak"
                elif cfloat < 0.75:
                    conf_label = "Moderate"
                else:
                    conf_label = "Strong"
            except Exception:
                conf_label = "Unknown"
            await self.report_repo.add_condition_assessment(
                assessment.id, cond.condition_id, cond.score, conf_label, None
            )

        # include lifestyle snapshot from profile
        try:
            profile = await self.profile_repo.get_by_user(result.user_id)
            lifestyle_json = None
            if getattr(profile, "lifestyle", None) is not None:
                # stringify for storage
                lifestyle_json = json.dumps({"lifestyle": str(profile.lifestyle)})
            else:
                lifestyle_json = json.dumps({})
            await self.report_repo.add_lifestyle_assessment(
                assessment.id, lifestyle_json
            )
        except Exception:
            # ignore if profile not present
            await self.report_repo.add_lifestyle_assessment(
                assessment.id, json.dumps({})
            )

        # Batch-load recommendations for generated_recommendations
        rec_ids = [r.recommendation_id for r in result.generated_recommendations]
        rec_map: dict[str, RecommendationModel] = {}
        if rec_ids:
            rows = await self.session.execute(
                select(RecommendationModel).where(RecommendationModel.id.in_(rec_ids))
            )
            rec_map = {rec.id: rec for rec in rows.scalars().all()}

        # generated advices: map generated recommendations
        for r in result.generated_recommendations:
            rec = rec_map.get(r.recommendation_id)
            text = rec.text if rec else None
            await self.report_repo.add_generated_advice(
                assessment.id,
                r.recommendation_id,
                getattr(rec, "category", None) if rec else None,
                text,
            )

        # labs and screenings already persisted in decision repository; also include as advices if needed
        # final summary
        summary = {
            "body_systems_count": len(body_scores),
            "activated_conditions_count": len(result.activated_conditions),
            "generated_recommendations_count": len(result.generated_recommendations),
        }
        # update assessment summary
        await self.session.execute(
            HealthAssessmentModel.__table__.update()
            .where(HealthAssessmentModel.id == assessment.id)
            .values(summary=str(summary))
        )
        await self.session.commit()

        return {"report_id": assessment.id, "summary": summary}

    async def get_report_by_session(self, session_id: str):
        if self.cache:
            return await self.cache.remember(
                f"report:session:{session_id}", 300,
                lambda: self.report_repo.get_report_by_session(session_id),
            )
        return await self.report_repo.get_report_by_session(session_id)

    async def get_report(self, report_id: str):
        if self.cache:
            return await self.cache.remember(
                f"report:id:{report_id}", 300,
                lambda: self.report_repo.get_report(report_id),
            )
        return await self.report_repo.get_report(report_id)

    async def list_reports(self, user_id: str, limit: int = 100, offset: int = 0):
        return await self.report_repo.list_reports_by_user(user_id, limit=limit, offset=offset)

    async def compare_reports(self, id1: str, id2: str) -> dict[str, Any]:
        r1 = await self.get_report(id1)
        r2 = await self.get_report(id2)
        if not r1 or not r2:
            raise ValueError('One or both reports not found')

        # simple diff: compare body_systems, conditions, advices by ids
        def extract_ids(items, key='id'):
            return {i.id for i in items} if items else set()

        bs1 = extract_ids(r1.body_systems)
        bs2 = extract_ids(r2.body_systems)
        added_bs = bs2 - bs1
        removed_bs = bs1 - bs2

        cond1 = extract_ids(r1.conditions)
        cond2 = extract_ids(r2.conditions)
        added_cond = cond2 - cond1
        removed_cond = cond1 - cond2

        adv1 = extract_ids(r1.advices)
        adv2 = extract_ids(r2.advices)
        added_adv = adv2 - adv1
        removed_adv = adv1 - adv2

        return {
            'report_1': r1,
            'report_2': r2,
            'added_body_systems': list(added_bs),
            'removed_body_systems': list(removed_bs),
            'added_conditions': list(added_cond),
            'removed_conditions': list(removed_cond),
            'added_advices': list(added_adv),
            'removed_advices': list(removed_adv),
        }
