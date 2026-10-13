"""AI vendor spend / abuse guardrails.

Lightweight, request-count budgets for METERED (real-vendor) AI calls:
per-user hourly, per-user daily, and a global daily circuit breaker.
Stub providers bypass budgets entirely (no vendor cost), so local
development, CI, and offline deployments are unaffected.

Design notes:
- Counters live in Redis (``medicheck:ai:budget:v1:…`` keys, ``INCR`` +
  ``EXPIRE`` per tier). When Redis is unreachable, a process-local fallback
  keeps enforcing approximately — protection degrades but never vanishes,
  and care delivery never blocks on Redis.
- Consume-then-check: the increment happens before the comparison, so a
  rejected request still consumes one unit (conservative direction for
  spend; windows are short and self-healing). Concurrent overshoot of a
  few requests is possible and accepted for a guardrail.
- Exceeding any tier raises ``AIBudgetExceededError`` (HTTP 429,
  code ``ai_budget_exceeded``). Callers must let it propagate — it must
  NEVER be converted into a stub fallback.
- Only metadata (operation, tier, limit) ever appears in messages/logs:
  no keys, no audio, no transcripts, no patient text.
"""

from __future__ import annotations

import time
from typing import Any

from app.core.config import settings
from app.core.exceptions import AIBudgetExceededError
from app.core.logging import get_logger

logger = get_logger(__name__)

_KEY_PREFIX = "medicheck:ai:budget:v1"

# TTL padding (seconds) so counters outlive the window they cover.
_HOURLY_TTL = 3900
_DAILY_TTL = 90000


def _hour_key(now: float) -> str:
    return time.strftime("%Y%m%d%H", time.gmtime(now))


def _day_key(now: float) -> str:
    return time.strftime("%Y%m%d", time.gmtime(now))


class _LocalBudgetStore:
    """Process-local fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._counts: dict[str, tuple[int, float]] = {}

    def check_and_consume(self, key: str, limit: int, ttl: int) -> bool:
        now = time.time()
        count, reset_at = self._counts.get(key, (0, now + ttl))
        if now >= reset_at:
            count, reset_at = 0, now + ttl
        if count >= limit:
            self._counts[key] = (count, reset_at)
            return False
        self._counts[key] = (count + 1, reset_at)
        return True


_LOCAL_STORE = _LocalBudgetStore()


def _resolve_client(explicit: Any | None) -> Any | None:
    """Return an async Redis client, or None when unavailable (→ local)."""
    if explicit is not None:
        return explicit
    try:
        from app.infrastructure.redis import get_redis_client

        return get_redis_client()
    except Exception as exc:
        logger.warning(
            "AI budget: redis unavailable (%s); using local fallback",
            type(exc).__name__,
        )
        return None


async def _redis_consume(client: Any, key: str, limit: int, ttl: int) -> bool:
    count = await client.incr(key)
    if int(count) == 1:
        await client.expire(key, ttl)
    return int(count) <= limit


def _tiers(user_id: str, operation: str, now: float) -> list[tuple[str, int, int, str, str]]:
    """(counter key, limit, ttl, label, scope) per enforced tier."""
    return [
        (
            f"{_KEY_PREFIX}:user:{user_id}:{operation}:hour:{_hour_key(now)}",
            settings.ai_budget_user_hourly_requests,
            _HOURLY_TTL,
            "hourly",
            "user",
        ),
        (
            f"{_KEY_PREFIX}:user:{user_id}:{operation}:day:{_day_key(now)}",
            settings.ai_budget_user_daily_requests,
            _DAILY_TTL,
            "daily",
            "user",
        ),
        (
            f"{_KEY_PREFIX}:global:{operation}:day:{_day_key(now)}",
            settings.ai_budget_global_daily_requests,
            _DAILY_TTL,
            "global daily",
            "global",
        ),
    ]


async def enforce_ai_budget(
    *,
    user_id: str,
    operation: str,
    metered: bool,
    redis_client: Any | None = None,
) -> None:
    """Enforce vendor spend budgets for one metered AI call.

    ``operation`` is ``report_explanation`` | ``intake_extract`` |
    ``trajectory_explanation`` | ``stt_transcribe``. ``metered=False``
    (stubs) returns immediately with zero I/O. Raises
    ``AIBudgetExceededError`` when any configured tier is exhausted.
    """
    if not metered:
        return
    now = time.time()
    client = _resolve_client(redis_client)
    for key, limit, ttl, label, scope in _tiers(user_id, operation, now):
        if not limit or limit <= 0:
            continue  # tier disabled
        try:
            allowed = (
                await _redis_consume(client, key, limit, ttl)
                if client is not None
                else _LOCAL_STORE.check_and_consume(key, limit, ttl)
            )
        except Exception as exc:
            logger.warning(
                "AI budget: redis error (%s); using local fallback",
                type(exc).__name__,
            )
            allowed = _LOCAL_STORE.check_and_consume(key, limit, ttl)
        if not allowed:
            logger.warning(
                "AI budget exceeded: operation=%s scope=%s tier=%s limit=%d",
                operation,
                scope,
                label,
                limit,
            )
            raise AIBudgetExceededError(
                detail=(
                    f"AI budget exceeded for {operation} "
                    f"({label} limit of {limit} reached). "
                    "Try again later."
                )
            )
