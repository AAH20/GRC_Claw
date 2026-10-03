"""Redis-backed response cache for the Recruitment Platform SDK.

Provides a caching layer that stores API responses in Redis with
automatic fallback to in-memory caching when Redis is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-backed response cache with in-memory fallback.

    Caches API responses in Redis with a configurable TTL. If Redis
    is not available, falls back to an in-memory dictionary with
    the same TTL behavior.

    Args:
        redis_url: Redis connection URL (default: redis://localhost:6379).
        ttl: Cache TTL in seconds (default: 300).
        prefix: Key prefix for cache entries (default: rpc:cache:).

    Example:
        >>> cache = RedisCache(ttl=60)
        >>> cache.set("GET", "/api/v1/health", None, {"status": "healthy"})
        >>> cache.get("GET", "/api/v1/health", None)
        {'status': 'healthy'}
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 300,
        prefix: str = "rpc:cache:",
    ) -> None:
        self._ttl: int = ttl
        self._prefix: str = prefix
        self._redis: Any = None
        self._available: bool = False
        self._memory_cache: dict[str, tuple[float, Any]] = {}
        self._connect(redis_url)

    def _connect(self, redis_url: str) -> None:
        """Attempt to connect to Redis."""
        try:
            import redis

            self._redis = redis.from_url(redis_url)
            self._redis.ping()
            self._available = True
            logger.info("Redis cache connected", extra={"url": redis_url})
        except Exception as e:
            self._available = False
            self._redis = None
            logger.warning(
                "Redis unavailable, using in-memory cache",
                extra={"error": str(e)},
            )

    @property
    def available(self) -> bool:
        """Whether Redis is available."""
        return self._available

    @property
    def ttl(self) -> int:
        """Cache TTL in seconds."""
        return self._ttl

    def _make_key(self, method: str, path: str, params: dict[str, Any] | None) -> str:
        """Generate a cache key from request parameters."""
        data = (
            f"{method}:{path}:{json.dumps(params or {}, sort_keys=True, default=str)}"
        )
        return f"{self._prefix}{hashlib.sha256(data.encode()).hexdigest()}"

    def get(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> Any | None:
        """Retrieve a cached response.

        Args:
            method: HTTP method of the original request.
            path: API path of the original request.
            params: Query parameters of the original request.

        Returns:
            The cached response data, or None if not found or expired.
        """
        key = self._make_key(method, path, params)
        if self._available and self._redis is not None:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning("Redis get failed", extra={"error": str(e)})
                self._available = False
        # Fallback to memory cache
        return self._memory_get(key)

    def _memory_get(self, key: str) -> Any | None:
        """Get from in-memory cache."""
        if key in self._memory_cache:
            expiry, value = self._memory_cache[key]
            if time.time() < expiry:
                return value
            del self._memory_cache[key]
        return None

    def set(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        value: Any,
    ) -> None:
        """Store a response in the cache.

        Args:
            method: HTTP method of the original request.
            path: API path of the original request.
            params: Query parameters of the original request.
            value: Response data to cache.
        """
        key = self._make_key(method, path, params)
        if self._available and self._redis is not None:
            try:
                self._redis.setex(key, self._ttl, json.dumps(value, default=str))
                return
            except Exception as e:
                logger.warning("Redis set failed", extra={"error": str(e)})
                self._available = False
        # Fallback to memory cache
        self._memory_cache[key] = (time.time() + self._ttl, value)

    def delete(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> None:
        """Delete a cached response.

        Args:
            method: HTTP method of the original request.
            path: API path of the original request.
            params: Query parameters of the original request.
        """
        key = self._make_key(method, path, params)
        if self._available and self._redis is not None:
            try:
                self._redis.delete(key)
            except Exception as e:
                logger.warning("Redis delete failed", extra={"error": str(e)})
        self._memory_cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached responses."""
        if self._available and self._redis is not None:
            try:
                keys = self._redis.keys(f"{self._prefix}*")
                if keys:
                    self._redis.delete(*keys)
            except Exception as e:
                logger.warning("Redis clear failed", extra={"error": str(e)})
        self._memory_cache.clear()

    def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            with contextlib.suppress(Exception):
                self._redis.close()
            self._redis = None
            self._available = False

    def __enter__(self) -> RedisCache:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and close connection."""
        self.close()
