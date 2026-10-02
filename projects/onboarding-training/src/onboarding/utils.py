"""Shared utilities for the Onboarding & Training platform."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from onboarding.config import get_settings


def generate_id(prefix: str) -> str:
    """Generate a unique identifier with the given prefix.

    Args:
        prefix: A short prefix for the ID (e.g. ``"course"``, ``"learner"``).

    Returns:
        A unique ID string like ``"course_01J9Z3..."``.
    """
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger bound to the given name.

    Args:
        name: The logger name, typically ``__name__``.

    Returns:
        A configured structlog logger.
    """
    settings = get_settings()
    return structlog.get_logger(name).bind(
        app_env=settings.app_env,
        log_level=settings.log_level,
    )


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to a maximum length, appending an ellipsis if needed.

    Args:
        text: The text to truncate.
        max_length: Maximum allowed length.

    Returns:
        The truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dict, returning a default if missing.

    Args:
        data: The dictionary to query.
        key: The key to look up.
        default: Value to return if key is missing.

    Returns:
        The value at key, or default.
    """
    return data.get(key, default)
