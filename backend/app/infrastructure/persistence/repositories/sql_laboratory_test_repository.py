from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.laboratory_test import LaboratoryTest
from app.domain.repositories.laboratory_test_repository import LaboratoryTestRepository
from app.infrastructure.persistence.models.laboratory_test import LaboratoryTestModel


class SQLLaboratoryTestRepository(LaboratoryTestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> LaboratoryTest | None:
        stmt = select(LaboratoryTestModel).where(
            LaboratoryTestModel.id == id, LaboratoryTestModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> LaboratoryTest | None:
        stmt = select(LaboratoryTestModel).where(
            LaboratoryTestModel.code == code,
            LaboratoryTestModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_loinc(self, loinc_code: str) -> LaboratoryTest | None:
        stmt = select(LaboratoryTestModel).where(
            LaboratoryTestModel.loinc_code == loinc_code,
            LaboratoryTestModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[LaboratoryTest]:
        stmt = (
            select(LaboratoryTestModel)
            .where(
                LaboratoryTestModel.body_system_id == body_system_id,
                LaboratoryTestModel.deleted_at.is_(None),
            )
            .order_by(LaboratoryTestModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[LaboratoryTest]:
        stmt = (
            select(LaboratoryTestModel)
            .where(
                LaboratoryTestModel.is_active.is_(True),
                LaboratoryTestModel.deleted_at.is_(None),
            )
            .order_by(LaboratoryTestModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, lab_test: LaboratoryTest) -> LaboratoryTest:
        model = LaboratoryTestModel(
            id=lab_test.id,
            code=lab_test.code,
            name=lab_test.name,
            description=lab_test.description,
            body_system_id=lab_test.body_system_id,
            loinc_code=lab_test.loinc_code,
            normal_range=lab_test.normal_range,
            unit=lab_test.unit,
            reference_range_min=lab_test.reference_range_min,
            reference_range_max=lab_test.reference_range_max,
            critical_low=lab_test.critical_low,
            critical_high=lab_test.critical_high,
            is_active=lab_test.is_active,
            version=lab_test.version,
            status=lab_test.status,
            created_by=lab_test.created_by,
            updated_by=lab_test.updated_by,
            created_at=lab_test.created_at,
            updated_at=lab_test.updated_at,
            deleted_at=lab_test.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return lab_test

    async def update(self, lab_test: LaboratoryTest) -> LaboratoryTest:
        stmt = select(LaboratoryTestModel).where(LaboratoryTestModel.id == lab_test.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"LaboratoryTest with id {lab_test.id} not found")

        model.code = lab_test.code
        model.name = lab_test.name
        model.description = lab_test.description
        model.body_system_id = lab_test.body_system_id
        model.loinc_code = lab_test.loinc_code
        model.normal_range = lab_test.normal_range
        model.unit = lab_test.unit
        model.reference_range_min = lab_test.reference_range_min
        model.reference_range_max = lab_test.reference_range_max
        model.critical_low = lab_test.critical_low
        model.critical_high = lab_test.critical_high
        model.is_active = lab_test.is_active
        model.version = lab_test.version
        model.status = lab_test.status
        model.updated_by = lab_test.updated_by
        model.updated_at = lab_test.updated_at
        model.deleted_at = lab_test.deleted_at

        await self._session.flush()
        return lab_test

    def _to_entity(self, model: LaboratoryTestModel) -> LaboratoryTest:
        return LaboratoryTest(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description or "",
            body_system_id=model.body_system_id,
            loinc_code=model.loinc_code,
            normal_range=model.normal_range,
            unit=model.unit,
            reference_range_min=model.reference_range_min,
            reference_range_max=model.reference_range_max,
            critical_low=model.critical_low,
            critical_high=model.critical_high,
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
