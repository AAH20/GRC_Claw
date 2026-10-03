"""Redis-based caching layer."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Cache:
    """Redis cache wrapper with serialization."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self.redis_url = redis_url
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        if self._redis is None:
            import redis.asyncio as redis

            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            r = await self._get_redis()
            value = await r.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            r = await self._get_redis()
            await r.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            r = await self._get_redis()
            await r.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        try:
            r = await self._get_redis()
            keys = await r.keys(pattern)
            if keys:
                return await r.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            r = await self._get_redis()
            return bool(await r.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache."""
        try:
            r = await self._get_redis()
            return await r.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache increment error: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        try:
            r = await self._get_redis()
            return bool(await r.expire(key, ttl))
        except Exception as e:
            logger.warning(f"Cache expire error: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Global cache instance
cache = Cache()
