"""Logging configuration for the tier management service."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

from tier_management.config.settings import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application.

    Sets up both structlog for structured logging and standard library
    logging with JSON formatter for production environments.
    """
    settings = get_settings()

    # Configure standard library logging
    log_handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        formatter: logging.Formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Configure structlog processors
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    if settings.is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level),
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: The logger name, typically ``__name__``.

    Returns:
        A bound structlog logger.
    """
    return structlog.get_logger(name)
