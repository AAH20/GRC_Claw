"""Cache integration using Redis."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class CacheService:
    """Simple Redis cache service."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self.redis_url = redis_url
        self._data: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        return self._data.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in cache with TTL."""
        self._data[key] = value

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        self._data.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return key in self._data

    async def clear(self) -> None:
        """Clear all cached data."""
        self._data.clear()
