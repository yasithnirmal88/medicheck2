from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.lifestyle_advice import LifestyleAdvice
from app.domain.repositories.lifestyle_advice_repository import (
    LifestyleAdviceRepository,
)
from app.infrastructure.persistence.models.lifestyle_advice import LifestyleAdviceModel


class SQLLifestyleAdviceRepository(LifestyleAdviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> LifestyleAdvice | None:
        stmt = select(LifestyleAdviceModel).where(
            LifestyleAdviceModel.id == id,
            LifestyleAdviceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> LifestyleAdvice | None:
        stmt = select(LifestyleAdviceModel).where(
            LifestyleAdviceModel.code == code,
            LifestyleAdviceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[LifestyleAdvice]:
        stmt = (
            select(LifestyleAdviceModel)
            .where(
                LifestyleAdviceModel.body_system_id == body_system_id,
                LifestyleAdviceModel.deleted_at.is_(None),
            )
            .order_by(LifestyleAdviceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[LifestyleAdvice]:
        stmt = (
            select(LifestyleAdviceModel)
            .where(
                LifestyleAdviceModel.is_active.is_(True),
                LifestyleAdviceModel.deleted_at.is_(None),
            )
            .order_by(LifestyleAdviceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, advice: LifestyleAdvice) -> LifestyleAdvice:
        model = LifestyleAdviceModel(
            id=advice.id,
            body_system_id=advice.body_system_id,
            code=advice.code,
            title=advice.title,
            summary=advice.summary,
            details=advice.details,
            category=advice.category,
            tags=advice.tags,
            is_active=advice.is_active,
            version=advice.version,
            status=advice.status,
            created_by=advice.created_by,
            updated_by=advice.updated_by,
            created_at=advice.created_at,
            updated_at=advice.updated_at,
            deleted_at=advice.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return advice

    async def update(self, advice: LifestyleAdvice) -> LifestyleAdvice:
        stmt = select(LifestyleAdviceModel).where(
            LifestyleAdviceModel.id == advice.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"LifestyleAdvice with id {advice.id} not found")

        model.body_system_id = advice.body_system_id
        model.code = advice.code
        model.title = advice.title
        model.summary = advice.summary
        model.details = advice.details
        model.category = advice.category
        model.tags = advice.tags
        model.is_active = advice.is_active
        model.version = advice.version
        model.status = advice.status
        model.updated_by = advice.updated_by
        model.updated_at = advice.updated_at
        model.deleted_at = advice.deleted_at

        await self._session.flush()
        return advice

    def _to_entity(self, model: LifestyleAdviceModel) -> LifestyleAdvice:
        return LifestyleAdvice(
            id=model.id,
            body_system_id=model.body_system_id,
            code=model.code,
            title=model.title,
            summary=model.summary,
            details=model.details,
            category=model.category,
            tags=model.tags or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
