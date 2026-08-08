from __future__ import annotations

import importlib
import pkgutil
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.errors import (
    app_exception_handler,
    auth_error_handler,
    generic_error_handler,
    http_exception_handler,
    not_found_error_handler,
    validation_error_handler,
)
from app.api.middleware import (
    AuditLogMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.security.rate_limit import RateLimitMiddleware as AppRateLimitMiddleware
from app.core.config import Environment, settings
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger, setup_logging
from app.core.security.firebase import get_firebase_app
from app.infrastructure.database import close_db
from app.infrastructure.redis import close_redis

logger = get_logger(__name__)


def _import_persistence_models() -> None:
    from sqlalchemy.exc import InvalidRequestError

    from app.infrastructure.persistence import models as persistence_models

    persistence_module_names = [
        module_name
        for finder, module_name, is_pkg in pkgutil.iter_modules(persistence_models.__path__)
        if not is_pkg
    ]
    pending_modules = sorted(persistence_module_names)
    imported_modules: set[str] = set()

    while pending_modules:
        progress = False
        for module_name in pending_modules[:]:
            try:
                importlib.import_module(f"app.infrastructure.persistence.models.{module_name}")
                imported_modules.add(module_name)
                pending_modules.remove(module_name)
                progress = True
            except InvalidRequestError:
                continue
        if not progress:
            raise RuntimeError(
                "Unable to import persistence models due to unresolved dependencies: "
                + ", ".join(pending_modules)
            )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()

    # Security startup validation
    if not settings.secret_key or settings.secret_key == "change-me-to-a-random-secret-key":
        logger.warning("SECURITY: SECRET_KEY is not set or is the default value. Set a strong random key in .env for production.")
    if settings.environment == Environment.PRODUCTION:
        if settings.cors_origins == "http://localhost:3000,http://localhost:5173":
            logger.warning("SECURITY: CORS origins use localhost defaults in production. Configure proper CORS_ORIGINS.")
        if settings.allowed_hosts_list == ["*"]:
            logger.warning("SECURITY: ALLOWED_HOSTS is set to wildcard. Restrict to specific domains in production.")
        if settings.enable_security_headers:
            logger.info("SECURITY: Security headers enabled (CSP, HSTS, X-Frame-Options, etc.)")
        if not settings.firebase_credentials:
            logger.error("SECURITY: Firebase credentials not configured. Authentication will be disabled in production!")
    logger.info(
        "Starting %s v%s (%s)",
        settings.project_name,
        settings.version,
        settings.environment.value,
    )

    # init_db()

    from app.infrastructure.database import get_db

    async for session in get_db():
        from app.infrastructure.seed import seed_database

        await seed_database(session)
        break

    get_firebase_app()

    yield

    await close_db()
    await close_redis()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    _import_persistence_models()

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description="Healthcare Risk Assessment Platform API",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    _setup_middleware(app)
    _setup_exception_handlers(app)
    _setup_routers(app)

    return app


def _setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"^https://(?:[a-zA-Z0-9-]+\.)*(?:vercel\.app|onrender\.com|medicheck\.app)$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-Correlation-ID",
            "X-CSRF-Token",
            "Accept",
        ],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(AppRateLimitMiddleware,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    # app.add_middleware(CSRFProtectMiddleware)


def _setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)


def _setup_routers(app: FastAPI) -> None:
    from app.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix=settings.api_v1_prefix)


app = create_app()
