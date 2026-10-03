"""Structured logging configuration for the Recruitment Platform SDK.

Provides JSON-formatted structured logging with automatic serialization
of extra fields, timestamps, and log levels.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured log output.

    Formats log records as JSON objects with timestamp, level,
    logger name, message, and any extra fields.
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
        }
        # Add extra fields from the record
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


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
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str = "recruitment_platform_sdk") -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
