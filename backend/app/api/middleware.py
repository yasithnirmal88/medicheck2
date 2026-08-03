from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger, get_request_id_filter

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            request.headers.get("X-Correlation-ID", uuid.uuid4().hex),
        )
        request.state.request_id = request_id
        get_request_id_filter().request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start_time

        response.headers["X-Response-Time"] = f"{elapsed:.4f}s"

        if elapsed > 1.0:
            logger.warning(
                "Slow request: %s %s took %.4fs",
                request.method,
                request.url.path,
                elapsed,
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        req_id = getattr(request.state, "request_id", "-")
        logger.info(
            "--> %s %s",
            request.method,
            request.url.path,
        )

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        logger.info(
            "<-- %s %s %d (%.4fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        if settings.enable_security_headers:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={settings.hsts_max_age}; includeSubDomains"
                + ("; preload" if settings.is_production else "")
            )
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), interest-cohort=()"
            )
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://apis.google.com https://www.gstatic.com"
                + (" https://cdn.jsdelivr.net" if settings.is_development else "")
                + "; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com"
                + (" https://cdn.jsdelivr.net" if settings.is_development else "")
                + "; "
                "img-src 'self' data: blob: https:; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com; "
                "frame-src 'self' https://medicheck.firebaseapp.com; "
                "object-src 'none'; base-uri 'self'; form-action 'self'"
            )
            key = "Content-Security-Policy-Report-Only" if settings.csp_report_only else "Content-Security-Policy"
            response.headers[key] = csp
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    SENSITIVE_PATHS = {"/login", "/token", "/register", "/password"}
    SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        is_sensitive = (
            request.method in self.SENSITIVE_METHODS
            or any(p in request.url.path for p in self.SENSITIVE_PATHS)
        )
        if not is_sensitive:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        audit_logger = get_logger("audit")
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


class CSRFProtectMiddleware(BaseHTTPMiddleware):
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if settings.environment.value != "production":
            return await call_next(request)

        if request.method not in self.SAFE_METHODS:
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                origin = request.headers.get("origin", "")
                referer = request.headers.get("referer", "")
                if not origin and not referer:
                    raise AuthenticationError(detail="CSRF check failed: missing origin/referer")
                allowed_hosts = set(settings.allowed_hosts_list)
                if origin:
                    from urllib.parse import urlparse
                    parsed = urlparse(origin)
                    if parsed.hostname and parsed.hostname not in allowed_hosts:
                        raise AuthenticationError(detail="CSRF check failed: invalid origin")
                if referer:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    if parsed.hostname and parsed.hostname not in allowed_hosts:
                        raise AuthenticationError(detail="CSRF check failed: invalid referer")
        return await call_next(request)
