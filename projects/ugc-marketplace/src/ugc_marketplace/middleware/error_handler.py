"""Error handling middleware and custom exceptions for ugc-marketplace."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base application error with HTTP status code."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    """Resource not found."""

    status_code = 404
    error_code = "not_found"


class ValidationError(AppError):
    """Invalid input data."""

    status_code = 422
    error_code = "validation_error"


class AuthenticationError(AppError):
    """Authentication failed or missing."""

    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(AppError):
    """Insufficient permissions."""

    status_code = 403
    error_code = "authorization_error"


class ConflictError(AppError):
    """Resource conflict."""

    status_code = 409
    error_code = "conflict"


# ---------------------------------------------------------------------------
# Error Handler Middleware
# ---------------------------------------------------------------------------


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return structured JSON error responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Any]],
    ) -> Any:
        try:
            return await call_next(request)
        except AppError as exc:
            return self._build_response(exc.status_code, exc.error_code, exc.message, exc.details)
        except Exception as exc:
            logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
            return self._build_response(
                500,
                "internal_error",
                "An unexpected error occurred.",
            )

    @staticmethod
    def _build_response(
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        body: dict[str, Any] = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }
        if details:
            body["error"]["details"] = details
        return JSONResponse(status_code=status_code, content=body)
