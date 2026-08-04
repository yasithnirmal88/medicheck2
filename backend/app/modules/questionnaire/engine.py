from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.assessment_answer import AssessmentAnswer
from app.domain.entities.assessment_progress import AssessmentProgress
from app.domain.entities.assessment_session import AssessmentSession
from app.domain.entities.question import Question
from app.domain.services.questionnaire_engine import QuestionnaireEngine
from app.infrastructure.persistence.models.assessment_answer import AssessmentAnswerModel
from app.infrastructure.persistence.models.question_dependency import QuestionDependencyModel
from app.infrastructure.persistence.repositories.sql_assessment_session_repository import (
    SQLAssessmentSessionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_group_repository import (
    SQLQuestionGroupRepository,
)
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)
from app.modules.questionnaire.branching import BranchingEvaluator
from app.modules.questionnaire.dependency_evaluator import DependencyEvaluator
from app.modules.questionnaire.scoring import ScoringEngine
from app.modules.questionnaire.validation import ValidationEngine


class QuestionnaireEngineImpl(QuestionnaireEngine):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._question_repo = SQLQuestionRepository(session)
        self._option_repo = SQLQuestionOptionRepository(session)
        self._group_repo = SQLQuestionGroupRepository(session)
        self._session_repo = SQLAssessmentSessionRepository(session)
        self._branching = BranchingEvaluator()
        self._scoring = ScoringEngine()
        self._validation = ValidationEngine()
        self._dependency = DependencyEvaluator()

    async def load_questions(self, session: AssessmentSession) -> list[Question]:
        if session.questionnaire_template_id:
            return await self._question_repo.find_by_questionnaire(
                session.questionnaire_template_id
            )
        return await self._question_repo.find_active()

    async def get_next_question(
        self, session: AssessmentSession, current_question: Question | None = None
    ) -> Question | None:
        questions = await self.load_questions(session)
        answers = await self._get_answers_map(session.id)
        user_attrs = session.metadata.get("user_attributes", {})

        # If we have a current_question, look for next in same group
        if current_question:
            group_questions = [
                q
                for q in questions
                if q.question_group_id == current_question.question_group_id
            ]
            found_current = False
            for q in group_questions:
                if q.id == current_question.id:
                    found_current = True
                    continue
                if (
                    found_current
                    and q.id not in answers
                    and await self._is_question_visible(q, answers, user_attrs)
                ):
                    return q

        # Find first unanswered visible question
        for q in questions:
            if q.id not in answers and await self._is_question_visible(
                q, answers, user_attrs
            ):
                return q

        return None

    async def evaluate_branching(
        self, session: AssessmentSession, answer: AssessmentAnswer
    ) -> list[str]:
        questions = await self.load_questions(session)
        answers = await self._get_answers_map(session.id)
        answers[answer.question_id] = answer.response_value.get("value")

        user_attrs = session.metadata.get("user_attributes", {})
        branch_path: list[str] = [answer.question_id]

        # Evaluate branch rules for all questions
        for q in questions:
            if q.id not in answers:
                deps = await self._get_dependencies(q.id)
                if not self._branching.evaluate_visibility(deps, answers, user_attrs):
                    branch_path.append(f"hidden:{q.id}")

        return branch_path

    async def calculate_progress(
        self, session: AssessmentSession
    ) -> AssessmentProgress:
        questions = await self.load_questions(session)
        answers = await self._get_answers_map(session.id)
        total = len(questions)
        answered = len(answers)

        current_section = None
        if session.current_group_id:
            group = await self._group_repo.find_by_id(session.current_group_id)
            if group:
                current_section = group.name

        percentage = (answered / total * 100) if total > 0 else 0.0
        estimated_remaining = max(0, (total - answered) * 30)

        return AssessmentProgress(
            id="",
            session_id=session.id,
            current_section=current_section,
            completed_questions=answered,
            total_questions=total,
            answered_questions=answered,
            skipped_questions=0,
            estimated_time_remaining=estimated_remaining,
            completion_percentage=round(percentage, 1),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def validate_answer(
        self, question: Question, answer: dict[str, Any]
    ) -> list[str]:
        return await self._validation.validate(question, answer)

    async def _is_question_visible(
        self,
        question: Question,
        answers_map: dict[str, Any],
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        deps = await self._get_dependencies(question.id)
        return self._branching.evaluate_visibility(deps, answers_map, user_attributes)

    async def _get_answers_map(self, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            return {}
        rows = await self._session.execute(
            select(AssessmentAnswerModel).where(
                AssessmentAnswerModel.session_id == session_id
            )
        )
        answers_map: dict[str, Any] = {}
        for row in rows.scalars().all():
            rv = row.response_value or {}
            if isinstance(rv, dict):
                answers_map[row.question_id] = rv.get("value")
            else:
                answers_map[row.question_id] = rv
        return answers_map

    async def _get_dependencies(self, question_id: str) -> list[dict[str, Any]]:
        rows = await self._session.execute(
            select(QuestionDependencyModel).where(
                QuestionDependencyModel.question_id == question_id
            )
        )
        return [
            {
                "question_id": dep.question_id,
                "depends_on_question_id": dep.depends_on_question_id,
                "condition_type": dep.condition_type,
                "condition_value": dep.condition_value,
                "logic_operator": dep.logic_operator,
                "group_id": dep.group_id,
            }
            for dep in rows.scalars().all()
        ]
