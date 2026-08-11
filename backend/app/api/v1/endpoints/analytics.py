"""Phase 6 — Population Health + SDG Analytics API.

All endpoints return de-identified, aggregated, small-cell-suppressed metrics.
No patient identifiers, raw answers, transcripts, or trace IDs appear in any
response. Access requires the ANALYTICS_VIEW_POPULATION permission
(RESEARCH_REVIEWER, MEDICAL_DIRECTOR, SUPER_ADMIN).
"""

from __future__ import annotations

import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_analytics_user, get_db
from app.application.dtos.analytics_dtos import (
    AccessibilityResponse,
    AnalyticsFilters,
    AnalyticsOverviewResponse,
    BodySystemsResponse,
    IndicatorsResponse,
    SDGDashboardResponse,
    SeverityDistributionResponse,
    TimeBucket,
    TrajectoryResponse,
)
from app.application.services.population_analytics_service import (
    PopulationAnalyticsService,
)
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.domain.entities.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Population Analytics (Phase 6)"])


def _build_filters(
    start_date: datetime.date | None,
    end_date: datetime.date | None,
    body_system_id: str | None,
    language: str | None,
    input_type: str | None,
) -> AnalyticsFilters:
    # Validate language if provided.
    if language:
        supported = [l.strip() for l in settings.supported_intake_languages.split(",")]
        if language not in supported:
            raise AuthorizationError(
                detail=f"Unsupported language. Supported: {', '.join(supported)}"
            )
    # Validate input_type.
    if input_type and input_type not in ("text", "voice"):
        raise AuthorizationError(detail="input_type must be 'text' or 'voice'.")
    # Validate date range.
    if start_date and end_date and end_date < start_date:
        raise AuthorizationError(detail="end_date cannot be before start_date.")
    if start_date and end_date:
        max_days = settings.analytics_max_date_range_days
        if (end_date - start_date).days > max_days:
            raise AuthorizationError(
                detail=f"Date range exceeds maximum of {max_days} days."
            )
    return AnalyticsFilters(
        start_date=start_date,
        end_date=end_date,
        body_system_id=body_system_id,
        language=language,
        input_type=input_type,
    )


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Population health overview",
    description="De-identified overview of assessment activity with time-series trend.",
)
async def get_overview(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    bucket: TimeBucket = Query(default="month"),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> AnalyticsOverviewResponse:
    logger.info(
        "analytics overview requested by role=%s bucket=%s",
        user.roles, bucket,
    )
    filters = _build_filters(start_date, end_date, None, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_overview(filters, bucket=bucket)


@router.get(
    "/severity",
    response_model=SeverityDistributionResponse,
    summary="Severity distribution",
    description="Distribution of MediCheck assessment findings (body-system categories). NOT population prevalence.",
)
async def get_severity(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    body_system_id: str | None = Query(default=None),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> SeverityDistributionResponse:
    filters = _build_filters(start_date, end_date, body_system_id, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_severity_distribution(filters)


@router.get(
    "/body-systems",
    response_model=BodySystemsResponse,
    summary="Body-system analytics",
    description="Assessment counts by body system (active, non-deleted only).",
)
async def get_body_systems(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> BodySystemsResponse:
    filters = _build_filters(start_date, end_date, None, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_body_systems(filters)


@router.get(
    "/indicators",
    response_model=IndicatorsResponse,
    summary="Indicator trends",
    description="Assessment counts activating each clinical indicator. Indicator activation is NOT confirmed diagnosis.",
)
async def get_indicators(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    body_system_id: str | None = Query(default=None),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> IndicatorsResponse:
    filters = _build_filters(start_date, end_date, body_system_id, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_indicators(filters)


@router.get(
    "/trajectory",
    response_model=TrajectoryResponse,
    summary="Trajectory distribution",
    description="Distribution of Phase 4 trend classifications. A worsening trajectory is an assessment trend, not disease progression.",
)
async def get_trajectory(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> TrajectoryResponse:
    filters = _build_filters(start_date, end_date, None, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_trajectory(filters)


@router.get(
    "/accessibility",
    response_model=AccessibilityResponse,
    summary="Accessibility metrics (Phase 5)",
    description="Multilingual + voice accessibility metrics. Language is an interaction metric, not a demographic.",
)
async def get_accessibility(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    language: str | None = Query(default=None),
) -> AccessibilityResponse:
    filters = _build_filters(start_date, end_date, None, language, None)
    svc = PopulationAnalyticsService(session)
    return await svc.get_accessibility(filters)


@router.get(
    "/sdg",
    response_model=SDGDashboardResponse,
    summary="SDG dashboard",
    description="SDG-aligned digital health monitoring indicators. Platform-derived, not validated SDG indicators.",
)
async def get_sdg_dashboard(
    user: Annotated[User, Depends(get_analytics_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime.date | None = Query(default=None),
    end_date: datetime.date | None = Query(default=None),
    language: str | None = Query(default=None),
    input_type: str | None = Query(default=None),
) -> SDGDashboardResponse:
    filters = _build_filters(start_date, end_date, None, language, input_type)
    svc = PopulationAnalyticsService(session)
    return await svc.get_sdg_dashboard(filters)
