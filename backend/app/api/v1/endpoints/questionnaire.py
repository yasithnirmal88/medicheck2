from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.services.questionnaire_service import QuestionnaireService
from app.domain.entities.user import User

router = APIRouter(prefix="/questionnaire", tags=["questionnaire"])


@router.post("/start")
async def start_assessment(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    template_id: str | None = Body(None),
):
    svc = QuestionnaireService(session)
    s = await svc.start_session(current_user, template_id)
    return s


@router.get("/resume/{session_id}")
async def resume_assessment(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    try:
        return await svc.resume_session(current_user, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/answer")
async def save_answer(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: dict = Body(...),
):
    svc = QuestionnaireService(session)
    sid = payload.get("session_id")
    if not sid:
        raise HTTPException(status_code=400, detail="session_id required")
    answer_data = {
        "question_id": payload.get("question_id"),
        "response_value": {"value": payload.get("value") or payload.get("option_id")},
        "time_taken_seconds": payload.get("time_taken_seconds", 0),
        "is_skipped": payload.get("is_skipped", False),
    }
    return await svc.save_answer(current_user, sid, answer_data)


@router.get("/next/{session_id}")
async def next_question(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    try:
        session_data = await svc.get_session(current_user, session_id)
        return {"next": session_data.get("current_question")}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/progress/{session_id}")
async def progress(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    try:
        return await svc.get_session_progress(current_user, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/search")
async def search(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    q: str = Body(""),
):
    svc = QuestionnaireService(session)
    return await svc.search_questions(current_user, q)
