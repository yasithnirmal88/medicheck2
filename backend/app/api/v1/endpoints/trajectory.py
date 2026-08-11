"""Phase 4 — Longitudinal trajectory API.

Endpoints (all enforce ``get_current_user`` + ownership; trajectory is scoped to
the caller — no cross-user access):

- ``GET /api/v1/trajectory`` — deterministic trajectory (latest N, bounded).
- ``GET /api/v1/trajectory/compare/{previous_session_id}/{current_session_id}``
  — deterministic comparison of two specific owned assessments.
- ``POST /api/v1/trajectory/explanation`` — AI explanation of the trajectory.
  Body: ``{"previous_session_id": "...", "current_session_id": "..."}`` (both
  optional; defaults to the latest two completed assessments).

The deterministic trajectory is always returned even when the AI is
unavailable. AI failure never breaks the trajectory.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.application.dtos.longitudinal_dtos import (
    HealthTrajectory,
    LongitudinalExplanationResponse,
    TrajectoryComparison,
)
from app.application.services.longitudinal_analysis_service import (
    LongitudinalAnalysisService,
)
from app.application.services.longitudinal_explanation_service import (
    LongitudinalExplanationService,
)

router = APIRouter(prefix="/trajectory", tags=["trajectory"])


class ExplanationRequest(BaseModel):
    previous_session_id: str | None = None
    current_session_id: str | None = None


@router.get("", response_model=HealthTrajectory)
async def get_trajectory(
    limit: int = 20,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HealthTrajectory:
    svc = LongitudinalAnalysisService(session)
    return await svc.get_trajectory(current_user.id, limit=limit)


@router.get(
    "/compare/{previous_session_id}/{current_session_id}",
    response_model=TrajectoryComparison,
)
async def compare_specific(
    previous_session_id: str,
    current_session_id: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TrajectoryComparison:
    svc = LongitudinalAnalysisService(session)
    res = await svc.compare_specific(
        current_user.id, previous_session_id, current_session_id
    )
    if res is None:
        raise HTTPException(status_code=404, detail="trajectory comparison not found")
    return res


@router.post("/explanation", response_model=LongitudinalExplanationResponse)
async def explain_trajectory(
    payload: ExplanationRequest = Body(default_factory=ExplanationRequest),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LongitudinalExplanationResponse:
    """AI explanation of the caller's deterministic trajectory.

    If both session ids are omitted, the latest two completed assessments are
    explained. With < 2 assessments the AI is NOT called; a safe
    insufficient-data response is returned. The deterministic trajectory
    remains available via ``GET /trajectory`` regardless.
    """
    svc = LongitudinalExplanationService(session)
    return await svc.explain_trajectory(
        current_user.id,
        previous_session_id=payload.previous_session_id,
        current_session_id=payload.current_session_id,
    )
