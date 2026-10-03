"""Cache service for content marketplace."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CacheService:
    """Simple cache service for marketplace data."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        """Initialize cache service.

        Args:
            redis_url: Redis connection URL.
        """
        self.redis_url = redis_url
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Redis client.

        Returns:
            Redis client.
        """
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(self.redis_url)
            except ImportError:
                logger.warning("redis not installed, cache disabled")
                return None
        return self._client

    async def get(self, key: str) -> Any | None:
        """Get cached value.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        client = await self._get_client()
        if client is not None:
            return await client.get(key)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set cached value.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        client = await self._get_client()
        if client is not None:
            await client.setex(key, ttl, str(value))

    async def delete(self, key: str) -> None:
        """Delete cached value.

        Args:
            key: Cache key.
        """
        client = await self._get_client()
        if client is not None:
            await client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Cache key.

        Returns:
            True if key exists.
        """
        client = await self._get_client()
        if client is not None:
            return bool(await client.exists(key))
        return False

    async def clear(self) -> None:
        """Clear all cached values."""
        client = await self._get_client()
        if client is not None:
            await client.flushdb()
