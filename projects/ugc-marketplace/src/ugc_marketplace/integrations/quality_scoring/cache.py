"""Cache client for quality scoring."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CacheClient:
    """Simple in-memory cache client for quality scoring."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """Initialize cache client.

        Args:
            ttl_seconds: Time-to-live in seconds.
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a cache value.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._cache[key] = value
        logger.debug("Cache set", key=key)

    def get(self, key: str) -> Any | None:
        """Get a cache value.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        return self._cache.get(key)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.debug("Cache cleared")
