from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.assessment_session import AssessmentSession, SessionStatus
from app.domain.repositories.assessment_session_repository import (
    AssessmentSessionRepository,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)


class SQLAssessmentSessionRepository(AssessmentSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: str) -> AssessmentSession | None:
        stmt = select(AssessmentSessionModel).where(AssessmentSessionModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user(self, user_id: str) -> list[AssessmentSession]:
        stmt = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.user_id == user_id,
            )
            .order_by(AssessmentSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_active_by_user(self, user_id: str) -> list[AssessmentSession]:
        stmt = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.user_id == user_id,
                AssessmentSessionModel.status.in_(["active", "paused"]),
            )
            .order_by(AssessmentSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_status(self, status: str) -> list[AssessmentSession]:
        stmt = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.status == status,
            )
            .order_by(AssessmentSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, session: AssessmentSession) -> AssessmentSession:
        model = AssessmentSessionModel(
            id=session.id,
            user_id=session.user_id,
            questionnaire_template_id=session.questionnaire_template_id,
            questionnaire_version_id=session.questionnaire_version_id,
            status=session.status.value,
            current_question_id=session.current_question_id,
            current_group_id=session.current_group_id,
            answers_count=session.answers_count,
            total_questions=session.total_questions,
            completed_questions=session.completed_questions,
            started_at=session.started_at,
            paused_at=session.paused_at,
            completed_at=session.completed_at,
            expires_at=session.expires_at,
            device_info=session.device_info,
            extra_metadata=session.metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return session

    async def update(self, session: AssessmentSession) -> AssessmentSession:
        stmt = select(AssessmentSessionModel).where(
            AssessmentSessionModel.id == session.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"AssessmentSession with id {session.id} not found")

        model.status = session.status.value
        model.current_question_id = session.current_question_id
        model.current_group_id = session.current_group_id
        model.answers_count = session.answers_count
        model.total_questions = session.total_questions
        model.completed_questions = session.completed_questions
        model.started_at = session.started_at
        model.paused_at = session.paused_at
        model.completed_at = session.completed_at
        model.expires_at = session.expires_at
        model.device_info = session.device_info
        model.extra_metadata = session.metadata
        model.updated_at = session.updated_at

        await self._session.flush()
        return session

    async def count_completed_by_user(self, user_id: str) -> int:
        stmt = select(func.count(AssessmentSessionModel.id)).where(
            AssessmentSessionModel.user_id == user_id,
            AssessmentSessionModel.status == "completed",
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    def _to_entity(self, model: AssessmentSessionModel) -> AssessmentSession:
        return AssessmentSession(
            id=model.id,
            user_id=model.user_id,
            questionnaire_template_id=model.questionnaire_template_id,
            questionnaire_version_id=model.questionnaire_version_id,
            status=SessionStatus(model.status),
            current_question_id=model.current_question_id,
            current_group_id=model.current_group_id,
            answers_count=model.answers_count,
            total_questions=model.total_questions,
            completed_questions=model.completed_questions,
            started_at=model.started_at,
            paused_at=model.paused_at,
            completed_at=model.completed_at,
            expires_at=model.expires_at,
            device_info=model.device_info,
            metadata=model.extra_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
