from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.application.dtos.ai_dtos import AIExplanationResponse
from app.application.services.ai_explanation_service import AIExplanationService
from app.application.services.report_service import ReportService
from app.core.cache import CacheService

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate")
async def generate_report(
    payload: dict = Body(...),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    svc = ReportService(session)
    try:
        res = await svc.generate_report(session_id, current_user.id)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{session_id}")
async def get_report_by_session(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = ReportService(session, CacheService(redis))
    rpt = await svc.get_report_by_session(session_id, user_id=current_user.id)
    if not rpt:
        raise HTTPException(status_code=404, detail="report not found")
    return rpt


@router.get("/id/{report_id}")
async def get_report(
    report_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = ReportService(session, CacheService(redis))
    rpt = await svc.get_report(report_id, user_id=current_user.id)
    if not rpt:
        raise HTTPException(status_code=404, detail="report not found")
    return rpt


@router.get("/")
async def list_reports(
    limit: int = 100,
    offset: int = 0,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ReportService(session)
    reports = await svc.list_reports(current_user.id, limit=limit, offset=offset)
    return reports


@router.get("/compare/{id1}/{id2}")
async def compare_reports(
    id1: str,
    id2: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    svc = ReportService(session, CacheService(redis))
    try:
        res = await svc.compare_reports(id1, id2, user_id=current_user.id)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{session_id}/explanation", response_model=AIExplanationResponse)
async def get_report_explanation(
    session_id: str,
    language: str = "en",
    literacy_level: str = "standard",
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """AI-assisted explanation of an already-generated deterministic report.

    The deterministic report is never modified or recalculated. The AI only
    explains the existing result. If the AI provider is unavailable or returns
    an invalid response, a safe fallback (``available=False``) is returned so
    the clinical report is never broken. Authentication + ownership use the
    same dependency/access checks as the other report endpoints.

    Phase 7: ``language`` (en/si/ta) and ``literacy_level``
    (simple/standard/detailed) personalize the communication. The
    deterministic result is identical at every level.
    """
    svc = AIExplanationService(session)
    try:
        return await svc.explain_report(
            session_id,
            current_user.id,
            language=language,
            literacy_level=literacy_level,
        )
    except ValueError as exc:
        # No report owned by this user for this session.
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{session_id}/question-explanation")
async def get_question_explanation(
    session_id: str,
    question_id: str,
    language: str = "en",
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Phase 7 — Explain why a question was asked in an assessment.

    Uses ONLY existing knowledge-graph relationships (question → indicator →
    condition, question → evidence). The AI does NOT invent medical
    relationships. Ownership: the caller must own the session.
    """
    from app.application.services.question_explanation_service import (
        QuestionExplanationService,
    )

    svc = QuestionExplanationService(session)
    try:
        return await svc.explain_question(
            session_id=session_id,
            question_id=question_id,
            user_id=current_user.id,
            language=language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
