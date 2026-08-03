from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.services.questionnaire_service import QuestionnaireService
from app.domain.entities.user import User

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/sessions/{id}/result")
async def get_session_result(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    return await svc.get_session(current_user, id)
