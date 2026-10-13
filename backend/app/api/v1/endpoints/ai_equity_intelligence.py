"""Phase 11 — AI equity intelligence + SDG narrative + review API.

Endpoints:
- POST /api/v1/ai-equity/equity-insight       : generate left-behind equity
  intelligence over de-identified aggregates.
- GET  /api/v1/ai-equity/equity-insight        : list persisted equity insights.
- POST /api/v1/ai-equity/sdg-narratives        : generate SDG narratives.
- GET  /api/v1/ai-equity/sdg-narratives        : list persisted SDG narratives.
- POST /api/v1/ai-equity/review/operational/{id}     : review (approve/reject/edit).
- POST /api/v1/ai-equity/review/operational/{id}/publish
- POST /api/v1/ai-equity/review/population/{id}      : review (approve/reject/edit).
- POST /api/v1/ai-equity/review/population/{id}/publish

Population outputs are de-identified + k-anonymity-suppressed. AI never
self-publishes — only a human reviewer may approve/reject/edit/publish.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_insight_reviewer_user,
    get_population_insight_user,
)
from app.application.dtos.ai_governance_dtos import (
    EquityInsightResponse,
    InsightReviewResponse,
    PopulationInsightRecord,
    ReviewRequest,
    SdgNarrativeResponse,
)
from app.application.dtos.analytics_dtos import AnalyticsFilters
from app.application.services.ai_insight_review_service import (
    AiInsightReviewService,
)
from app.application.services.equity_intelligence_service import (
    EquityIntelligenceService,
)
from app.application.services.population_narrative_service import (
    PopulationNarrativeService,
)
from app.identity import User

router = APIRouter(prefix="/ai-equity", tags=["ai-equity-intelligence"])


def _filters(
    start_date: date | None = None, end_date: date | None = None
) -> AnalyticsFilters:
    return AnalyticsFilters(start_date=start_date, end_date=end_date)


# ── Equity intelligence ───────────────────────────────────────────────


@router.post("/equity-insight", response_model=EquityInsightResponse)
async def generate_equity_insight(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_population_insight_user),
    session: AsyncSession = Depends(get_db),
) -> EquityInsightResponse:
    """Generate left-behind equity intelligence over de-identified aggregates."""
    svc = EquityIntelligenceService(session)
    return await svc.generate_equity_insight(
        current_user, _filters(start_date, end_date)
    )


@router.get("/equity-insight", response_model=list[PopulationInsightRecord])
async def list_equity_insights(
    limit: int | None = Query(default=None, ge=1, le=200),
    current_user: User = Depends(get_population_insight_user),
    session: AsyncSession = Depends(get_db),
) -> list[PopulationInsightRecord]:
    svc = EquityIntelligenceService(session)
    return await svc.list_insights(current_user, limit=limit)


# ── SDG narratives ────────────────────────────────────────────────────


@router.post("/sdg-narratives", response_model=SdgNarrativeResponse)
async def generate_sdg_narratives(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_population_insight_user),
    session: AsyncSession = Depends(get_db),
) -> SdgNarrativeResponse:
    """Generate SDG narratives over de-identified aggregate metrics."""
    svc = PopulationNarrativeService(session)
    return await svc.generate_narratives(
        current_user, _filters(start_date, end_date)
    )


@router.get("/sdg-narratives", response_model=list[PopulationInsightRecord])
async def list_sdg_narratives(
    limit: int | None = Query(default=None, ge=1, le=200),
    current_user: User = Depends(get_population_insight_user),
    session: AsyncSession = Depends(get_db),
) -> list[PopulationInsightRecord]:
    svc = PopulationNarrativeService(session)
    return await svc.list_narratives(current_user, limit=limit)


# ── Human review workflow ─────────────────────────────────────────────


@router.post(
    "/review/operational/{suggestion_id}", response_model=InsightReviewResponse
)
async def review_operational(
    suggestion_id: str,
    req: ReviewRequest,
    current_user: User = Depends(get_insight_reviewer_user),
    session: AsyncSession = Depends(get_db),
) -> InsightReviewResponse:
    """Approve/reject/edit an AI operational suggestion (human reviewer only)."""
    svc = AiInsightReviewService(session)
    return await svc.review_operational(current_user, suggestion_id, req)


@router.post(
    "/review/operational/{suggestion_id}/publish",
    response_model=InsightReviewResponse,
)
async def publish_operational(
    suggestion_id: str,
    current_user: User = Depends(get_insight_reviewer_user),
    session: AsyncSession = Depends(get_db),
) -> InsightReviewResponse:
    """Publish an approved/edited operational suggestion (human reviewer only)."""
    svc = AiInsightReviewService(session)
    return await svc.publish_operational(current_user, suggestion_id)


@router.post(
    "/review/population/{insight_id}", response_model=InsightReviewResponse
)
async def review_population(
    insight_id: str,
    req: ReviewRequest,
    current_user: User = Depends(get_insight_reviewer_user),
    session: AsyncSession = Depends(get_db),
) -> InsightReviewResponse:
    """Approve/reject/edit an AI population/equity/SDG insight."""
    svc = AiInsightReviewService(session)
    return await svc.review_population(current_user, insight_id, req)


@router.post(
    "/review/population/{insight_id}/publish",
    response_model=InsightReviewResponse,
)
async def publish_population(
    insight_id: str,
    current_user: User = Depends(get_insight_reviewer_user),
    session: AsyncSession = Depends(get_db),
) -> InsightReviewResponse:
    """Publish an approved/edited population insight (human reviewer only)."""
    svc = AiInsightReviewService(session)
    return await svc.publish_population(current_user, insight_id)
