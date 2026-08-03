from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question_option import QuestionOption
from app.domain.repositories.question_option_repository import QuestionOptionRepository
from app.infrastructure.persistence.models.question_option import QuestionOptionModel


class SQLQuestionOptionRepository(QuestionOptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> QuestionOption | None:
        stmt = select(QuestionOptionModel).where(QuestionOptionModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_question(self, question_id: str) -> list[QuestionOption]:
        stmt = (
            select(QuestionOptionModel)
            .where(
                QuestionOptionModel.question_id == question_id,
            )
            .order_by(QuestionOptionModel.display_order)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, option: QuestionOption) -> QuestionOption:
        model = QuestionOptionModel(
            id=option.id,
            question_id=option.question_id,
            code=option.code,
            text=option.text,
            value=option.value,
            score_value=option.score_value,
            severity=option.severity,
            color_hex=option.color_hex,
            recommendation_trigger=option.recommendation_trigger,
            follow_up_trigger=option.follow_up_trigger,
            medical_notes=option.medical_notes,
            display_order=option.display_order,
            is_active=option.is_active,
            created_at=option.created_at,
            updated_at=option.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return option

    async def update(self, option: QuestionOption) -> QuestionOption:
        stmt = select(QuestionOptionModel).where(QuestionOptionModel.id == option.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"QuestionOption with id {option.id} not found")

        model.question_id = option.question_id
        model.code = option.code
        model.text = option.text
        model.value = option.value
        model.score_value = option.score_value
        model.severity = option.severity
        model.color_hex = option.color_hex
        model.recommendation_trigger = option.recommendation_trigger
        model.follow_up_trigger = option.follow_up_trigger
        model.medical_notes = option.medical_notes
        model.display_order = option.display_order
        model.is_active = option.is_active
        model.updated_at = option.updated_at

        await self._session.flush()
        return option

    def _to_entity(self, model: QuestionOptionModel) -> QuestionOption:
        return QuestionOption(
            id=model.id,
            question_id=model.question_id,
            code=model.code,
            text=model.text,
            value=model.value,
            score_value=model.score_value,
            severity=model.severity,
            color_hex=model.color_hex,
            recommendation_trigger=model.recommendation_trigger,
            follow_up_trigger=model.follow_up_trigger,
            medical_notes=model.medical_notes,
            display_order=model.display_order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
