from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.dtos.common import ErrorBody, ErrorResponse
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError | AppException,
) -> JSONResponse:
    # Handles both Pydantic RequestValidationError (request-body validation)
    # and our AppException-based ValidationError (service-layer validation).
    if isinstance(exc, AppException):
        logger.warning(
            "Validation error for %s %s: %s",
            request.method,
            request.url.path,
            exc.detail,
        )
        body = ErrorResponse(
            success=False,
            error=ErrorBody(
                code=exc.code or "validation_error",
                message=exc.detail or "Validation failed",
                details=[],
            ),
        ).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            }
        )

    logger.warning(
        "Validation error for %s %s: %s",
        request.method,
        request.url.path,
        errors,
    )

    body = ErrorResponse(
        success=False,
        error=ErrorBody(
            code="validation_error",
            message="Validation failed",
            details=[str(e) for e in errors],
        ),
    ).model_dump()

    return JSONResponse(status_code=422, content=body)


async def auth_error_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "Auth error for %s %s: %s",
        request.method,
        request.url.path,
        exc.detail,
    )
    body = ErrorResponse(
        success=False,
        error=ErrorBody(code=exc.code or "auth_error", message=exc.detail or "Authentication error", details=[]),
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


async def not_found_error_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.info(
        "Not found: %s %s",
        request.method,
        request.url.path,
    )
    body = ErrorResponse(
        success=False,
        error=ErrorBody(code=exc.code or "not_found", message=exc.detail or "Resource not found", details=[]),
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    logger.warning(
        "HTTP exception for %s %s: %d %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    body = ErrorResponse(
        success=False,
        error=ErrorBody(code="http_error", message=str(exc.detail), details=[]),
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error(
            "App exception for %s %s: %s",
            request.method,
            request.url.path,
            exc.detail,
            exc_info=True,
        )
    else:
        logger.warning(
            "App exception for %s %s: %s",
            request.method,
            request.url.path,
            exc.detail,
        )

    body = ErrorResponse(
        success=False,
        error=ErrorBody(code=exc.code or "app_error", message=exc.detail or "Application error", details=[]),
    ).model_dump()

    return JSONResponse(status_code=exc.status_code, content=body)


async def generic_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled exception for %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )
    body = ErrorResponse(
        success=False,
        error=ErrorBody(code="internal_error", message="An unexpected error occurred", details=[]),
    ).model_dump()
    return JSONResponse(status_code=500, content=body)
