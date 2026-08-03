from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.symptom import Symptom
from app.domain.repositories.symptom_repository import SymptomRepository
from app.infrastructure.persistence.models.symptom import SymptomModel


class SQLSymptomRepository(SymptomRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> Symptom | None:
        stmt = select(SymptomModel).where(
            SymptomModel.id == id, SymptomModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> Symptom | None:
        stmt = select(SymptomModel).where(
            SymptomModel.code == code, SymptomModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(self, body_system_id: str) -> list[Symptom]:
        stmt = (
            select(SymptomModel)
            .where(
                SymptomModel.body_system_id == body_system_id,
                SymptomModel.deleted_at.is_(None),
            )
            .order_by(SymptomModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[Symptom]:
        stmt = (
            select(SymptomModel)
            .where(
                SymptomModel.is_active.is_(True),
                SymptomModel.deleted_at.is_(None),
            )
            .order_by(SymptomModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, symptom: Symptom) -> Symptom:
        model = SymptomModel(
            id=symptom.id,
            body_system_id=symptom.body_system_id,
            code=symptom.code,
            name=symptom.name,
            description=symptom.description,
            severity=symptom.severity,
            duration_rule=symptom.duration_rule,
            is_active=symptom.is_active,
            version=symptom.version,
            status=symptom.status,
            created_by=symptom.created_by,
            updated_by=symptom.updated_by,
            created_at=symptom.created_at,
            updated_at=symptom.updated_at,
            deleted_at=symptom.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return symptom

    async def update(self, symptom: Symptom) -> Symptom:
        stmt = select(SymptomModel).where(SymptomModel.id == symptom.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Symptom with id {symptom.id} not found")

        model.body_system_id = symptom.body_system_id
        model.code = symptom.code
        model.name = symptom.name
        model.description = symptom.description
        model.severity = symptom.severity
        model.duration_rule = symptom.duration_rule
        model.is_active = symptom.is_active
        model.version = symptom.version
        model.status = symptom.status
        model.updated_by = symptom.updated_by
        model.updated_at = symptom.updated_at
        model.deleted_at = symptom.deleted_at

        await self._session.flush()
        return symptom

    def _to_entity(self, model: SymptomModel) -> Symptom:
        return Symptom(
            id=model.id,
            body_system_id=model.body_system_id,
            code=model.code,
            name=model.name,
            description=model.description or "",
            severity=model.severity,
            duration_rule=model.duration_rule,
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
