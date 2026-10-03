"""Exception models for the recruitment platform."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: str
    details: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None
