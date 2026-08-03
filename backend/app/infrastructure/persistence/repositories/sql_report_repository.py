from __future__ import annotations

from sqlalchemy import insert, select
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
        stmt = insert(HealthAssessmentModel).values(**data)
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(HealthAssessmentModel).where(
            HealthAssessmentModel.session_id == data.get("session_id")
        )
        r = await self.session.execute(q)
        return r.scalars().first()

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
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(BodySystemAssessmentModel).where(
            BodySystemAssessmentModel.assessment_id == assessment_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

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
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(ConditionAssessmentModel).where(
            ConditionAssessmentModel.assessment_id == assessment_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def add_lifestyle_assessment(
        self, assessment_id: str, data: str
    ) -> LifestyleAssessmentModel:
        stmt = insert(LifestyleAssessmentModel).values(
            assessment_id=assessment_id, data=data
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(LifestyleAssessmentModel).where(
            LifestyleAssessmentModel.assessment_id == assessment_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

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
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = select(GeneratedAdviceModel).where(
            GeneratedAdviceModel.assessment_id == assessment_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def get_report_by_session(
        self, session_id: str
    ) -> HealthAssessmentModel | None:
        q = select(HealthAssessmentModel).where(
            HealthAssessmentModel.session_id == session_id
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def get_report(self, report_id: str) -> HealthAssessmentModel | None:
        q = select(HealthAssessmentModel).where(HealthAssessmentModel.id == report_id)
        r = await self.session.execute(q)
        return r.scalars().first()

    async def list_reports_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> list[HealthAssessmentModel]:
        q = select(HealthAssessmentModel).where(HealthAssessmentModel.user_id == user_id).order_by(HealthAssessmentModel.created_at.desc()).limit(limit).offset(offset)
        r = await self.session.execute(q)
        return r.scalars().all()
