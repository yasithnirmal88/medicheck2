from __future__ import annotations

from typing import Any


class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    code: str = "internal_error"

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or {}
        super().__init__(self.detail)

    def to_dict(self) -> dict[str, Any]:
        return {
            "detail": self.detail,
            "code": self.code,
            "status_code": self.status_code,
            **self.extra,
        }


class AuthenticationError(AppException):
    status_code = 401
    detail = "Not authenticated"
    code = "authentication_error"


class AuthorizationError(AppException):
    status_code = 403
    detail = "Not authorized"
    code = "authorization_error"


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"
    code = "not_found"


class ValidationError(AppException):
    status_code = 422
    detail = "Validation failed"
    code = "validation_error"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource already exists"
    code = "conflict"


class RateLimitError(AppException):
    status_code = 429
    detail = "Too many requests"
    code = "rate_limit_exceeded"


class InternalError(AppException):
    status_code = 500
    detail = "Internal server error"
    code = "internal_error"
