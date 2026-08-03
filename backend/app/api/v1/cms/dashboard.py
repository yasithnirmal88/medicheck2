from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cms_user, get_db
from app.application.services.cms.dashboard_service import CMSDashboardService
from app.domain.entities.user import User

router = APIRouter(prefix="/cms/dashboard", tags=["CMS Dashboard"])


@router.get("/overview")
async def get_overview(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = CMSDashboardService(session)
    return await svc.get_overview()


@router.get("/recent-activity")
async def get_recent_activity(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    svc = CMSDashboardService(session)
    return await svc.get_recent_activity(limit)


@router.get("/workflow-summary")
async def get_workflow_summary(
    user: Annotated[User, Depends(get_cms_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = CMSDashboardService(session)
    return await svc.get_workflow_summary()
