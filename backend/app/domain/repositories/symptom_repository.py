from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.symptom import Symptom


class SymptomRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Symptom | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> Symptom | None:
        pass

    @abstractmethod
    async def find_by_body_system(self, body_system_id: str) -> list[Symptom]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[Symptom]:
        pass

    @abstractmethod
    async def create(self, symptom: Symptom) -> Symptom:
        pass

    @abstractmethod
    async def update(self, symptom: Symptom) -> Symptom:
        pass
