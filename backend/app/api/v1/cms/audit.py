from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.audit_service import CMSAuditService
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/audit", tags=["CMS Audit & Compliance"])


@router.get("/logs")
async def search_audit_logs(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    actor_id: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    action: str | None = Query(None),
    query: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    svc = CMSAuditService(session)
    return await svc.search(
        actor_id=actor_id, entity_type=entity_type,
        entity_id=entity_id, action=action,
        query=query, skip=skip, limit=limit,
    )


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_audit_timeline(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = CMSAuditService(session)
    return await svc.get_timeline(entity_type, entity_id)


@router.get("/diffs/{entity_type}/{entity_id}")
async def get_audit_diffs(
    entity_type: str,
    entity_id: str,
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = CMSAuditService(session)
    return await svc.get_diffs(entity_type, entity_id)


@router.get("/export")
async def export_audit(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str | None = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    svc = CMSAuditService(session)
    result = await svc.export(entity_type=entity_type, format=format)
    if format == "csv":
        return PlainTextResponse(
            content=result, media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
        )
    return result


@router.get("/stats")
async def get_audit_stats(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    svc = CMSAuditService(session)
    return await svc.get_stats(days=days)
