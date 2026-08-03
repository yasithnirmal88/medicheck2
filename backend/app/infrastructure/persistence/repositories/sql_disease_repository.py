from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.disease import Disease
from app.domain.repositories.disease_repository import DiseaseRepository
from app.infrastructure.persistence.models.disease import DiseaseModel


class SQLDiseaseRepository(DiseaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> Disease | None:
        stmt = select(DiseaseModel).where(
            DiseaseModel.id == id, DiseaseModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_icd10_code(self, code: str) -> Disease | None:
        stmt = select(DiseaseModel).where(
            DiseaseModel.icd10_code == code.upper(),
            DiseaseModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(self, body_system_id: str) -> list[Disease]:
        stmt = (
            select(DiseaseModel)
            .where(
                DiseaseModel.body_system_id == body_system_id,
                DiseaseModel.deleted_at.is_(None),
            )
            .order_by(DiseaseModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[Disease]:
        stmt = (
            select(DiseaseModel)
            .where(
                DiseaseModel.is_active.is_(True),
                DiseaseModel.deleted_at.is_(None),
            )
            .order_by(DiseaseModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, disease: Disease) -> Disease:
        model = DiseaseModel(
            id=disease.id,
            icd10_code=disease.icd10_code,
            name=disease.name,
            description=disease.description,
            body_system_id=disease.body_system_id,
            risk_factors=disease.risk_factors,
            early_indicators=disease.early_indicators,
            is_active=disease.is_active,
            version=disease.version,
            status=disease.status,
            created_by=disease.created_by,
            updated_by=disease.updated_by,
            created_at=disease.created_at,
            updated_at=disease.updated_at,
            deleted_at=disease.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return disease

    async def update(self, disease: Disease) -> Disease:
        stmt = select(DiseaseModel).where(DiseaseModel.id == disease.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Disease with id {disease.id} not found")

        model.icd10_code = disease.icd10_code
        model.name = disease.name
        model.description = disease.description
        model.body_system_id = disease.body_system_id
        model.risk_factors = disease.risk_factors
        model.early_indicators = disease.early_indicators
        model.is_active = disease.is_active
        model.version = disease.version
        model.status = disease.status
        model.updated_by = disease.updated_by
        model.updated_at = disease.updated_at
        model.deleted_at = disease.deleted_at

        await self._session.flush()
        return disease

    def _to_entity(self, model: DiseaseModel) -> Disease:
        return Disease(
            id=model.id,
            icd10_code=model.icd10_code,
            name=model.name,
            description=model.description or "",
            body_system_id=model.body_system_id,
            risk_factors=model.risk_factors or [],
            early_indicators=model.early_indicators or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
