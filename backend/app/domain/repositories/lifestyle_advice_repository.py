from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.lifestyle_advice import LifestyleAdvice


class LifestyleAdviceRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> LifestyleAdvice | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> LifestyleAdvice | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[LifestyleAdvice]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[LifestyleAdvice]:
        pass

    @abstractmethod
    async def create(self, advice: LifestyleAdvice) -> LifestyleAdvice:
        pass

    @abstractmethod
    async def update(self, advice: LifestyleAdvice) -> LifestyleAdvice:
        pass
