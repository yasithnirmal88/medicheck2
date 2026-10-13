from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
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


class ReadinessResponse(BaseModel):
    status: str
    db_status: str
    redis_status: str


async def _db_status() -> str:
    """Database reachability probe (SELECT 1). No PHI, no table access."""
    try:
        factory = create_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
            return "healthy"
    except Exception:
        return "unhealthy"


async def _redis_status() -> str:
    try:
        return "healthy" if await redis_health_check() else "unhealthy"
    except Exception:
        return "unhealthy"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness + dependency overview. Always returns 200 (orchestrators and
    existing monitors rely on reachability, not the status field)."""
    db_status = await _db_status()
    redis_status = await _redis_status()

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


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe for orchestrators/autoscalers.

    Returns 200 only when database AND Redis are both reachable, else 503
    so traffic is routed away from unready instances. Use this (not
    ``/health``) as the readiness gate; ``/health`` stays 200 for
    backward-compatible liveness monitoring.
    """
    db_status = await _db_status()
    redis_status = await _redis_status()
    healthy = db_status == "healthy" and redis_status == "healthy"
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ready" if healthy else "not_ready",
            "db_status": db_status,
            "redis_status": redis_status,
        },
    )
