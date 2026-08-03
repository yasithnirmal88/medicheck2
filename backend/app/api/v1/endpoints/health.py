from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.infrastructure.database import create_session_factory
from app.infrastructure.redis import redis_health_check

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
    db_status: str
    redis_status: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_status = "unknown"
    redis_status = "unknown"

    try:
        factory = create_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    try:
        redis_ok = await redis_health_check()
        redis_status = "healthy" if redis_ok else "unhealthy"
    except Exception:
        redis_status = "unhealthy"

    overall = "healthy"
    if db_status == "unhealthy" or redis_status == "unhealthy":
        overall = "degraded"

    return HealthResponse(
        status=overall,
        version=settings.version,
        environment=settings.environment.value,
        timestamp=datetime.now(UTC).isoformat(),
        db_status=db_status,
        redis_status=redis_status,
    )
