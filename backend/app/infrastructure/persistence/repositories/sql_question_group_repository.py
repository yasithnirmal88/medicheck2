from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question_group import QuestionGroup
from app.domain.repositories.question_group_repository import QuestionGroupRepository
from app.infrastructure.persistence.models.question_group import QuestionGroupModel


class SQLQuestionGroupRepository(QuestionGroupRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> QuestionGroup | None:
        stmt = select(QuestionGroupModel).where(QuestionGroupModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(self, body_system_id: str) -> list[QuestionGroup]:
        stmt = (
            select(QuestionGroupModel)
            .where(
                QuestionGroupModel.body_system_id == body_system_id,
            )
            .order_by(QuestionGroupModel.display_order)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, group: QuestionGroup) -> QuestionGroup:
        model = QuestionGroupModel(
            id=group.id,
            body_system_id=group.body_system_id,
            code=group.code,
            name=group.name,
            description=group.description,
            display_order=group.display_order,
            is_active=group.is_active,
            extra_metadata=group.metadata,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return group

    async def update(self, group: QuestionGroup) -> QuestionGroup:
        stmt = select(QuestionGroupModel).where(QuestionGroupModel.id == group.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"QuestionGroup with id {group.id} not found")

        model.body_system_id = group.body_system_id
        model.code = group.code
        model.name = group.name
        model.description = group.description
        model.display_order = group.display_order
        model.is_active = group.is_active
        model.extra_metadata = group.metadata
        model.updated_at = group.updated_at

        await self._session.flush()
        return group

    def _to_entity(self, model: QuestionGroupModel) -> QuestionGroup:
        return QuestionGroup(
            id=model.id,
            body_system_id=model.body_system_id,
            code=model.code,
            name=model.name,
            description=model.description,
            display_order=model.display_order,
            is_active=model.is_active,
            metadata=model.extra_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
