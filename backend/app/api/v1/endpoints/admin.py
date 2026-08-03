from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.application.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/body-systems")
async def create_body_system(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    bs = await svc.create_body_system(current_user.id, payload)
    return bs


@router.get("/body-systems")
async def list_body_systems(
    current_user=Depends(get_current_admin), session: AsyncSession = Depends(get_db)
):
    svc = AdminService(session)
    return await svc.repo.list_body_systems()


@router.post("/indicators")
async def create_indicator(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    ind = await svc.create_indicator(current_user.id, payload)
    return ind


@router.get("/indicators")
async def list_indicators(
    body_system_id: str | None = Query(None),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    return await svc.list_indicators(body_system_id)


@router.post("/evidence")
async def create_evidence(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    ev = await svc.create_evidence(current_user.id, payload)
    return ev


@router.get("/evidence")
async def list_evidence(
    limit: int = Query(50),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    return await svc.list_evidence(limit)


@router.post("/recommendations")
async def create_recommendation(
    payload: dict = Body(...),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    rec = await svc.create_recommendation(current_user.id, payload)
    return rec


@router.get("/recommendations")
async def list_recommendations(
    limit: int = Query(100),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    return await svc.list_recommendations(limit)


@router.get("/audit")
async def audit_logs(
    entity_type: str | None = Query(None),
    limit: int = Query(100),
    current_user=Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
):
    svc = AdminService(session)
    return await svc.list_audit_logs(entity_type, limit)
