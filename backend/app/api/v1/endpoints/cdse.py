from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.application.services.clinical_decision_service import ClinicalDecisionService

router = APIRouter(prefix="/assessment", tags=["cdse"])


@router.post("/process")
async def process_assessment(
    payload: dict = Body(...),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    svc = ClinicalDecisionService(session)
    try:
        res = await svc.process_assessment(session_id, current_user.id)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/results/{session_id}")
async def get_result_by_session(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result_by_session(session_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res


@router.get("/result/{result_id}")
async def get_result(
    result_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result(result_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res


@router.get("/{session_id}/explanation")
async def get_explanation(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result_by_session(session_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res.explanations


@router.get("/{session_id}/recommendations")
async def get_recommendations(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result_by_session(session_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res.generated_recommendations


@router.get("/{session_id}/laboratory-tests")
async def get_laboratory_tests(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result_by_session(session_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res.generated_laboratory_tests


@router.get("/{session_id}/screenings")
async def get_screenings(
    session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = ClinicalDecisionService(session)
    res = await svc.get_result_by_session(session_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return res.generated_screenings
