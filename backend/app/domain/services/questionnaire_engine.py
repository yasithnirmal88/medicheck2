from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.assessment_answer import AssessmentAnswer
from app.domain.entities.assessment_progress import AssessmentProgress
from app.domain.entities.assessment_session import AssessmentSession
from app.domain.entities.question import Question


class QuestionnaireEngine(ABC):
    @abstractmethod
    async def load_questions(self, session: AssessmentSession) -> list[Question]:
        pass

    @abstractmethod
    async def get_next_question(
        self, session: AssessmentSession, current_question: Question | None = None
    ) -> Question | None:
        pass

    @abstractmethod
    async def evaluate_branching(
        self, session: AssessmentSession, answer: AssessmentAnswer
    ) -> list[str]:
        pass

    @abstractmethod
    async def calculate_progress(
        self, session: AssessmentSession
    ) -> AssessmentProgress:
        pass

    @abstractmethod
    async def validate_answer(self, question: Question, answer: dict[str, object]) -> list[str]:
        pass
