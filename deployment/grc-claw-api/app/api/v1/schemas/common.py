"""Common schemas shared across all endpoints."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Cursor-based pagination parameters."""

    limit: int = Field(default=50, ge=1, le=500)
    cursor: str | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata in responses."""

    next_cursor: str | None = None
    has_next: bool = False
    total: int | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    data: list[T]
    pagination: PaginationMeta


class HealthComponent(BaseModel):
    """Health check component status."""

    status: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    components: dict[str, HealthComponent]
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    checks: dict[str, HealthComponent]


class IdempotencyKey(BaseModel):
    """Idempotency key header."""

    idempotency_key: str | None = Field(default=None, max_length=255)
