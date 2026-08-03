from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.question_option import QuestionOption


class QuestionOptionRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> QuestionOption | None:
        pass

    @abstractmethod
    async def find_by_question(self, question_id: str) -> list[QuestionOption]:
        pass

    @abstractmethod
    async def create(self, option: QuestionOption) -> QuestionOption:
        pass

    @abstractmethod
    async def update(self, option: QuestionOption) -> QuestionOption:
        pass
