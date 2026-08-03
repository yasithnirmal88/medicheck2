from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.body_system import BodySystem
from app.domain.repositories.body_system_repository import BodySystemRepository
from app.infrastructure.persistence.models.body_system import BodySystemModel


class SQLBodySystemRepository(BodySystemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> BodySystem | None:
        stmt = select(BodySystemModel).where(BodySystemModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> BodySystem | None:
        stmt = select(BodySystemModel).where(BodySystemModel.code == code.upper())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all_active(self) -> list[BodySystem]:
        stmt = (
            select(BodySystemModel)
            .where(
                BodySystemModel.is_active.is_(True),
                BodySystemModel.deleted_at.is_(None),
            )
            .order_by(BodySystemModel.display_order)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, body_system: BodySystem) -> BodySystem:
        model = BodySystemModel(
            id=body_system.id,
            code=body_system.code,
            name=body_system.name,
            description=body_system.description,
            icon=body_system.icon,
            color_hex=body_system.color_hex,
            display_order=body_system.display_order,
            module_version=body_system.module_version,
            is_active=body_system.is_active,
            is_core=body_system.is_core,
            scoring_weight=body_system.scoring_weight,
            extra_metadata=body_system.metadata,
            created_at=body_system.created_at,
            updated_at=body_system.updated_at,
            deleted_at=body_system.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return body_system

    async def update(self, body_system: BodySystem) -> BodySystem:
        stmt = select(BodySystemModel).where(BodySystemModel.id == body_system.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"BodySystem with id {body_system.id} not found")

        model.code = body_system.code
        model.name = body_system.name
        model.description = body_system.description
        model.icon = body_system.icon
        model.color_hex = body_system.color_hex
        model.display_order = body_system.display_order
        model.module_version = body_system.module_version
        model.is_active = body_system.is_active
        model.is_core = body_system.is_core
        model.scoring_weight = body_system.scoring_weight
        model.extra_metadata = body_system.metadata
        model.updated_at = body_system.updated_at
        model.deleted_at = body_system.deleted_at

        await self._session.flush()
        return body_system

    def _to_entity(self, model: BodySystemModel) -> BodySystem:
        return BodySystem(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description or "",
            icon=model.icon,
            color_hex=model.color_hex,
            display_order=model.display_order,
            module_version=model.module_version,
            is_active=model.is_active,
            is_core=model.is_core,
            scoring_weight=model.scoring_weight,
            metadata=model.extra_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
