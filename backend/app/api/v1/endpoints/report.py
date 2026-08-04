from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
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
