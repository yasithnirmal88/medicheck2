from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exercise_program import ExerciseProgram
from app.domain.repositories.exercise_program_repository import (
    ExerciseProgramRepository,
)
from app.infrastructure.persistence.models.exercise_program import (
    ExerciseProgramModel,
)


class SQLExerciseProgramRepository(ExerciseProgramRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> ExerciseProgram | None:
        stmt = select(ExerciseProgramModel).where(
            ExerciseProgramModel.id == id,
            ExerciseProgramModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_code(self, code: str) -> ExerciseProgram | None:
        stmt = select(ExerciseProgramModel).where(
            ExerciseProgramModel.code == code,
            ExerciseProgramModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[ExerciseProgram]:
        stmt = (
            select(ExerciseProgramModel)
            .where(
                ExerciseProgramModel.body_system_id == body_system_id,
                ExerciseProgramModel.deleted_at.is_(None),
            )
            .order_by(ExerciseProgramModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_all_active(self) -> list[ExerciseProgram]:
        stmt = (
            select(ExerciseProgramModel)
            .where(
                ExerciseProgramModel.is_active.is_(True),
                ExerciseProgramModel.deleted_at.is_(None),
            )
            .order_by(ExerciseProgramModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, program: ExerciseProgram) -> ExerciseProgram:
        model = ExerciseProgramModel(
            id=program.id,
            body_system_id=program.body_system_id,
            code=program.code,
            name=program.name,
            description=program.description,
            duration_minutes=program.duration_minutes,
            frequency_per_week=program.frequency_per_week,
            intensity=program.intensity,
            contraindications=program.contraindications,
            is_active=program.is_active,
            version=program.version,
            status=program.status,
            created_by=program.created_by,
            updated_by=program.updated_by,
            created_at=program.created_at,
            updated_at=program.updated_at,
            deleted_at=program.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return program

    async def update(self, program: ExerciseProgram) -> ExerciseProgram:
        stmt = select(ExerciseProgramModel).where(
            ExerciseProgramModel.id == program.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"ExerciseProgram with id {program.id} not found")

        model.body_system_id = program.body_system_id
        model.code = program.code
        model.name = program.name
        model.description = program.description
        model.duration_minutes = program.duration_minutes
        model.frequency_per_week = program.frequency_per_week
        model.intensity = program.intensity
        model.contraindications = program.contraindications
        model.is_active = program.is_active
        model.version = program.version
        model.status = program.status
        model.updated_by = program.updated_by
        model.updated_at = program.updated_at
        model.deleted_at = program.deleted_at

        await self._session.flush()
        return program

    def _to_entity(self, model: ExerciseProgramModel) -> ExerciseProgram:
        return ExerciseProgram(
            id=model.id,
            body_system_id=model.body_system_id,
            code=model.code,
            name=model.name,
            description=model.description,
            duration_minutes=model.duration_minutes,
            frequency_per_week=model.frequency_per_week,
            intensity=model.intensity,
            contraindications=model.contraindications or [],
            is_active=model.is_active,
            version=model.version,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
