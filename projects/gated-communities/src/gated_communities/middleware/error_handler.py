"""
Error handling middleware for gated-communities.

Provides:
- Custom exception classes with proper HTTP status codes
- ErrorHandlerMiddleware that catches exceptions and formats consistent JSON responses
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Awaitable, Callable, Dict, Optional, Type

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exception Classes
# ---------------------------------------------------------------------------


class AppException(Exception):
    """Base application exception with HTTP status code."""

    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An internal server error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(AppException):
    """Resource not found."""

    status_code = 404
    error_code = "not_found"
    message = "The requested resource was not found."


class ValidationError(AppException):
    """Invalid input data."""

    status_code = 422
    error_code = "validation_error"
    message = "The provided data failed validation."


class AuthenticationError(AppException):
    """Authentication failed or missing."""

    status_code = 401
    error_code = "authentication_error"
    message = "Authentication is required or has failed."


class AuthorizationError(AppException):
    """Insufficient permissions."""

    status_code = 403
    error_code = "authorization_error"
    message = "You do not have permission to perform this action."


class ConflictError(AppException):
    """Resource conflict (e.g., duplicate)."""

    status_code = 409
    error_code = "conflict"
    message = "The request conflicts with the current state of the resource."


class RateLimitError(AppException):
    """Too many requests."""

    status_code = 429
    error_code = "rate_limit_exceeded"
    message = "Rate limit exceeded. Please try again later."


# ---------------------------------------------------------------------------
# Error Handler Middleware
# ---------------------------------------------------------------------------


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches unhandled exceptions and returns
    consistent JSON error responses.

    - AppException subclasses are serialised with their status code and body.
    - Unexpected exceptions are logged and return a generic 500 response.
    """

    def __init__(
        self,
        app: Any,
        *,
        debug: bool = False,
        include_traceback: bool = False,
    ) -> None:
        super().__init__(app)
        self.debug = debug
        self.include_traceback = include_traceback

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Any]],
    ) -> Any:
        try:
            return await call_next(request)
        except AppException as exc:
            return self._handle_app_exception(exc)
        except Exception as exc:
            return self._handle_unexpected_exception(exc, request)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_app_exception(self, exc: AppException) -> JSONResponse:
        """Format a known application exception."""
        logger.warning(
            "AppException [%s] %s: %s",
            exc.error_code,
            exc.status_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    def _handle_unexpected_exception(
        self,
        exc: Exception,
        request: Request,
    ) -> JSONResponse:
        """Format an unexpected exception as a generic 500 error."""
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )

        body: Dict[str, Any] = {
            "error": {
                "code": "internal_error",
                "message": "An internal server error occurred.",
                "details": {},
            }
        }

        if self.debug or self.include_traceback:
            body["error"]["details"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }
            if self.include_traceback:
                body["error"]["details"]["traceback"] = traceback.format_exc()

        return JSONResponse(
            status_code=500,
            content=body,
        )
