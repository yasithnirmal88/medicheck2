"""Phase 11 — AI care-coordination API (CHW operational suggestions).

Endpoints:
- POST /api/v1/ai-care-coordination/suggestions : generate operational
  suggestions for the caller's CHW queue (operational factors only).
- GET  /api/v1/ai-care-coordination/suggestions : list the caller's persisted
  suggestions (own only — IDOR enforced).

All suggestions are administrative assistance ONLY — they never determine
clinical priority, severity, or urgency. AI never self-publishes; review is a
separate human-driven workflow (see ai_equity_intelligence router).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_chw_operational_user, get_db
from app.application.dtos.ai_governance_dtos import (
    OperationalSuggestionBatchResponse,
    OperationalSuggestionRecord,
)
from app.application.services.ai_operational_suggestion_service import (
    AiOperationalSuggestionService,
)
from app.identity import User

router = APIRouter(
    prefix="/ai-care-coordination", tags=["ai-care-coordination"]
)


@router.post("/suggestions", response_model=OperationalSuggestionBatchResponse)
async def generate_suggestions(
    current_user: User = Depends(get_chw_operational_user),
    session: AsyncSession = Depends(get_db),
) -> OperationalSuggestionBatchResponse:
    """Generate AI operational suggestions for the caller's CHW queue.

    Operational/administrative assistance only — never clinical priority.
    """
    svc = AiOperationalSuggestionService(session)
    return await svc.generate_for_chw(current_user)


@router.get("/suggestions", response_model=list[OperationalSuggestionRecord])
async def list_suggestions(
    limit: int | None = Query(default=None, ge=1, le=200),
    current_user: User = Depends(get_chw_operational_user),
    session: AsyncSession = Depends(get_db),
) -> list[OperationalSuggestionRecord]:
    """List the caller's persisted operational suggestions (own only)."""
    svc = AiOperationalSuggestionService(session)
    return await svc.list_for_chw(current_user, limit=limit)
