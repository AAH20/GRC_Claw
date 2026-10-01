"""Custom exceptions and error handling."""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """RFC 7807 Problem Details error response."""

    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    timestamp: str
    request_id: str | None = None
    trace_id: str | None = None
    errors: list[dict[str, Any]] | None = None


class GRCClawException(Exception):
    """Base exception for GRC_Claw API."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        errors: list[dict[str, Any]] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.errors = errors
        super().__init__(message)


class NotFoundException(GRCClawException):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with ID '{resource_id}' does not exist.",
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{resource.upper()}_NOT_FOUND",
        )


class ValidationException(GRCClawException):
    """Request validation failed."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            errors=errors,
        )


class ConflictException(GRCClawException):
    """Resource conflict."""

    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code=code,
        )


class UnauthorizedException(GRCClawException):
    """Missing or invalid credentials."""

    def __init__(self, message: str = "Missing or invalid credentials."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
        )


class ForbiddenException(GRCClawException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
        )


class RateLimitException(GRCClawException):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 30, limit: int = 1000):
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
        )
        self.retry_after = retry_after
        self.limit = limit


class PolicyCompilationException(GRCClawException):
    """Policy compilation failed."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="POLICY_COMPILATION_FAILED",
        )
        self.compilation_errors = errors


async def grc_exception_handler(request: Request, exc: GRCClawException) -> JSONResponse:
    """Handle custom GRC_Claw exceptions."""
    from datetime import datetime, timezone

    error = ErrorDetail(
        type=f"https://api.grc-claw.io/errors/{exc.code.lower()}",
        title=exc.code.replace("_", " ").title(),
        status=exc.status_code,
        detail=exc.message,
        instance=str(request.url.path),
        code=exc.code,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request.headers.get("X-Request-ID"),
        trace_id=request.headers.get("X-Trace-ID"),
        errors=exc.errors,
    )

    headers = {}
    if isinstance(exc, RateLimitException):
        headers["Retry-After"] = str(exc.retry_after)
        headers["X-RateLimit-Limit"] = str(exc.limit)
        headers["X-RateLimit-Remaining"] = "0"

    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(exclude_none=True),
        headers=headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    from datetime import datetime, timezone

    error = ErrorDetail(
        type="https://api.grc-claw.io/errors/internal-error",
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
        code="INTERNAL_ERROR",
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=request.headers.get("X-Request-ID"),
        trace_id=request.headers.get("X-Trace-ID"),
    )

    return JSONResponse(
        status_code=500,
        content=error.model_dump(exclude_none=True),
    )
