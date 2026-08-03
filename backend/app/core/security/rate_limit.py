from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.exceptions import RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


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
        if not await self._is_rate_limited(request):
            return await call_next(request)

        raise RateLimitError(
            detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s"
        )

    async def _is_rate_limited(self, request: Request) -> bool:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        if client_ip not in self._requests:
            self._requests[client_ip] = []

        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning("Rate limit exceeded for IP: %s", client_ip)
            return True

        self._requests[client_ip].append(now)
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
