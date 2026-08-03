from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        if settings.enable_security_headers:
            # HSTS (HTTP Strict Transport Security)
            if settings.is_production:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={settings.hsts_max_age}; includeSubDomains; preload"
                )
            else:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={settings.hsts_max_age}; includeSubDomains"
                )

            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"

            # XSS protection (legacy browsers)
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Permissions policy (disable risky features)
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), interest-cohort=()"
            )

            # Content Security Policy
            directive = settings.csp_report_only
            csp_key = "Content-Security-Policy-Report-Only" if directive else "Content-Security-Policy"

            swagger_sources = (
                " https://cdn.jsdelivr.net"
                if settings.is_development
                else ""
            )

            response.headers[csp_key] = (
                "default-src 'self'; "
                f"script-src 'self' 'unsafe-inline' https://apis.google.com https://www.gstatic.com{swagger_sources}; "
                f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com{swagger_sources}; "
                "img-src 'self' data: blob: https:; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com; "
                "frame-src 'self' https://medicheck.firebaseapp.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        return response
