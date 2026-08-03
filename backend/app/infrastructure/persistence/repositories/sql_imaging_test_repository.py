from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.imaging_test import ImagingTest
from app.domain.repositories.imaging_test_repository import ImagingTestRepository
from app.infrastructure.persistence.models.imaging_test import ImagingTestModel


class SQLImagingTestRepository(ImagingTestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> ImagingTest | None:
        stmt = select(ImagingTestModel).where(
            ImagingTestModel.id == id, ImagingTestModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> ImagingTest | None:
        stmt = select(ImagingTestModel).where(
            ImagingTestModel.code == code,
            ImagingTestModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(self, body_system_id: str) -> list[ImagingTest]:
        stmt = (
            select(ImagingTestModel)
            .where(
                ImagingTestModel.body_system_id == body_system_id,
                ImagingTestModel.deleted_at.is_(None),
            )
            .order_by(ImagingTestModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[ImagingTest]:
        stmt = (
            select(ImagingTestModel)
            .where(
                ImagingTestModel.is_active.is_(True),
                ImagingTestModel.deleted_at.is_(None),
            )
            .order_by(ImagingTestModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, imaging_test: ImagingTest) -> ImagingTest:
        model = ImagingTestModel(
            id=imaging_test.id,
            code=imaging_test.code,
            name=imaging_test.name,
            description=imaging_test.description,
            body_system_id=imaging_test.body_system_id,
            modality=imaging_test.modality,
            is_contrast_required=imaging_test.is_contrast_required,
            preparation_notes=imaging_test.preparation_notes,
            is_active=imaging_test.is_active,
            version=imaging_test.version,
            status=imaging_test.status,
            created_by=imaging_test.created_by,
            updated_by=imaging_test.updated_by,
            created_at=imaging_test.created_at,
            updated_at=imaging_test.updated_at,
            deleted_at=imaging_test.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return imaging_test

    async def update(self, imaging_test: ImagingTest) -> ImagingTest:
        stmt = select(ImagingTestModel).where(ImagingTestModel.id == imaging_test.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"ImagingTest with id {imaging_test.id} not found")

        model.code = imaging_test.code
        model.name = imaging_test.name
        model.description = imaging_test.description
        model.body_system_id = imaging_test.body_system_id
        model.modality = imaging_test.modality
        model.is_contrast_required = imaging_test.is_contrast_required
        model.preparation_notes = imaging_test.preparation_notes
        model.is_active = imaging_test.is_active
        model.version = imaging_test.version
        model.status = imaging_test.status
        model.updated_by = imaging_test.updated_by
        model.updated_at = imaging_test.updated_at
        model.deleted_at = imaging_test.deleted_at

        await self._session.flush()
        return imaging_test

    def _to_entity(self, model: ImagingTestModel) -> ImagingTest:
        return ImagingTest(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description or "",
            body_system_id=model.body_system_id,
            modality=model.modality,
            is_contrast_required=model.is_contrast_required,
            preparation_notes=model.preparation_notes,
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
