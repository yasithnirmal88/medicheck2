from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.dtos.questionnaire_dtos import (
    AssessmentSessionResponse,
    QuestionnaireTemplateResponse,
    SaveAnswerRequest,
    SaveAnswerResponse,
    SessionProgressResponse,
    StartSessionResponse,
    SubmitSessionResponse,
)
from app.application.services.questionnaire_service import QuestionnaireService
from app.domain.entities.user import User

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])


@router.get("", summary="List questionnaire templates", description="List available questionnaire templates for the current user. Optionally filter by target audience.", response_model=list[QuestionnaireTemplateResponse])
async def list_templates(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    audience: str | None = Query(None),
):
    svc = QuestionnaireService(session)
    templates = await svc.get_available_templates(current_user, audience=audience)
    return [QuestionnaireTemplateResponse.from_attributes(t) for t in templates]


# Static /sessions routes MUST be declared before the /{id} parametric route,
# otherwise FastAPI matches "/sessions" against "/{id}" (id="sessions") and
# returns a 404 "Template not found".
@router.get("/sessions", response_model=list[AssessmentSessionResponse], summary="List user questionnaire sessions", description="List past assessment sessions for the authenticated user.")
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    sessions = await svc.get_session_history(current_user)
    # map dicts to DTOs
    return [AssessmentSessionResponse(**s) for s in sessions]


@router.get("/sessions/{id}", response_model=AssessmentSessionResponse, summary="Get a session", description="Retrieve the current state and progress of a questionnaire session belonging to the authenticated user.")
async def get_session(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    res = await svc.get_session(current_user, id)
    return AssessmentSessionResponse(**res)


@router.post("/sessions/{id}/answer", response_model=SaveAnswerResponse, summary="Save an answer", description="Save an answer for the current session and return the saved answer and the next question (if any).")
async def save_answer(
    id: str,
    payload: SaveAnswerRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    res = await svc.save_answer(current_user, id, payload.model_dump())
    return SaveAnswerResponse(**res)


@router.post("/sessions/{id}/pause", response_model=SubmitSessionResponse, summary="Pause a session", description="Pause an in-progress questionnaire session.")
async def pause_session(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    res = await svc.pause_session(current_user, id)
    return SubmitSessionResponse(**res)


@router.post("/sessions/{id}/resume", response_model=SubmitSessionResponse, summary="Resume a session", description="Resume a paused questionnaire session.")
async def resume_session(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    res = await svc.resume_session(current_user, id)
    return SubmitSessionResponse(**res)


@router.post("/sessions/{id}/complete", response_model=SubmitSessionResponse, summary="Complete a session", description="Mark a questionnaire session as complete and trigger downstream processing.")
async def complete_session(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    res = await svc.complete_session(current_user, id)
    return SubmitSessionResponse(**res)


@router.get("/sessions/{id}/progress", response_model=SessionProgressResponse)
async def get_session_progress(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    return await svc.get_session_progress(current_user, id)


# Parametric /{id} routes declared LAST so they cannot shadow the static
# /sessions routes above.
@router.get("/{id}", summary="Get questionnaire template detail", response_model=QuestionnaireTemplateResponse)
async def get_template_detail(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    from app.infrastructure.persistence.repositories.sql_questionnaire_repository import (
        SQLQuestionnaireRepository,
    )
    repo = SQLQuestionnaireRepository(session)
    template = await repo.find_by_id(id)
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")
    return QuestionnaireTemplateResponse.from_attributes(template)


@router.post("/{id}/start", response_model=StartSessionResponse, summary="Start a questionnaire session", description="Start a questionnaire session for the authenticated user using the given template id.")
async def start_session(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = QuestionnaireService(session)
    result = await svc.start_session(current_user, template_id=id)
    return StartSessionResponse(**result)
