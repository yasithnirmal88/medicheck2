from __future__ import annotations

from typing import Any

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.assessment_answer import AssessmentAnswer
from app.domain.entities.assessment_session import AssessmentSession, SessionStatus
from app.domain.entities.question import Question
from app.domain.entities.questionnaire_template import QuestionnaireTemplate
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
from app.infrastructure.persistence.repositories.sql_questionnaire_repository import (
    SQLQuestionnaireRepository,
)
from app.modules.questionnaire.branching import BranchingEvaluator
from app.modules.questionnaire.engine import QuestionnaireEngineImpl
from app.modules.questionnaire.scoring import ScoringEngine
from app.modules.questionnaire.validation import ValidationEngine


class QuestionnaireService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._session_repo = SQLAssessmentSessionRepository(session)
        self._question_repo = SQLQuestionRepository(session)
        self._option_repo = SQLQuestionOptionRepository(session)
        self._group_repo = SQLQuestionGroupRepository(session)
        self._template_repo = SQLQuestionnaireRepository(session)
        self._engine = QuestionnaireEngineImpl(session)
        self._scoring = ScoringEngine()
        self._validation = ValidationEngine()
        self._branching = BranchingEvaluator()

    async def get_available_templates(
        self, _user: Any, audience: str | None = None
    ) -> list[QuestionnaireTemplate]:
        if audience:
            return await self._template_repo.find_by_target_audience(audience)
        return await self._template_repo.find_all_active()

    async def start_session(
        self, user: Any, template_id: str | None = None
    ) -> dict[str, Any]:
        template = None
        total_questions = 0
        version_id = None

        if template_id:
            template = await self._template_repo.find_by_id(template_id)
            if not template:
                raise NotFoundError(detail=f"Template {template_id} not found")
            questions = await self._question_repo.find_by_questionnaire(template_id)
            total_questions = len(questions)

            versions = await self._template_repo.find_version(
                template_id, template.version
            )
            if versions:
                version_id = versions.id

        session = AssessmentSession.create(
            user_id=user.id if hasattr(user, "id") else str(user),
            questionnaire_template_id=template_id,
            questionnaire_version_id=version_id,
            total_questions=total_questions,
        )

        created = await self._session_repo.create(session)

        # Find first question
        questions = await self._engine.load_questions(created)
        first_question = questions[0] if questions else None

        if first_question:
            created.current_question_id = first_question.id
            created.current_group_id = first_question.question_group_id
            await self._session_repo.update(created)

        # Get options for first question
        options = []
        if first_question:
            options = await self._option_repo.find_by_question(first_question.id)

        return {
            "session_id": created.id,
            "status": created.status.value,
            "current_question": (
                self._serialize_question(first_question, options)
                if first_question
                else None
            ),
        }

    async def get_session(self, user: Any, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")

        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")

        question = None
        options = []
        if session.current_question_id:
            q = await self._question_repo.find_by_id(session.current_question_id)
            if q:
                options = await self._option_repo.find_by_question(q.id)
                question = self._serialize_question(q, options)

        progress = await self._engine.calculate_progress(session)

        return {
            "id": session.id,
            "status": session.status.value,
            "current_question": question,
            "progress": progress.to_dict() if progress else None,
            "started_at": (
                session.started_at.isoformat() if session.started_at else None
            ),
            "completed_at": (
                session.completed_at.isoformat() if session.completed_at else None
            ),
        }

    async def save_answer(
        self, user: Any, session_id: str, answer_data: dict[str, Any]
    ) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")

        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")

        if session.status != SessionStatus.ACTIVE:
            raise ValidationError(detail="Session is not active")

        question_id = answer_data.get("question_id", "")
        response_value = answer_data.get("response_value", {})
        time_taken = answer_data.get("time_taken_seconds", 0)
        is_skipped = answer_data.get("is_skipped", False)

        question = await self._question_repo.find_by_id(question_id)
        if not question:
            raise NotFoundError(detail=f"Question {question_id} not found")

        # Validate
        if not is_skipped:
            errors = await self._validation.validate(question, response_value)
            if errors:
                raise ValidationError(detail="; ".join(errors))

        # Calculate score
        score_value = 0.0
        if not is_skipped:
            option_value = response_value.get("value")
            if option_value:
                options = await self._option_repo.find_by_question(question_id)
                for opt in options:
                    if opt.value == str(option_value) or opt.code == str(option_value):
                        score_value = opt.score_value
                        break

        answer = AssessmentAnswer.create(
            session_id=session_id,
            question_id=question_id,
            question_code=question.code,
            question_version=question.version,
            response_value=response_value,
            score_value=score_value,
            is_skipped=is_skipped,
            time_taken_seconds=time_taken,
        )

        # Save answer to DB
        from app.infrastructure.persistence.models.assessment_answer import (
            AssessmentAnswerModel,
        )
        from app.infrastructure.persistence.models.assessment_session import (
            AssessmentSessionModel,
        )

        model = AssessmentAnswerModel(
            id=answer.id,
            session_id=answer.session_id,
            question_id=answer.question_id,
            question_version=answer.question_version,
            question_code=answer.question_code,
            response_value=answer.response_value,
            score_value=answer.score_value,
            is_skipped=answer.is_skipped,
            time_taken_seconds=answer.time_taken_seconds,
            branch_path=answer.branch_path,
        )
        self._session.add(model)

        session.answers_count += 1
        session.completed_questions += 1
        await self._session_repo.update(session)

        # Get next question
        next_q = await self._evaluate_next(session)
        next_question_data = None
        if next_q:
            opts = await self._option_repo.find_by_question(next_q.id)
            next_question_data = self._serialize_question(next_q, opts)

            await self._session.execute(
                sql_update(AssessmentSessionModel)
                .where(AssessmentSessionModel.id == session_id)
                .values(current_question_id=next_q.id)
            )

        return {
            "answer": answer.to_dict(),
            "next_question": next_question_data,
        }

    async def get_current_question(self, session: AssessmentSession) -> Question | None:
        if session.current_question_id:
            return await self._question_repo.find_by_id(session.current_question_id)
        return None

    async def _evaluate_next(self, session: AssessmentSession) -> Question | None:
        current_q = None
        if session.current_question_id:
            current_q = await self._question_repo.find_by_id(
                session.current_question_id
            )
        return await self._engine.get_next_question(session, current_q)

    async def pause_session(self, user: Any, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")
        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")
        session.pause()
        await self._session_repo.update(session)
        return {
            "session_id": session.id,
            "status": session.status.value,
            "message": "Session paused",
        }

    async def resume_session(self, user: Any, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")
        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")
        session.resume()
        await self._session_repo.update(session)

        question = None
        if session.current_question_id:
            q = await self._question_repo.find_by_id(session.current_question_id)
            if q:
                opts = await self._option_repo.find_by_question(q.id)
                question = self._serialize_question(q, opts)

        return {
            "session_id": session.id,
            "status": session.status.value,
            "current_question": question,
            "message": "Session resumed",
        }

    async def complete_session(self, user: Any, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")
        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")
        session.complete()
        await self._session_repo.update(session)

        score_summary = await self._calculate_scores(session)

        return {
            "session_id": session.id,
            "status": session.status.value,
            "message": "Assessment completed successfully",
            "score_summary": score_summary,
        }

    async def get_session_progress(self, user: Any, session_id: str) -> dict[str, Any]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError(detail="Session not found")
        user_id = user.id if hasattr(user, "id") else str(user)
        if session.user_id != user_id:
            raise ValidationError(detail="Session does not belong to this user")
        progress = await self._engine.calculate_progress(session)
        return progress.to_dict()

    async def get_session_history(self, user: Any) -> list[dict[str, Any]]:
        user_id = user.id if hasattr(user, "id") else str(user)
        sessions = await self._session_repo.find_by_user(user_id)
        return [s.to_dict() for s in sessions]

    async def search_questions(self, _user: Any, query: str) -> list[dict[str, Any]]:
        questions = await self._question_repo.search(query)
        result = []
        for q in questions:
            opts = await self._option_repo.find_by_question(q.id)
            result.append(self._serialize_question(q, opts))
        return result

    async def _calculate_scores(self, session: AssessmentSession) -> dict[str, Any]:
        from app.infrastructure.persistence.models.assessment_answer import (
            AssessmentAnswerModel,
        )

        rows = await self._session.execute(
            select(AssessmentAnswerModel).where(
                AssessmentAnswerModel.session_id == session.id
            )
        )
        answer_models = rows.scalars().all()
        answers_data = []
        for a in answer_models:
            d = {
                "question_id": a.question_id,
                "score_value": a.score_value or 0.0,
            }
            answers_data.append(d)

        from app.infrastructure.persistence.models.question import QuestionModel

        q_ids = list({a["question_id"] for a in answers_data})
        if q_ids:
            q_rows = await self._session.execute(
                select(QuestionModel).where(QuestionModel.id.in_(q_ids))
            )
            q_map = {q.id: q for q in q_rows.scalars().all()}
        else:
            q_map = {}

        group_scores: dict[str, dict[str, Any]] = {}
        for ans in answers_data:
            q = q_map.get(ans["question_id"])
            if q:
                gid = q.question_group_id
                if gid not in group_scores:
                    group_scores[gid] = {"answers": []}
                group_scores[gid]["answers"].append(ans)

        scored_groups = {}
        for gid, data in group_scores.items():
            scored_groups[gid] = self._scoring.calculate_group_score(
                data["answers"], {}
            )

        overall = self._scoring.calculate_overall_score(scored_groups)
        return overall

    def _serialize_question(
        self, question: Question, options: list[Any]
    ) -> dict[str, Any]:
        return {
            "id": question.id,
            "code": question.code,
            "text": question.text,
            "question_type": (
                question.question_type.value
                if hasattr(question.question_type, "value")
                else question.question_type
            ),
            "description": question.description,
            "tooltip": question.tooltip,
            "is_required": question.is_required,
            "validation_rules": question.validation_rules,
            "priority": question.priority,
            "difficulty": (
                question.difficulty.value
                if hasattr(question.difficulty, "value")
                else question.difficulty
            ),
            "options": [
                {
                    "id": o.id,
                    "code": o.code,
                    "text": o.text,
                    "value": o.value,
                    "score_value": o.score_value,
                    "severity": o.severity,
                    "color_hex": o.color_hex,
                    "display_order": o.display_order,
                }
                for o in options
            ],
        }
