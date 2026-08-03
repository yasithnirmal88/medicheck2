from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.clinical_indicator import ClinicalIndicator


class ClinicalIndicatorRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> ClinicalIndicator | None:
        pass

    @abstractmethod
    async def find_by_key(self, key: str) -> ClinicalIndicator | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[ClinicalIndicator]:
        pass

    @abstractmethod
    async def find_by_disease(self, disease_id: str) -> list[ClinicalIndicator]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[ClinicalIndicator]:
        pass

    @abstractmethod
    async def create(self, indicator: ClinicalIndicator) -> ClinicalIndicator:
        pass

    @abstractmethod
    async def update(self, indicator: ClinicalIndicator) -> ClinicalIndicator:
        pass
