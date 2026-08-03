from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.disease import Disease


class DiseaseRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Disease | None:
        pass

    @abstractmethod
    async def find_by_icd10_code(self, code: str) -> Disease | None:
        pass

    @abstractmethod
    async def find_by_body_system(self, body_system_id: str) -> list[Disease]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[Disease]:
        pass

    @abstractmethod
    async def create(self, disease: Disease) -> Disease:
        pass

    @abstractmethod
    async def update(self, disease: Disease) -> Disease:
        pass
