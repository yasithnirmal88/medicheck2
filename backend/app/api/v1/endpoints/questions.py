from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.dtos.questionnaire_dtos import QuestionResponse
from app.domain.entities.user import User
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("", response_model=list[QuestionResponse])
async def list_questions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    body_system: str | None = Query(None),
    group: str | None = Query(None),
):
    repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)

    if group:
        questions = await repo.find_by_group(group)
    elif body_system:
        questions = await repo.find_by_body_system(body_system)
    else:
        questions = await repo.find_active()

    result = []
    for q in questions:
        opts = await opt_repo.find_by_question(q.id)
        result.append(QuestionResponse.from_entity(q, opts))
    return result


@router.get("/{id}", response_model=QuestionResponse)
async def get_question_detail(
    id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)
    q = await repo.find_by_id(id)
    if not q:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Question not found")
    opts = await opt_repo.find_by_question(q.id)
    return QuestionResponse.from_entity(q, opts)


@router.get("/by-body-system/{code}", response_model=list[QuestionResponse])
async def get_questions_by_body_system(
    code: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)

    from app.infrastructure.persistence.repositories.sql_body_system_repository import (
        SQLBodySystemRepository,
    )

    bs_repo = SQLBodySystemRepository(session)
    body_sys = await bs_repo.find_by_code(code)
    if not body_sys:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Body system not found")

    questions = await repo.find_by_body_system(body_sys.id)
    result = []
    for q in questions:
        opts = await opt_repo.find_by_question(q.id)
        result.append(QuestionResponse.from_entity(q, opts))
    return result


@router.get("/search", response_model=list[QuestionResponse])
async def search_questions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(""),
):
    svc = __import__(
        "app.application.services.questionnaire_service",
        fromlist=["QuestionnaireService"],
    ).QuestionnaireService(session)
    return await svc.search_questions(current_user, q)
