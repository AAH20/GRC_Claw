"""Redis caching layer for performance optimization."""

from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class CacheLayer:
    """Redis-based caching layer."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self.redis_url = redis_url
        self._redis = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("cache_layer_connected")
        except ImportError:
            logger.warning("redis_not_available")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._redis:
            return False
        try:
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache by pattern."""
        if not self._redis:
            return 0
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error("cache_invalidate_error", pattern=pattern, error=str(e))
            return 0


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheLayer()
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache instance
cache = CacheLayer()
