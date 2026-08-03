from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.imaging_test import ImagingTest


class ImagingTestRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> ImagingTest | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> ImagingTest | None:
        pass

    @abstractmethod
    async def find_by_body_system(self, body_system_id: str) -> list[ImagingTest]:
        pass

    @abstractmethod
    async def find_all_active(self) -> list[ImagingTest]:
        pass

    @abstractmethod
    async def create(self, imaging_test: ImagingTest) -> ImagingTest:
        pass

    @abstractmethod
    async def update(self, imaging_test: ImagingTest) -> ImagingTest:
        pass
