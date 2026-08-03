from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.exercise_program import ExerciseProgram


class ExerciseProgramRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> ExerciseProgram | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> ExerciseProgram | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[ExerciseProgram]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[ExerciseProgram]:
        pass

    @abstractmethod
    async def create(self, program: ExerciseProgram) -> ExerciseProgram:
        pass

    @abstractmethod
    async def update(self, program: ExerciseProgram) -> ExerciseProgram:
        pass
