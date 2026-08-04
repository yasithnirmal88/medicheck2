from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)


class SQLAssessmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: str,
        template_id: str | None = None,
        questionnaire_version_id: str | None = None,
    ) -> AssessmentSessionModel:
        stmt = insert(AssessmentSessionModel).values(
            user_id=user_id,
            template_id=template_id,
            questionnaire_version_id=questionnaire_version_id,
            status="started",
        )
        await self.session.execute(stmt)
        await self.session.commit()
        q = (
            select(AssessmentSessionModel)
            .where(AssessmentSessionModel.user_id == user_id)
            .order_by(AssessmentSessionModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def get_session(self, session_id: str) -> AssessmentSessionModel | None:
        q = select(AssessmentSessionModel).where(
            AssessmentSessionModel.id == session_id
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def get_latest_session_for_user(
        self, user_id: str
    ) -> AssessmentSessionModel | None:
        q = (
            select(AssessmentSessionModel)
            .where(AssessmentSessionModel.user_id == user_id)
            .order_by(AssessmentSessionModel.created_at.desc())
        )
        r = await self.session.execute(q)
        return r.scalars().first()

    async def save_answer(
        self,
        session_id: str,
        question_id: str,
        option_id: str | None,
        value: str | None,
        numeric_value: float | None = None,
    ) -> AssessmentAnswerModel:
        # upsert: try to find existing
        q = select(AssessmentAnswerModel).where(
            AssessmentAnswerModel.session_id == session_id,
            AssessmentAnswerModel.question_id == question_id,
        )
        r = await self.session.execute(q)
        existing = r.scalars().first()
        if existing:
            upd = (
                update(AssessmentAnswerModel)
                .where(AssessmentAnswerModel.id == existing.id)
                .values(
                    option_id=option_id,
                    value=value,
                    numeric_value=numeric_value,
                    recorded_at=datetime.now(timezone.utc),
                )
            )
            await self.session.execute(upd)
            await self.session.commit()
            q2 = select(AssessmentAnswerModel).where(
                AssessmentAnswerModel.id == existing.id
            )
            r2 = await self.session.execute(q2)
            return r2.scalars().first()
        ins = insert(AssessmentAnswerModel).values(
            session_id=session_id,
            question_id=question_id,
            option_id=option_id,
            value=value,
            numeric_value=numeric_value,
            recorded_at=datetime.now(timezone.utc),
        )
        await self.session.execute(ins)
        await self.session.commit()
        q3 = select(AssessmentAnswerModel).where(
            AssessmentAnswerModel.session_id == session_id,
            AssessmentAnswerModel.question_id == question_id,
        )
        r3 = await self.session.execute(q3)
        return r3.scalars().first()

    async def list_answers_for_session(
        self, session_id: str
    ) -> list[AssessmentAnswerModel]:
        q = (
            select(AssessmentAnswerModel)
            .where(AssessmentAnswerModel.session_id == session_id)
            .order_by(AssessmentAnswerModel.created_at.asc())
        )
        r = await self.session.execute(q)
        return r.scalars().all()

    async def set_session_state(self, session_id: str, **kwargs) -> None:
        stmt = (
            update(AssessmentSessionModel)
            .where(AssessmentSessionModel.id == session_id)
            .values(**kwargs)
        )
        await self.session.execute(stmt)
        await self.session.commit()
