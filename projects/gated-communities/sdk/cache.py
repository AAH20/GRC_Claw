"""Redis-backed response cache for the Gated Communities SDK.

Provides caching for API responses to reduce latency and API calls.
Falls back to in-memory caching if Redis is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds.
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: Cache key.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        ...


class InMemoryCache(CacheBackend):
    """Simple in-memory cache backend.

    Args:
        default_ttl: Default time-to-live in seconds.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expires_at = time.monotonic() + ttl
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


class RedisCache(CacheBackend):
    """Redis-backed cache backend.

    Args:
        redis_url: Redis connection URL (e.g., ``redis://localhost:6379/0``).
        default_ttl: Default time-to-live in seconds.
        key_prefix: Prefix for all cache keys.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,
        key_prefix: str = "gc_sdk:",
    ) -> None:
        try:
            import redis

            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            self._available = True
        except Exception as e:
            logger.warning("Redis unavailable (%s), falling back to in-memory cache", e)
            self._redis = None
            self._available = False
            self._fallback = InMemoryCache(default_ttl)

        self._default_ttl = default_ttl
        self._key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def get(self, key: str) -> Any | None:
        if not self._available:
            return self._fallback.get(key)
        full_key = self._make_key(key)
        try:
            data = self._redis.get(full_key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning("Redis get failed: %s", e)
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self._available:
            self._fallback.set(key, value, ttl)
            return
        full_key = self._make_key(key)
        try:
            serialized = json.dumps(value, default=str)
            self._redis.setex(full_key, ttl, serialized)
        except Exception as e:
            logger.warning("Redis set failed: %s", e)

    def delete(self, key: str) -> None:
        if not self._available:
            self._fallback.delete(key)
            return
        full_key = self._make_key(key)
        try:
            self._redis.delete(full_key)
        except Exception as e:
            logger.warning("Redis delete failed: %s", e)

    def clear(self) -> None:
        if not self._available:
            self._fallback.clear()
            return
        try:
            keys = self._redis.keys(f"{self._key_prefix}*")
            if keys:
                self._redis.delete(*keys)
        except Exception as e:
            logger.warning("Redis clear failed: %s", e)


def generate_cache_key(method: str, url: str, params: dict[str, Any] | None = None) -> str:
    """Generate a deterministic cache key from request parameters.

    Args:
        method: HTTP method.
        url: Request URL.
        params: Query parameters.

    Returns:
        A unique cache key string.
    """
    key_parts = [method.upper(), url]
    if params:
        sorted_params = sorted(params.items())
        key_parts.append(json.dumps(sorted_params, sort_keys=True))
    raw = "|".join(key_parts)
    return hashlib.sha256(raw.encode()).hexdigest()


class ResponseCache:
    """High-level response cache with TTL support.

    Args:
        backend: Cache backend to use.
        default_ttl: Default TTL in seconds.
    """

    def __init__(
        self,
        backend: CacheBackend | None = None,
        default_ttl: int = 300,
    ) -> None:
        self._backend = backend or InMemoryCache(default_ttl)
        self._default_ttl = default_ttl

    def get(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any | None:
        """Get a cached response.

        Args:
            method: HTTP method.
            url: Request URL.
            params: Query parameters.

        Returns:
            Cached response data or None.
        """
        key = generate_cache_key(method, url, params)
        return self._backend.get(key)

    def set(
        self,
        method: str,
        url: str,
        data: Any,
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> None:
        """Cache a response.

        Args:
            method: HTTP method.
            url: Request URL.
            data: Response data to cache.
            params: Query parameters.
            ttl: TTL in seconds (uses default if not specified).
        """
        key = generate_cache_key(method, url, params)
        self._backend.set(key, data, ttl or self._default_ttl)

    def invalidate(self, method: str, url: str, params: dict[str, Any] | None = None) -> None:
        """Invalidate a cached response.

        Args:
            method: HTTP method.
            url: Request URL.
            params: Query parameters.
        """
        key = generate_cache_key(method, url, params)
        self._backend.delete(key)

    def clear(self) -> None:
        """Clear all cached responses."""
        self._backend.clear()
