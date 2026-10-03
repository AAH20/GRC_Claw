"""Exception models for the recruitment platform."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None
