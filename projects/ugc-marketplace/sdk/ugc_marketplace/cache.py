"""Redis-backed response cache for UGC Marketplace SDK."""

from __future__ import annotations

import json
import time
from typing import Any


class RedisCache:
    """Redis-backed cache with in-memory fallback.

    Args:
        redis_url: Redis connection URL.
        ttl: Default TTL in seconds for cached entries.
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", ttl: int = 300
    ) -> None:
        self._redis_url = redis_url
        self._ttl = ttl
        self._redis: Any = None
        self._memory_cache: dict[str, Any] = {}
        self._memory_expiry: dict[str, float] = {}

    def _get_redis(self) -> Any | None:
        if self._redis is None:
            try:
                import redis

                self._redis = redis.from_url(self._redis_url)
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        r = self._get_redis()
        if r:
            try:
                val = r.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        if key in self._memory_cache:
            if time.time() < self._memory_expiry.get(key, 0):
                return self._memory_cache[key]
            self._memory_cache.pop(key, None)
            self._memory_expiry.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: TTL in seconds (overrides default).
        """
        ttl = ttl or self._ttl
        r = self._get_redis()
        if r:
            try:
                r.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:
                pass
        self._memory_cache[key] = value
        self._memory_expiry[key] = time.time() + ttl

    def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: Cache key.
        """
        r = self._get_redis()
        if r:
            try:
                r.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        self._memory_expiry.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        r = self._get_redis()
        if r:
            try:
                r.flushdb()
            except Exception:
                pass
        self._memory_cache.clear()
        self._memory_expiry.clear()


class AsyncRedisCache:
    """Asyncio Redis-backed cache with in-memory fallback.

    Args:
        redis_url: Redis connection URL.
        ttl: Default TTL in seconds for cached entries.
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", ttl: int = 300
    ) -> None:
        self._redis_url = redis_url
        self._ttl = ttl
        self._redis: Any = None
        self._memory_cache: dict[str, Any] = {}
        self._memory_expiry: dict[str, float] = {}

    async def _get_redis(self) -> Any | None:
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(self._redis_url)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        r = await self._get_redis()
        if r:
            try:
                val = await r.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        if key in self._memory_cache:
            if time.time() < self._memory_expiry.get(key, 0):
                return self._memory_cache[key]
            self._memory_cache.pop(key, None)
            self._memory_expiry.pop(key, None)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: TTL in seconds (overrides default).
        """
        ttl = ttl or self._ttl
        r = await self._get_redis()
        if r:
            try:
                await r.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:
                pass
        self._memory_cache[key] = value
        self._memory_expiry[key] = time.time() + ttl

    async def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: Cache key.
        """
        r = await self._get_redis()
        if r:
            try:
                await r.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        self._memory_expiry.pop(key, None)

    async def clear(self) -> None:
        """Clear all cached values."""
        r = await self._get_redis()
        if r:
            try:
                await r.flushdb()
            except Exception:
                pass
        self._memory_cache.clear()
        self._memory_expiry.clear()
