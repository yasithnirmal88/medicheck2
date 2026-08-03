from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.assessment_session import AssessmentSession


class AssessmentSessionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> AssessmentSession | None:
        pass

    @abstractmethod
    async def find_by_user(self, user_id: str) -> list[AssessmentSession]:
        pass

    @abstractmethod
    async def find_active_by_user(self, user_id: str) -> list[AssessmentSession]:
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> list[AssessmentSession]:
        pass

    @abstractmethod
    async def create(self, session: AssessmentSession) -> AssessmentSession:
        pass

    @abstractmethod
    async def update(self, session: AssessmentSession) -> AssessmentSession:
        pass

    @abstractmethod
    async def count_completed_by_user(self, user_id: str) -> int:
        pass
