from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.dtos.profile_dtos import HealthProfileDTO, PersonalInfoDTO
from app.application.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=HealthProfileDTO)
async def get_my_profile(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> HealthProfileDTO:
    svc = ProfileService(session)
    profile = await svc.get_or_create_profile_for_user(current_user)
    return profile


@router.post("/me/personal", response_model=HealthProfileDTO)
async def update_personal_info(
    payload: PersonalInfoDTO,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> HealthProfileDTO:
    svc = ProfileService(session)
    try:
        updated = await svc.update_personal_info(current_user, payload)
        return updated
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/me/versions")
async def list_my_versions(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    profile = await svc.get_or_create_profile_for_user(current_user)
    versions = await svc.repo.list_versions(profile.id)
    return [v.snapshot for v in versions]
