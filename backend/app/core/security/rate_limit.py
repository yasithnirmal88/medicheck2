from __future__ import annotations

import math
import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.application.dtos.common import ErrorBody, ErrorResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


def _client_key(request: Request) -> str:
    """Proxy-aware best-effort client identity for rate limiting.

    Prefers the left-most (originating) ``X-Forwarded-For`` entry when the
    header is present - the value set by trusted proxies such as Render /
    Vercel - then ``X-Real-IP``, then the raw socket peer. Without this, a
    proxy addresses every request from the same backend IP and the limiter
    becomes a single global bucket for all users.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        client_key = _client_key(request)
        if not await self._is_rate_limited(client_key):
            return await call_next(request)
        # Return a real 429 response directly: this middleware runs OUTSIDE
        # Starlette's ExceptionMiddleware, so raising here would surface as
        # a generic 500 from ServerErrorMiddleware instead of the app's
        # exception handler. RateLimitError stays available for in-route use.
        return self._limited_response(client_key)

    def _retry_after(self, client_key: str) -> int:
        now = time.time()
        oldest = min(self._requests.get(client_key, []) or [now])
        return max(1, math.ceil(oldest + self.window_seconds - now))

    def _limited_response(self, client_key: str) -> JSONResponse:
        body = ErrorResponse(
            success=False,
            error=ErrorBody(
                code="rate_limit_exceeded",
                message=(
                    f"Rate limit exceeded. Max {self.max_requests} requests "
                    f"per {self.window_seconds}s"
                ),
                details=[],
            ),
        ).model_dump()
        return JSONResponse(
            status_code=429,
            content=body,
            headers={"Retry-After": str(self._retry_after(client_key))},
        )

    async def _is_rate_limited(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        if client_key not in self._requests:
            self._requests[client_key] = []

        self._requests[client_key] = [
            t for t in self._requests[client_key] if t > window_start
        ]

        if len(self._requests[client_key]) >= self.max_requests:
            logger.warning("Rate limit exceeded for key: %s", client_key)
            return True

        self._requests[client_key].append(now)
        return False


class RateLimiter:
    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        self._local: dict[str, list[float]] = {}

    async def check(self, key: str, max_requests: int, window: int) -> bool:
        if self._redis:
            return await self._check_redis(key, max_requests, window)
        return self._check_local(key, max_requests, window)

    async def _check_redis(self, key: str, max_requests: int, window: int) -> bool:
        try:

            pipeline = self._redis.pipeline()
            now = time.time()
            pipeline.zadd(key, {str(now): now})
            pipeline.zremrangebyscore(key, 0, now - window)
            pipeline.expire(key, window)
            pipeline.zcard(key)
            results = await pipeline.execute()
            count = results[-1]
            return count > max_requests
        except Exception as exc:
            logger.warning("Redis rate limit check failed: %s", exc)
            return False

    def _check_local(self, key: str, max_requests: int, window: int) -> bool:
        now = time.time()
        cutoff = now - window

        if key not in self._local:
            self._local[key] = []

        self._local[key] = [t for t in self._local[key] if t > cutoff]

        if len(self._local[key]) >= max_requests:
            return True

        self._local[key].append(now)
        return False
