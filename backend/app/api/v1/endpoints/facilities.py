"""Phase 10 — Facility API: operational metadata.

Read access open to referral users (they need to see facilities to route
referrals). Create/manage requires INTEROP_MANAGE (admin). No clinical
content; no patient data.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.application.dtos.referral_dtos import (
    FacilityCreateRequest,
    FacilityListResponse,
    FacilityResponse,
)
from app.application.services.facility_service import FacilityService
from app.identity import (
    User,
    get_current_user,
    get_interop_user,
    get_referral_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/facilities", tags=["Facilities (Phase 10)"])


@router.get(
    "",
    response_model=FacilityListResponse,
    summary="List facilities (operational metadata)",
)
async def list_facilities(
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FacilityService(session)
    return await svc.list_facilities()


@router.get(
    "/{facility_id}",
    response_model=FacilityResponse,
    summary="Get a facility",
)
async def get_facility(
    facility_id: str,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FacilityService(session)
    return await svc.get_facility(facility_id)


@router.post(
    "",
    response_model=FacilityResponse,
    summary="Create a facility (admin)",
)
async def create_facility(
    req: FacilityCreateRequest,
    user: Annotated[User, Depends(get_interop_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FacilityService(session)
    result = await svc.create_facility(req)
    await session.commit()
    return result
