from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.recommendation import Recommendation


class RecommendationRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Recommendation | None:
        pass

    @abstractmethod
    async def find_by_body_system(
        self, body_system_id: str
    ) -> list[Recommendation]:
        pass

    @abstractmethod
    async def find_by_disease(self, disease_id: str) -> list[Recommendation]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[Recommendation]:
        pass

    @abstractmethod
    async def create(self, recommendation: Recommendation) -> Recommendation:
        pass

    @abstractmethod
    async def update(self, recommendation: Recommendation) -> Recommendation:
        pass
