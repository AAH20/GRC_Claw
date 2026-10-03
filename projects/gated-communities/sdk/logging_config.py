"""Structured logging configuration for the Gated Communities SDK.

Provides JSON-formatted structured logging with context propagation.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Outputs log records as JSON objects with timestamp, level, message,
    and any additional context fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from the record
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "url"):
            log_obj["url"] = record.url
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "attempt"):
            log_obj["attempt"] = record.attempt
        if hasattr(record, "max_retries"):
            log_obj["max_retries"] = record.max_retries

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


def setup_logging(
    level: int = logging.INFO,
    use_json: bool = True,
    stream: Any = None,
) -> logging.Logger:
    """Set up structured logging for the SDK.

    Args:
        level: Logging level (default: INFO).
        use_json: Whether to use JSON formatting (default: True).
        stream: Output stream (default: sys.stderr).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("gated_communities")
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(stream or sys.stderr)
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        )

    logger.addHandler(handler)
    return logger


class RequestContext:
    """Context manager for adding request context to log records.

    Args:
        logger: Logger instance.
        request_id: Unique request identifier.
        method: HTTP method.
        url: Request URL.
    """

    def __init__(
        self,
        logger: logging.Logger,
        request_id: str,
        method: str,
        url: str,
    ) -> None:
        self._logger = logger
        self._request_id = request_id
        self._method = method
        self._url = url
        self._start_time: float = 0.0

    def __enter__(self) -> RequestContext:
        self._start_time = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def log(
        self,
        level: int,
        message: str,
        *,
        status_code: int | None = None,
        attempt: int | None = None,
        max_retries: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log a message with request context.

        Args:
            level: Logging level.
            message: Log message.
            status_code: HTTP status code.
            attempt: Current retry attempt.
            max_retries: Maximum retry attempts.
            extra: Additional fields to include.
        """
        attrs: dict[str, Any] = {
            "request_id": self._request_id,
            "method": self._method,
            "url": self._url,
        }
        if status_code is not None:
            attrs["status_code"] = status_code
        if attempt is not None:
            attrs["attempt"] = attempt
        if max_retries is not None:
            attrs["max_retries"] = max_retries
        if extra:
            attrs.update(extra)

        duration_ms = (time.monotonic() - self._start_time) * 1000
        attrs["duration_ms"] = round(duration_ms, 2)

        self._logger.log(level, message, extra=attrs)
