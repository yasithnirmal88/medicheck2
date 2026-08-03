from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.question_group import QuestionGroup


class QuestionGroupRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> QuestionGroup | None:
        pass

    @abstractmethod
    async def find_by_body_system(self, body_system_id: str) -> list[QuestionGroup]:
        pass

    @abstractmethod
    async def create(self, group: QuestionGroup) -> QuestionGroup:
        pass

    @abstractmethod
    async def update(self, group: QuestionGroup) -> QuestionGroup:
        pass
