from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.laboratory_test import LaboratoryTest


class LaboratoryTestRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> LaboratoryTest | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> LaboratoryTest | None:
        pass

    @abstractmethod
    async def find_by_loinc(self, loinc_code: str) -> LaboratoryTest | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[LaboratoryTest]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[LaboratoryTest]:
        pass

    @abstractmethod
    async def create(self, lab_test: LaboratoryTest) -> LaboratoryTest:
        pass

    @abstractmethod
    async def update(self, lab_test: LaboratoryTest) -> LaboratoryTest:
        pass
