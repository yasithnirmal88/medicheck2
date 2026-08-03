from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.body_system import BodySystem


class BodySystemRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> BodySystem | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> BodySystem | None:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[BodySystem]:
        pass

    @abstractmethod
    async def create(self, body_system: BodySystem) -> BodySystem:
        pass

    @abstractmethod
    async def update(self, body_system: BodySystem) -> BodySystem:
        pass
