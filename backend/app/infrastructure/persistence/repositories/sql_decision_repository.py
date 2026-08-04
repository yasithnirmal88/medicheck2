from __future__ import annotations

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.decision import (
    ActivatedConditionModel,
    ActivatedIndicatorModel,
    AssessmentResultModel,
    ExplanationRecordModel,
    GeneratedLaboratoryTestModel,
    GeneratedRecommendationModel,
    GeneratedScreeningModel,
)


class SQLDecisionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_result(self, data: dict) -> AssessmentResultModel:
        stmt = insert(AssessmentResultModel).values(**data)
        await self.session.execute(stmt)
        q = select(AssessmentResultModel).where(
            AssessmentResultModel.session_id == data.get("session_id")
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def add_activated_indicator(
        self,
        result_id: str,
        indicator_id: str,
        score: float | None,
        evidence_count: int | None,
        notes: str | None,
    ) -> ActivatedIndicatorModel:
        stmt = insert(ActivatedIndicatorModel).values(
            result_id=result_id,
            indicator_id=indicator_id,
            score=score,
            evidence_count=evidence_count,
            notes=notes,
        )
        await self.session.execute(stmt)
        q = select(ActivatedIndicatorModel).where(
            ActivatedIndicatorModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        # return last added
        return rows[-1]

    async def add_activated_condition(
        self,
        result_id: str,
        condition_id: str,
        score: float | None,
        confidence: float | None,
        notes: str | None,
    ) -> ActivatedConditionModel:
        stmt = insert(ActivatedConditionModel).values(
            result_id=result_id,
            condition_id=condition_id,
            score=score,
            confidence=confidence,
            notes=notes,
        )
        await self.session.execute(stmt)
        q = select(ActivatedConditionModel).where(
            ActivatedConditionModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def add_recommendation(
        self,
        result_id: str,
        recommendation_id: str,
        source: str | None,
        notes: str | None,
    ) -> GeneratedRecommendationModel:
        stmt = insert(GeneratedRecommendationModel).values(
            result_id=result_id,
            recommendation_id=recommendation_id,
            source=source,
            notes=notes,
        )
        await self.session.execute(stmt)
        q = select(GeneratedRecommendationModel).where(
            GeneratedRecommendationModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def add_laboratory_test(
        self, result_id: str, laboratory_test_id: str, reason: str | None
    ) -> GeneratedLaboratoryTestModel:
        stmt = insert(GeneratedLaboratoryTestModel).values(
            result_id=result_id, laboratory_test_id=laboratory_test_id, reason=reason
        )
        await self.session.execute(stmt)
        q = select(GeneratedLaboratoryTestModel).where(
            GeneratedLaboratoryTestModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def add_screening(
        self, result_id: str, name: str, reason: str | None
    ) -> GeneratedScreeningModel:
        stmt = insert(GeneratedScreeningModel).values(
            result_id=result_id, name=name, reason=reason
        )
        await self.session.execute(stmt)
        q = select(GeneratedScreeningModel).where(
            GeneratedScreeningModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def add_explanation(
        self, result_id: str, source_type: str, source_id: str | None, text: str | None
    ) -> ExplanationRecordModel:
        stmt = insert(ExplanationRecordModel).values(
            result_id=result_id, source_type=source_type, source_id=source_id, text=text
        )
        await self.session.execute(stmt)
        q = select(ExplanationRecordModel).where(
            ExplanationRecordModel.result_id == result_id
        )
        r = await self.session.execute(q)
        rows = r.scalars().all()
        return rows[-1]

    async def get_result_by_session(
        self, session_id: str
    ) -> AssessmentResultModel | None:
        q = select(AssessmentResultModel).where(
            AssessmentResultModel.session_id == session_id
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def get_result(self, result_id: str) -> AssessmentResultModel | None:
        q = select(AssessmentResultModel).where(AssessmentResultModel.id == result_id)
        r = await self.session.execute(q)
        return r.scalars().first()
