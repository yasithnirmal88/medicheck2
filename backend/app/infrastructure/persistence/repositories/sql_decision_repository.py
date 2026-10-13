from __future__ import annotations

from sqlalchemy import delete, insert, select
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
        existing = await self.get_result_by_session(data["session_id"])
        if existing is not None:
            return existing
        stmt = insert(AssessmentResultModel).values(**data).returning(
            AssessmentResultModel
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def clear_result_details(self, result_id: str) -> None:
        for model in (
            ActivatedIndicatorModel,
            ActivatedConditionModel,
            GeneratedRecommendationModel,
            GeneratedLaboratoryTestModel,
            GeneratedScreeningModel,
            ExplanationRecordModel,
        ):
            await self.session.execute(
                delete(model).where(model.result_id == result_id)
            )

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
        ).returning(ActivatedIndicatorModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

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
        ).returning(ActivatedConditionModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

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
        ).returning(GeneratedRecommendationModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_laboratory_test(
        self, result_id: str, laboratory_test_id: str, reason: str | None
    ) -> GeneratedLaboratoryTestModel:
        stmt = insert(GeneratedLaboratoryTestModel).values(
            result_id=result_id, laboratory_test_id=laboratory_test_id, reason=reason
        ).returning(GeneratedLaboratoryTestModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_screening(
        self, result_id: str, name: str, reason: str | None
    ) -> GeneratedScreeningModel:
        stmt = insert(GeneratedScreeningModel).values(
            result_id=result_id, name=name, reason=reason
        ).returning(GeneratedScreeningModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_explanation(
        self, result_id: str, source_type: str, source_id: str | None, text: str | None
    ) -> ExplanationRecordModel:
        stmt = insert(ExplanationRecordModel).values(
            result_id=result_id, source_type=source_type, source_id=source_id, text=text
        ).returning(ExplanationRecordModel)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_result_by_session(
        self, session_id: str
    ) -> AssessmentResultModel | None:
        q = (
            select(AssessmentResultModel)
            .where(AssessmentResultModel.session_id == session_id)
            .order_by(
                AssessmentResultModel.created_at.desc().nulls_last(),
                AssessmentResultModel.id.desc(),
            )
            .limit(1)
        )
        r = await self.session.execute(q)
        return r.scalar_one_or_none()

    async def get_result(self, result_id: str) -> AssessmentResultModel | None:
        q = select(AssessmentResultModel).where(AssessmentResultModel.id == result_id)
        r = await self.session.execute(q)
        return r.scalars().first()
