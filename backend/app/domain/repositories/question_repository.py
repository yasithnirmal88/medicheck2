from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.question import Question


class QuestionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Question | None:
        pass

    @abstractmethod
    async def find_by_code(self, code: str) -> Question | None:
        pass

    @abstractmethod
    async def find_by_body_system(self, body_system_id: str) -> list[Question]:
        pass

    @abstractmethod
    async def find_by_group(self, group_id: str) -> list[Question]:
        pass

    @abstractmethod
    async def find_by_questionnaire(self, questionnaire_id: str) -> list[Question]:
        pass

    @abstractmethod
    async def find_active(self) -> list[Question]:
        pass

    @abstractmethod
    async def search(self, query: str) -> list[Question]:
        pass

    @abstractmethod
    async def create(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def update(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
