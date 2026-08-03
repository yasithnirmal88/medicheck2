from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.nutrition_advice import NutritionAdvice
from app.domain.repositories.nutrition_advice_repository import (
    NutritionAdviceRepository,
)
from app.infrastructure.persistence.models.nutrition_advice import (
    NutritionAdviceModel,
)


class SQLNutritionAdviceRepository(NutritionAdviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> NutritionAdvice | None:
        stmt = select(NutritionAdviceModel).where(
            NutritionAdviceModel.id == id,
            NutritionAdviceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> NutritionAdvice | None:
        stmt = select(NutritionAdviceModel).where(
            NutritionAdviceModel.code == code,
            NutritionAdviceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[NutritionAdvice]:
        stmt = (
            select(NutritionAdviceModel)
            .where(
                NutritionAdviceModel.body_system_id == body_system_id,
                NutritionAdviceModel.deleted_at.is_(None),
            )
            .order_by(NutritionAdviceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[NutritionAdvice]:
        stmt = (
            select(NutritionAdviceModel)
            .where(
                NutritionAdviceModel.is_active.is_(True),
                NutritionAdviceModel.deleted_at.is_(None),
            )
            .order_by(NutritionAdviceModel.title)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, advice: NutritionAdvice) -> NutritionAdvice:
        model = NutritionAdviceModel(
            id=advice.id,
            body_system_id=advice.body_system_id,
            code=advice.code,
            title=advice.title,
            summary=advice.summary,
            details=advice.details,
            meal_type=advice.meal_type,
            dietary_restrictions=advice.dietary_restrictions,
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

    async def update(self, advice: NutritionAdvice) -> NutritionAdvice:
        stmt = select(NutritionAdviceModel).where(
            NutritionAdviceModel.id == advice.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"NutritionAdvice with id {advice.id} not found")

        model.body_system_id = advice.body_system_id
        model.code = advice.code
        model.title = advice.title
        model.summary = advice.summary
        model.details = advice.details
        model.meal_type = advice.meal_type
        model.dietary_restrictions = advice.dietary_restrictions
        model.is_active = advice.is_active
        model.version = advice.version
        model.status = advice.status
        model.updated_by = advice.updated_by
        model.updated_at = advice.updated_at
        model.deleted_at = advice.deleted_at

        await self._session.flush()
        return advice

    def _to_entity(self, model: NutritionAdviceModel) -> NutritionAdvice:
        return NutritionAdvice(
            id=model.id,
            body_system_id=model.body_system_id,
            code=model.code,
            title=model.title,
            summary=model.summary,
            details=model.details,
            meal_type=model.meal_type,
            dietary_restrictions=model.dietary_restrictions or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
