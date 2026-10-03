"""Structured logging configuration for the Recruitment Platform SDK.

Provides JSON-formatted structured logging with automatic serialization
of extra fields, timestamps, log levels, and correlation IDs for
distributed tracing.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_correlation_id: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Get the current correlation ID, generating one if not set.

    Returns:
        The current correlation ID string.
    """
    cid = _correlation_id.get()
    if cid is None:
        cid = str(uuid.uuid4())
        _correlation_id.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context.

    Args:
        correlation_id: The correlation ID to set.
    """
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current context."""
    _correlation_id.set(None)


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured log output.

    Formats log records as JSON objects with timestamp, level,
    logger name, message, correlation ID, and any extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that injects correlation ID and context into log records.

    Args:
        logger: The underlying logger.
        extra: Extra fields to include in every log record.
    """

    def __init__(
        self, logger: logging.Logger, extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(logger, extra or {})

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Process log record to inject context.

        Args:
            msg: The log message.
            kwargs: Keyword arguments for the log call.

        Returns:
            Tuple of (message, kwargs) with context injected.
        """
        kwargs.setdefault("extra", {})
        kwargs["extra"]["correlation_id"] = get_correlation_id()
        for key, value in self.extra.items():
            kwargs["extra"].setdefault(key, value)
        return msg, kwargs


def setup_logging(
    level: int = logging.INFO,
    stream: Any = None,
) -> logging.Logger:
    """Set up structured logging for the SDK.

    Args:
        level: Logging level (default: INFO).
        stream: Output stream (default: sys.stdout).

    Returns:
        Configured logger instance.
    """
    if stream is None:
        stream = sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredLogFormatter())
    logger = logging.getLogger("recruitment_platform_sdk")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(
    name: str = "recruitment_platform_sdk",
    **context: Any,
) -> ContextAdapter:
    """Get a logger with the specified name and context.

    Args:
        name: Logger name.
        **context: Additional context fields to include in every log record.

    Returns:
        ContextAdapter wrapping the logger.
    """
    base_logger = logging.getLogger(name)
    return ContextAdapter(base_logger, context)


def log_request(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int | None = None,
    duration_ms: float | None = None,
    **extra: Any,
) -> None:
    """Log an HTTP request with structured fields.

    Args:
        logger: Logger instance.
        method: HTTP method.
        url: Request URL.
        status_code: Response status code if available.
        duration_ms: Request duration in milliseconds if available.
        **extra: Additional fields to include.
    """
    log_data: dict[str, Any] = {
        "event": "http_request",
        "method": method,
        "url": url,
    }
    if status_code is not None:
        log_data["status_code"] = status_code
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    log_data.update(extra)
    logger.info("HTTP request", extra={"extra": log_data})


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: dict[str, Any] | None = None,
) -> None:
    """Log an error with structured context.

    Args:
        logger: Logger instance.
        error: The exception to log.
        context: Additional context fields to include.
    """
    log_data: dict[str, Any] = {
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if context:
        log_data.update(context)
    logger.error("Error occurred", extra={"extra": log_data})


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **metrics: Any,
) -> None:
    """Log performance metrics for an operation.

    Args:
        logger: Logger instance.
        operation: Name of the operation.
        duration_ms: Duration in milliseconds.
        **metrics: Additional performance metrics.
    """
    log_data: dict[str, Any] = {
        "event": "performance",
        "operation": operation,
        "duration_ms": round(duration_ms, 2),
    }
    log_data.update(metrics)
    logger.info("Performance metric", extra={"extra": log_data})
