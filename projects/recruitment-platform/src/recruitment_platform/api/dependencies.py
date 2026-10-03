"""Shared API dependencies."""

from __future__ import annotations

from typing import Any

from recruitment_platform.config.settings import get_settings


async def get_db() -> Any:
    """Get database session dependency.

    Yields:
        Database session.
    """
    # Placeholder for actual DB session management
    yield None


async def get_cache() -> Any:
    """Get cache client dependency.

    Yields:
        Cache client.
    """
    # Placeholder for actual cache client
    yield None


def get_settings_dependency() -> Any:
    """Get application settings.

    Returns:
        Application settings.
    """
    return get_settings()
