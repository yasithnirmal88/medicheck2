"""Phase 3 — AI clinical-intake endpoint.

POST /api/v1/ai/intake/extract

Authentication: existing ``get_current_user`` dependency (RBAC preserved; no
CMS permissions required for patient intake). Session ownership is verified:
if a ``session_id`` is supplied it must belong to the authenticated user. The
intake is scoped to the caller — no cross-patient intake.

The endpoint never modifies the deterministic pipeline. The intake response is
session-scoped; AI output is validated against the authoritative knowledge
graph before it can influence question selection. On any failure, a safe
fallback (``available=false``) is returned so the standard questionnaire keeps
working.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.dtos.intake_dtos import IntakeResponse
from app.application.services.ai_intake_service import AIIntakeService
from app.infrastructure.database import get_db
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)

router = APIRouter(prefix="/ai/intake", tags=["ai-intake"])


class IntakeExtractRequest(BaseModel):
    """Request body for AI intake extraction.

    ``session_id`` is optional: it ties the intake to an existing assessment
    session (ownership verified). When omitted, a pseudonymous reference is
    derived from the authenticated user so the intake is still scoped.
    """

    session_id: str | None = Field(default=None, description="existing assessment session id")
    text: str = Field(..., min_length=1, description="patient free-text description")


@router.post("/extract", response_model=IntakeResponse)
async def extract_intake(
    payload: IntakeExtractRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> IntakeResponse:
    user_id = current_user.id
    session_ref = payload.session_id or f"u:{user_id}"

    # If a session id is supplied, verify it exists AND belongs to the caller.
    if payload.session_id:
        from sqlalchemy import select

        stmt = select(AssessmentSessionModel).where(
            AssessmentSessionModel.id == payload.session_id
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            # Unknown session → 404 (never leak existence to other users).
            raise HTTPException(status_code=404, detail="Session not found")
        if row.user_id != user_id:
            # Cross-patient attempt → 404 (do not reveal ownership to the caller).
            raise HTTPException(status_code=404, detail="Session not found")

    svc = AIIntakeService(session)
    try:
        return await svc.extract(payload.text, session_ref=session_ref)
    except Exception as exc:  # pragma: no cover - defensive
        # Any unexpected service error → safe fallback, never a 500 that breaks
        # the intake UX. The standard questionnaire remains available.
        from app.application.dtos.intake_dtos import safe_intake_response
        from app.application.ai.intake_prompts import INTAKE_PROMPT_VERSION
        from app.core.logging import get_logger

        get_logger(__name__).warning("intake endpoint fallback: %s", exc)
        return safe_intake_response(new_trace_id_stub(), INTAKE_PROMPT_VERSION)


def new_trace_id_stub() -> str:
    from app.application.dtos.intake_dtos import new_trace_id

    return new_trace_id()
