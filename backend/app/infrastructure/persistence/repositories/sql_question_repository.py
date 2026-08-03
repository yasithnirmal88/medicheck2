from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question import Question
from app.domain.repositories.question_repository import QuestionRepository
from app.infrastructure.persistence.models.question import QuestionModel


class SQLQuestionRepository(QuestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> Question | None:
        stmt = select(QuestionModel).where(QuestionModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> Question | None:
        stmt = select(QuestionModel).where(QuestionModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(self, body_system_id: str) -> list[Question]:
        stmt = (
            select(QuestionModel)
            .where(
                QuestionModel.body_system_id == body_system_id,
                QuestionModel.deleted_at.is_(None),
            )
            .order_by(QuestionModel.order_index)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_group(self, group_id: str) -> list[Question]:
        stmt = (
            select(QuestionModel)
            .where(
                QuestionModel.question_group_id == group_id,
                QuestionModel.deleted_at.is_(None),
            )
            .order_by(QuestionModel.order_index)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_questionnaire(self, questionnaire_id: str) -> list[Question]:
        _ = questionnaire_id
        stmt = (
            select(QuestionModel)
            .where(
                QuestionModel.deleted_at.is_(None),
            )
            .order_by(QuestionModel.order_index)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_active(self) -> list[Question]:
        stmt = (
            select(QuestionModel)
            .where(
                QuestionModel.status == "active",
                QuestionModel.deleted_at.is_(None),
            )
            .order_by(QuestionModel.order_index)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def search(self, query: str) -> list[Question]:
        stmt = (
            select(QuestionModel)
            .where(
                QuestionModel.deleted_at.is_(None),
                or_(
                    QuestionModel.code.ilike(f"%{query}%"),
                    QuestionModel.text.ilike(f"%{query}%"),
                ),
            )
            .order_by(QuestionModel.order_index)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, question: Question) -> Question:
        model = QuestionModel(
            id=question.id,
            body_system_id=question.body_system_id,
            question_group_id=question.question_group_id,
            code=question.code,
            question_type=question.question_type.value,
            text=(
                question.text if isinstance(question.text, str) else str(question.text)
            ),
            description=question.description,
            tooltip=question.tooltip,
            medical_notes=question.medical_notes,
            evidence_ref=question.evidence_ref,
            order_index=question.order_index,
            priority=question.priority,
            difficulty=question.difficulty.value,
            status=question.status.value,
            is_required=question.is_required,
            validation_rules=question.validation_rules,
            scoring_weight=question.scoring_weight,
            version=question.version,
            created_by=question.created_by,
            updated_by=question.updated_by,
            activation_date=question.activation_date,
            expiration_date=question.expiration_date,
            created_at=question.created_at,
            updated_at=question.updated_at,
            deleted_at=question.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return question

    async def update(self, question: Question) -> Question:
        stmt = select(QuestionModel).where(QuestionModel.id == question.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Question with id {question.id} not found")

        model.body_system_id = question.body_system_id
        model.question_group_id = question.question_group_id
        model.code = question.code
        model.question_type = question.question_type.value
        model.text = (
            question.text if isinstance(question.text, str) else str(question.text)
        )
        model.description = question.description
        model.tooltip = question.tooltip
        model.medical_notes = question.medical_notes
        model.evidence_ref = question.evidence_ref
        model.order_index = question.order_index
        model.priority = question.priority
        model.difficulty = question.difficulty.value
        model.status = question.status.value
        model.is_required = question.is_required
        model.validation_rules = question.validation_rules
        model.scoring_weight = question.scoring_weight
        model.version = question.version
        model.updated_by = question.updated_by
        model.activation_date = question.activation_date
        model.expiration_date = question.expiration_date
        model.updated_at = question.updated_at
        model.deleted_at = question.deleted_at

        await self._session.flush()
        return question

    async def delete(self, id: str) -> None:
        stmt = select(QuestionModel).where(QuestionModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    def _to_entity(self, model: QuestionModel) -> Question:
        from app.domain.entities.question import (
            QuestionDifficulty,
            QuestionStatus,
            QuestionType,
        )

        return Question(
            id=model.id,
            body_system_id=model.body_system_id,
            question_group_id=model.question_group_id,
            code=model.code,
            question_type=QuestionType(model.question_type),
            text=model.text,
            description=model.description,
            tooltip=model.tooltip,
            medical_notes=model.medical_notes,
            evidence_ref=model.evidence_ref,
            order_index=model.order_index,
            priority=model.priority,
            difficulty=QuestionDifficulty(model.difficulty),
            status=QuestionStatus(model.status),
            is_required=model.is_required,
            validation_rules=model.validation_rules or {},
            scoring_weight=model.scoring_weight,
            version=model.version,
            created_by=model.created_by,
            updated_by=model.updated_by,
            activation_date=model.activation_date,
            expiration_date=model.expiration_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
