from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

audit_logger = get_logger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    SENSITIVE_PATHS = {"/login", "/token", "/register", "/password"}
    SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in self.SENSITIVE_METHODS or any(
            p in request.url.path for p in self.SENSITIVE_PATHS
        ):
            start = time.time()
            response = await call_next(request)
            elapsed = time.time() - start

            audit_logger.info(
                "audit_event",
                extra={
                    "event": "api_access",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "elapsed_ms": round(elapsed * 1000),
                    "user_id": request.headers.get("x-user-id", "anonymous"),
                },
            )
            return response

        return await call_next(request)
