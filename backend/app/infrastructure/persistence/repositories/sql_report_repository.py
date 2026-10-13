from __future__ import annotations

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.report import (
    BodySystemAssessmentModel,
    ConditionAssessmentModel,
    GeneratedAdviceModel,
    HealthAssessmentModel,
    LifestyleAssessmentModel,
)


class SQLReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_health_assessment(self, data: dict) -> HealthAssessmentModel:
        q = (
            select(HealthAssessmentModel)
            .where(HealthAssessmentModel.session_id == data["session_id"])
            .order_by(
                HealthAssessmentModel.created_at.desc().nulls_last(),
                HealthAssessmentModel.id.desc(),
            )
            .limit(1)
        )
        existing = (await self.session.execute(q)).scalar_one_or_none()
        if existing is not None:
            return existing
        stmt = insert(HealthAssessmentModel).values(**data).returning(
            HealthAssessmentModel
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def clear_report_details(self, assessment_id: str) -> None:
        for model in (
            BodySystemAssessmentModel,
            ConditionAssessmentModel,
            LifestyleAssessmentModel,
            GeneratedAdviceModel,
        ):
            await self.session.execute(
                delete(model).where(model.assessment_id == assessment_id)
            )

    async def add_body_system_assessment(
        self,
        assessment_id: str,
        body_system_id: str | None,
        category: str | None,
        score: float | None,
        notes: str | None,
    ) -> BodySystemAssessmentModel:
        stmt = insert(BodySystemAssessmentModel).values(
            assessment_id=assessment_id,
            body_system_id=body_system_id,
            category=category,
            score=str(score) if score is not None else None,
            notes=notes,
        ).returning(BodySystemAssessmentModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_condition_assessment(
        self,
        assessment_id: str,
        condition_id: str,
        score: float | None,
        confidence: str | None,
        notes: str | None,
    ) -> ConditionAssessmentModel:
        stmt = insert(ConditionAssessmentModel).values(
            assessment_id=assessment_id,
            condition_id=condition_id,
            score=str(score) if score is not None else None,
            confidence=confidence,
            notes=notes,
        ).returning(ConditionAssessmentModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_lifestyle_assessment(
        self, assessment_id: str, data: str
    ) -> LifestyleAssessmentModel:
        stmt = insert(LifestyleAssessmentModel).values(
            assessment_id=assessment_id, data=data
        ).returning(LifestyleAssessmentModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_generated_advice(
        self,
        assessment_id: str,
        recommendation_id: str | None,
        category: str | None,
        text: str | None,
    ) -> GeneratedAdviceModel:
        stmt = insert(GeneratedAdviceModel).values(
            assessment_id=assessment_id,
            recommendation_id=recommendation_id,
            category=category,
            text=text,
        ).returning(GeneratedAdviceModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_report_by_session(
        self, session_id: str
    ) -> HealthAssessmentModel | None:
        q = (
            select(HealthAssessmentModel)
            .where(HealthAssessmentModel.session_id == session_id)
            .order_by(
                HealthAssessmentModel.created_at.desc().nulls_last(),
                HealthAssessmentModel.id.desc(),
            )
            .limit(1)
        )
        r = await self.session.execute(q)
        return r.scalar_one_or_none()

    async def get_report(self, report_id: str) -> HealthAssessmentModel | None:
        q = select(HealthAssessmentModel).where(HealthAssessmentModel.id == report_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_reports_by_user(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> list[HealthAssessmentModel]:
        q = (
            select(HealthAssessmentModel)
            .where(HealthAssessmentModel.user_id == user_id)
            .order_by(HealthAssessmentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        r = await self.session.execute(q)
        return r.scalars().all()
