"""Structured logging configuration for UGC Marketplace SDK."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_data", None)
        if extra:
            log_data["extra"] = extra
        return json.dumps(log_data, default=str)


def setup_logging(
    level: int = logging.INFO,
    json_format: bool = True,
) -> logging.Logger:
    """Set up structured logging for the UGC Marketplace SDK.

    Args:
        level: Logging level.
        json_format: Whether to use JSON formatting.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("ugc_marketplace")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        if json_format:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        logger.addHandler(handler)
    return logger
