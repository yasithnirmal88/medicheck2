from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[str] | None = Field(None, description="Optional list of detail messages")

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    success: bool = Field(False)
    error: ErrorBody

    model_config = {"from_attributes": True}


class SuccessResponse(GenericModel, Generic[T]):
    success: bool = Field(True)
    data: T

    model_config = {"from_attributes": True}


class IdResponse(BaseModel):
    id: str

    model_config = {"from_attributes": True}


class TimestampedResponse(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaginationResponse(GenericModel, Generic[T]):
    items: list[T]
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False

    model_config = {"from_attributes": True}
