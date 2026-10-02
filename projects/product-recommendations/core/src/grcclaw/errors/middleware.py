"""
Error Handling Middleware for GRC_Claw

FastAPI middleware that provides:
- RFC 7807 Problem Details responses
- Request ID and trace ID propagation
- Structured error logging
- Error classification and enrichment
- CORS headers for error responses
- Security headers
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .codes import get_error_code
from .taxonomy import ErrorCategory, classify_error

logger = logging.getLogger("grcclaw.errors")


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
    retry_after: float | None = None
    documentation_url: str | None = None


class ErrorContext:
    """Context information for an error."""

    def __init__(
        self,
        request_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.trace_id = trace_id or str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
        }
        if self.tenant_id:
            result["tenant_id"] = self.tenant_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.workflow_id:
            result["workflow_id"] = self.workflow_id
        if self.extra:
            result["extra"] = self.extra
        return result


class GRCClawException(Exception):
    """Base exception for GRC_Claw with full error context."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INTERNAL_ERROR",
        status_code: int | None = None,
        errors: list[dict[str, Any]] | None = None,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.errors = errors
        self.context = context or ErrorContext()
        self.cause = cause
        self.headers = headers or {}

        # Get classification from registry
        error_code = get_error_code(code)
        self.error_code = error_code
        self.status_code = status_code or error_code.http_status
        self.classification = classify_error(code)

    def to_error_detail(self, request: Request | None = None) -> ErrorDetail:
        """Convert to RFC 7807 ErrorDetail."""
        instance = str(request.url.path) if request else "/"
        return ErrorDetail(
            type=f"https://api.grc-claw.io/errors/{self.code.lower()}",
            title=self.code.replace("_", " ").title(),
            status=self.status_code,
            detail=self.message,
            instance=instance,
            code=self.code,
            timestamp=datetime.now(UTC).isoformat(),
            request_id=self.context.request_id,
            trace_id=self.context.trace_id,
            errors=self.errors,
            retry_after=self.classification.retry_after_seconds,
            documentation_url=self.error_code.documentation_url,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "classification": self.classification.to_dict(),
            "context": self.context.to_dict(),
            "errors": self.errors,
            "cause": str(self.cause) if self.cause else None,
        }


# ── Convenience Exception Constructors ────────────────────────────────────


def unauthenticated(
    message: str = "Missing or invalid credentials",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="UNAUTHENTICATED", **kwargs)


def token_expired(
    message: str = "Authentication token has expired",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="TOKEN_EXPIRED", **kwargs)


def token_invalid(
    message: str = "Authentication token is invalid",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="TOKEN_INVALID", **kwargs)


def api_key_invalid(
    message: str = "API key is invalid",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="API_KEY_INVALID", **kwargs)


def api_key_expired(
    message: str = "API key has expired",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="API_KEY_EXPIRED", **kwargs)


def forbidden(
    message: str = "Insufficient permissions",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="FORBIDDEN", **kwargs)


def insufficient_scope(
    message: str = "Insufficient scope for this operation",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="INSUFFICIENT_SCOPE", **kwargs)


def insufficient_role(
    message: str = "Insufficient role for this operation",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="INSUFFICIENT_ROLE", **kwargs)


def validation_error(
    message: str = "Request validation failed",
    errors: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(
        message, code="VALIDATION_ERROR", errors=errors, **kwargs
    )


def not_found(
    resource: str = "Resource",
    resource_id: str = "",
    **kwargs: Any,
) -> GRCClawException:
    message = f"{resource} with ID '{resource_id}' does not exist."
    return GRCClawException(message, code="NOT_FOUND", **kwargs)


def conflict(
    message: str = "Resource conflict",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="CONFLICT", **kwargs)


def rate_limit_exceeded(
    retry_after: int = 30,
    limit: int = 1000,
    **kwargs: Any,
) -> GRCClawException:
    exc = GRCClawException(
        f"Rate limit exceeded. Try again in {retry_after} seconds.",
        code="RATE_LIMIT_EXCEEDED",
        **kwargs,
    )
    exc.headers["Retry-After"] = str(retry_after)
    exc.headers["X-RateLimit-Limit"] = str(limit)
    exc.headers["X-RateLimit-Remaining"] = "0"
    return exc


def internal_error(
    message: str = "An unexpected error occurred",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="INTERNAL_ERROR", **kwargs)


def service_unavailable(
    message: str = "Service is temporarily unavailable",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="SERVICE_UNAVAILABLE", **kwargs)


def external_service_error(
    message: str = "External service returned an error",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="EXTERNAL_SERVICE_ERROR", **kwargs)


def timeout(
    message: str = "Operation timed out",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="TIMEOUT", **kwargs)


def policy_compilation_failed(
    message: str = "Policy compilation failed",
    errors: list[str] | None = None,
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(
        message, code="POLICY_COMPILATION_FAILED", errors=errors, **kwargs
    )


def workflow_execution_failed(
    message: str = "Workflow execution failed",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="WORKFLOW_EXECUTION_FAILED", **kwargs)


def workflow_step_failed(
    message: str = "Workflow step failed",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="WORKFLOW_STEP_FAILED", **kwargs)


def configuration_error(
    message: str = "Configuration error",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="CONFIGURATION_ERROR", **kwargs)


def security_violation(
    message: str = "Security violation detected",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="SECURITY_VIOLATION", **kwargs)


def dependency_unavailable(
    message: str = "Required dependency is unavailable",
    **kwargs: Any,
) -> GRCClawException:
    return GRCClawException(message, code="DEPENDENCY_UNAVAILABLE", **kwargs)


# ── Middleware ─────────────────────────────────────────────────────────────


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for unified error handling.

    - Assigns request IDs and trace IDs
    - Catches all unhandled exceptions
    - Returns RFC 7807 Problem Details responses
    - Logs structured error information
    - Adds security headers to error responses
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        debug: bool = False,
        include_stack_trace: bool = False,
        log_request_body: bool = False,
        log_response_body: bool = False,
        excluded_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.debug = debug
        self.include_stack_trace = include_stack_trace
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.excluded_paths = excluded_paths or {
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process a request with error handling."""
        # Skip excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Assign request IDs
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

        # Store in request state for access in route handlers
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        start_time = time.time()

        try:
            response = await call_next(request)

            # Add request ID headers to all responses
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id

            # Log slow requests
            duration = time.time() - start_time
            if duration > 5.0:
                logger.warning(
                    "Slow request",
                    extra={
                        "request_id": request_id,
                        "trace_id": trace_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration": duration,
                        "status_code": response.status_code,
                    },
                )

            return response

        except GRCClawException as exc:
            return self._handle_grc_exception(exc, request, request_id, trace_id)

        except Exception as exc:
            return self._handle_unexpected_exception(
                exc, request, request_id, trace_id
            )

    def _handle_grc_exception(
        self,
        exc: GRCClawException,
        request: Request,
        request_id: str,
        trace_id: str,
    ) -> JSONResponse:
        """Handle a GRCClawException."""
        # Update context with request IDs if not set
        if not exc.context.request_id:
            exc.context.request_id = request_id
        if not exc.context.trace_id:
            exc.context.trace_id = trace_id

        # Log the error
        self._log_error(exc, request)

        # Build response
        error_detail = exc.to_error_detail(request)
        content = error_detail.model_dump(exclude_none=True)

        if self.debug and self.include_stack_trace:
            import traceback

            content["stack_trace"] = traceback.format_exc()

        headers = dict(exc.headers)
        headers["X-Request-ID"] = request_id
        headers["X-Trace-ID"] = trace_id

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    def _handle_unexpected_exception(
        self,
        exc: Exception,
        request: Request,
        request_id: str,
        trace_id: str,
    ) -> JSONResponse:
        """Handle an unexpected exception."""
        # Classify the exception
        category = self._classify_exception(exc)
        code = self._exception_to_code(exc)

        error_code = get_error_code(code)
        classification = classify_error(code)

        # Log the error
        logger.error(
            "Unhandled exception",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "error_code": code,
                "category": category.value,
            },
            exc_info=True,
        )

        # Build response
        error_detail = ErrorDetail(
            type=f"https://api.grc-claw.io/errors/{code.lower()}",
            title=code.replace("_", " ").title(),
            status=error_code.http_status,
            detail=str(exc) if self.debug else "An unexpected error occurred",
            instance=str(request.url.path),
            code=code,
            timestamp=datetime.now(UTC).isoformat(),
            request_id=request_id,
            trace_id=trace_id,
            retry_after=classification.retry_after_seconds,
            documentation_url=error_code.documentation_url,
        )

        content = error_detail.model_dump(exclude_none=True)

        if self.debug and self.include_stack_trace:
            import traceback

            content["stack_trace"] = traceback.format_exc()

        headers = {
            "X-Request-ID": request_id,
            "X-Trace-ID": trace_id,
        }

        return JSONResponse(
            status_code=error_code.http_status,
            content=content,
            headers=headers,
        )

    def _log_error(self, exc: GRCClawException, request: Request) -> None:
        """Log a GRCClawException with structured data."""
        log_data = {
            "request_id": exc.context.request_id,
            "trace_id": exc.context.trace_id,
            "method": request.method,
            "path": request.url.path,
            "error_code": exc.code,
            "error_message": exc.message,
            "status_code": exc.status_code,
            "category": exc.classification.category.value,
            "severity": exc.classification.severity.value,
            "recoverability": exc.classification.recoverability.value,
            "scope": exc.classification.scope.value,
        }

        if exc.context.tenant_id:
            log_data["tenant_id"] = exc.context.tenant_id
        if exc.context.user_id:
            log_data["user_id"] = exc.context.user_id
        if exc.context.agent_id:
            log_data["agent_id"] = exc.context.agent_id
        if exc.context.workflow_id:
            log_data["workflow_id"] = exc.context.workflow_id

        # Log at appropriate level based on severity
        severity = exc.classification.severity
        if severity == "critical":
            logger.critical("GRC_Claw error", extra=log_data, exc_info=exc.cause)
        elif severity == "high":
            logger.error("GRC_Claw error", extra=log_data, exc_info=exc.cause)
        elif severity == "medium":
            logger.warning("GRC_Claw error", extra=log_data)
        else:
            logger.info("GRC_Claw error", extra=log_data)

    def _classify_exception(self, exc: Exception) -> ErrorCategory:
        """Classify a standard Python exception."""
        exc_name = type(exc).__name__
        mapping: dict[str, ErrorCategory] = {
            "ValueError": ErrorCategory.VALIDATION,
            "TypeError": ErrorCategory.VALIDATION,
            "KeyError": ErrorCategory.VALIDATION,
            "IndexError": ErrorCategory.VALIDATION,
            "AttributeError": ErrorCategory.INTERNAL,
            "NotImplementedError": ErrorCategory.INTERNAL,
            "RuntimeError": ErrorCategory.INTERNAL,
            "OSError": ErrorCategory.NETWORK,
            "IOError": ErrorCategory.NETWORK,
            "ConnectionError": ErrorCategory.NETWORK,
            "TimeoutError": ErrorCategory.TIMEOUT,
            "FileNotFoundError": ErrorCategory.NOT_FOUND,
            "PermissionError": ErrorCategory.AUTHORIZATION,
            "MemoryError": ErrorCategory.RESOURCE,
            "RecursionError": ErrorCategory.INTERNAL,
        }
        return mapping.get(exc_name, ErrorCategory.UNKNOWN)

    def _exception_to_code(self, exc: Exception) -> str:
        """Map a standard Python exception to an error code."""
        exc_name = type(exc).__name__
        mapping: dict[str, str] = {
            "ValueError": "VALIDATION_ERROR",
            "TypeError": "VALIDATION_ERROR",
            "KeyError": "MISSING_REQUIRED_FIELD",
            "IndexError": "VALIDATION_ERROR",
            "AttributeError": "INTERNAL_ERROR",
            "NotImplementedError": "NOT_IMPLEMENTED",
            "RuntimeError": "INTERNAL_ERROR",
            "OSError": "NETWORK_ERROR",
            "IOError": "NETWORK_ERROR",
            "ConnectionError": "NETWORK_ERROR",
            "TimeoutError": "TIMEOUT",
            "FileNotFoundError": "NOT_FOUND",
            "PermissionError": "FORBIDDEN",
            "MemoryError": "MEMORY_LIMIT_EXCEEDED",
            "RecursionError": "INTERNAL_ERROR",
        }
        return mapping.get(exc_name, "INTERNAL_ERROR")


def setup_error_handling(
    app: FastAPI,
    *,
    debug: bool = False,
    include_stack_trace: bool = False,
    excluded_paths: set[str] | None = None,
) -> None:
    """Set up error handling for a FastAPI application.

    Args:
        app: The FastAPI application.
        debug: Whether to include debug information in error responses.
        include_stack_trace: Whether to include stack traces in debug mode.
        excluded_paths: Paths to exclude from error handling.
    """
    # Add middleware
    app.add_middleware(
        ErrorHandlingMiddleware,
        debug=debug,
        include_stack_trace=include_stack_trace,
        excluded_paths=excluded_paths,
    )

    # Add exception handlers
    @app.exception_handler(GRCClawException)
    async def grc_exception_handler(
        request: Request, exc: GRCClawException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

        if not exc.context.request_id:
            exc.context.request_id = request_id
        if not exc.context.trace_id:
            exc.context.trace_id = trace_id

        error_detail = exc.to_error_detail(request)
        content = error_detail.model_dump(exclude_none=True)

        headers = dict(exc.headers)
        headers["X-Request-ID"] = request_id
        headers["X-Trace-ID"] = trace_id

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

        error_detail = ErrorDetail(
            type="https://api.grc-claw.io/errors/internal-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred",
            instance=str(request.url.path),
            code="INTERNAL_ERROR",
            timestamp=datetime.now(UTC).isoformat(),
            request_id=request_id,
            trace_id=trace_id,
        )

        return JSONResponse(
            status_code=500,
            content=error_detail.model_dump(exclude_none=True),
            headers={
                "X-Request-ID": request_id,
                "X-Trace-ID": trace_id,
            },
        )
