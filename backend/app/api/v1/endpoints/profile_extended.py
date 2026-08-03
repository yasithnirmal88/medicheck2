from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.application.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me/completion")
async def get_completion(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.compute_completion(current_user)


@router.get("/me/versions/{version}")
async def preview_version(
    version: int = Path(..., gt=0),
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    snapshot = await svc.get_version_snapshot(current_user, version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snapshot


@router.post("/me/versions/{version}/restore")
async def restore_version(
    version: int = Path(..., gt=0),
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    try:
        result = await svc.restore_version(current_user, version)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Section endpoints (lifestyle, nutrition)
@router.post("/me/lifestyle")
async def save_lifestyle(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.update_lifestyle(current_user, payload)


@router.post("/me/nutrition")
async def save_nutrition(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.update_nutrition(current_user, payload)


# repeatable sections: add/list
@router.post("/me/medical")
async def add_medical(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_medical_history(current_user, payload)


@router.get("/me/medical")
async def list_medical(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_medical_history(current_user)


@router.post("/me/medications")
async def add_medication(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_medication(current_user, payload)


@router.get("/me/medications")
async def list_medications(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_medications(current_user)


@router.post("/me/surgeries")
async def add_surgery(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_surgery(current_user, payload)


@router.get("/me/surgeries")
async def list_surgeries(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_surgeries(current_user)


@router.post("/me/family")
async def add_family(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_family_history(current_user, payload)


@router.get("/me/family")
async def list_family(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_family_histories(current_user)


@router.post("/me/allergies")
async def add_allergy(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_allergy(current_user, payload)


@router.get("/me/allergies")
async def list_allergies(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_allergies(current_user)


@router.post("/me/immunizations")
async def add_immunization(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_immunization(current_user, payload)


@router.get("/me/immunizations")
async def list_immunizations(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_immunizations(current_user)


@router.post("/me/measurements")
async def add_measurement(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_measurement(current_user, payload)


@router.get("/me/measurements")
async def list_measurements(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_measurements(current_user)


@router.post("/me/lab-reports")
async def add_lab_report(
    payload: dict,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.add_lab_report(current_user, payload)


@router.get("/me/lab-reports")
async def list_lab_reports(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ProfileService(session)
    return await svc.list_lab_reports(current_user)
