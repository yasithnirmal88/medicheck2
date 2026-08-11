"""Phase 7 — AI governance API.

Exposes aggregate AI quality/operational metrics to CMS-authorized users
(RESEARCH_REVIEWER+). Returns de-identified counts only — no session_id,
trace_id, or patient-identifying data. Individual AI audit records are never
exposed through this API.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ai_governance_user, get_db
from app.application.services.ai_audit_service import AIAuditService
from app.domain.entities.user import User

router = APIRouter(prefix="/ai-governance", tags=["ai-governance"])


@router.get("/summary")
async def get_governance_summary(
    current_user: User = Depends(get_ai_governance_user),
    session: AsyncSession = Depends(get_db),
):
    """Aggregate AI quality metrics for the governance dashboard.

    Returns: total requests, successful explanations, fallback rate,
    validation failure rate, provider breakdown, language distribution,
    prompt version distribution. All de-identified.
    """
    svc = AIAuditService(session)
    return await svc.get_governance_summary()
