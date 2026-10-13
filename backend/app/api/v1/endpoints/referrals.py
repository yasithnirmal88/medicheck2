"""Phase 10 — Referral API: CRUD, status lifecycle, facility feedback, outcomes.

RBAC + IDOR-guarded (patient own, CHW assigned, clinician/admin manage).
Every status transition is server-validated (deterministic state machine) and
audited. Facility feedback is operational only (no clinical notes). Care
outcomes are operational states that NEVER modify CDSE scoring.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.application.dtos.referral_dtos import (
    AcknowledgeRequest,
    BarrierRequest,
    CareOutcomeRequest,
    CompleteTaskRequest,
    CreateReferralRequest,
    FacilityFeedbackRequest,
    ReferralDetailResponse,
    ReferralListResponse,
    ReferralResponse,
    ScheduleRequest,
    StatusUpdateRequest,
)
from app.application.services.referral_service import ReferralService
from app.identity import User, get_current_user, get_referral_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/referrals", tags=["Referrals (Phase 9/10)"])


@router.post(
    "",
    response_model=ReferralResponse,
    summary="Create a referral from an existing CDSE recommendation",
)
async def create_referral(
    req: CreateReferralRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.create_referral(user, req)
    await session.commit()
    return result


@router.get(
    "",
    response_model=ReferralListResponse,
    summary="List referrals (caller-scoped)",
)
async def list_referrals(
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    patient_user_id: str | None = None,
):
    svc = ReferralService(session)
    return await svc.list_referrals(user, patient_user_id=patient_user_id)


@router.get(
    "/{referral_id}",
    response_model=ReferralDetailResponse,
    summary="Get referral detail (with status events, barriers, tasks)",
)
async def get_referral(
    referral_id: str,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    return await svc.get_referral(user, referral_id)


@router.post(
    "/{referral_id}/acknowledge",
    response_model=ReferralResponse,
    summary="Patient acknowledges a referral",
)
async def acknowledge_referral(
    referral_id: str,
    req: AcknowledgeRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.acknowledge(user, referral_id, req)
    await session.commit()
    return result


@router.post(
    "/{referral_id}/schedule",
    response_model=ReferralResponse,
    summary="Schedule a referral appointment",
)
async def schedule_referral(
    referral_id: str,
    req: ScheduleRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.schedule(user, referral_id, req)
    await session.commit()
    return result


@router.post(
    "/{referral_id}/status",
    response_model=ReferralResponse,
    summary="Update referral status (server-validated transition)",
)
async def update_referral_status(
    referral_id: str,
    req: StatusUpdateRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.update_status(user, referral_id, req)
    await session.commit()
    return result


@router.post(
    "/{referral_id}/feedback",
    response_model=ReferralResponse,
    summary="Record receiving-side facility feedback (operational, no clinical notes)",
)
async def record_facility_feedback(
    referral_id: str,
    req: FacilityFeedbackRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.record_facility_feedback(user, referral_id, req)
    await session.commit()
    return result


@router.post(
    "/{referral_id}/barriers",
    summary="Record a non-clinical access barrier",
)
async def record_barrier(
    referral_id: str,
    req: BarrierRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.record_barrier(user, referral_id, req)
    await session.commit()
    return result


@router.post(
    "/{referral_id}/outcomes",
    summary="Record a care-continuity outcome (operational; never modifies CDSE)",
)
async def record_outcome(
    referral_id: str,
    req: CareOutcomeRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.record_outcome(user, referral_id, req)
    await session.commit()
    return result


@router.get(
    "/{referral_id}/outcomes",
    summary="List care outcomes for a referral",
)
async def list_outcomes(
    referral_id: str,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    return await svc.list_outcomes(user, referral_id)


@router.get(
    "/{referral_id}/tasks",
    summary="List follow-up tasks for a referral",
)
async def list_follow_up_tasks(
    referral_id: str,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    return await svc.list_follow_up_tasks(user, referral_id)


@router.post(
    "/{referral_id}/tasks/{task_id}/complete",
    summary="Complete a follow-up task",
)
async def complete_follow_up_task(
    referral_id: str,
    task_id: str,
    req: CompleteTaskRequest,
    user: Annotated[User, Depends(get_referral_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ReferralService(session)
    result = await svc.complete_task(user, referral_id, task_id, req)
    await session.commit()
    return result
