"""Cache integration client for tier management."""
from __future__ import annotations

from typing import Any

from tier_management.config.logging_config import get_logger
from tier_management.config.settings import get_settings

logger = get_logger(__name__)


class CacheClient:
    """Client for cache operations.

    Provides async caching for frequently accessed tier
    management data. Supports Redis via redis-py.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the cache client.

        Args:
            settings: Application settings. Uses global settings if None.
        """
        self.settings = settings or get_settings()
        self._redis: Any = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("cache_connected")
        except ImportError:
            logger.warning("redis_not_available", detail="Cache features disabled")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("cache_disconnected")

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/unavailable.
        """
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.

        Returns:
            True if successful, False otherwise.
        """
        if not self._redis:
            return False
        try:
            import json

            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: Cache key.

        Returns:
            True if key was deleted, False otherwise.
        """
        if not self._redis:
            return False
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error("cache_delete_failed", key=key, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check cache connectivity.

        Returns:
            True if cache is reachable, False otherwise.
        """
        if not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error("cache_health_check_failed", error=str(e))
            return False
