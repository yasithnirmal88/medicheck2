from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.nutrition_advice import NutritionAdvice


class NutritionAdviceRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> NutritionAdvice | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> NutritionAdvice | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[NutritionAdvice]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[NutritionAdvice]:
        pass

    @abstractmethod
    async def create(self, advice: NutritionAdvice) -> NutritionAdvice:
        pass

    @abstractmethod
    async def update(self, advice: NutritionAdvice) -> NutritionAdvice:
        pass
