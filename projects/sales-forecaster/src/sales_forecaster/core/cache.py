"""Caching utilities for the Sales Forecaster."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from sales_forecaster.core import get_settings

F = TypeVar("F", bound=Callable[..., Any])


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Get a value from cache if not expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        import time

        if key in self._cache:
            expiry, value = self._cache[key]
            if time.time() < expiry:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.
        """
        import time

        self._cache[key] = (time.time() + ttl_seconds, value)

    def delete(self, key: str) -> None:
        """Delete a key from cache.

        Args:
            key: Cache key to delete.
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


_cache = SimpleCache()


def cached(ttl_seconds: int = 300) -> Callable[[F], F]:
    """Decorator to cache function results.

    Args:
        ttl_seconds: Cache TTL in seconds.

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.sha256(
                json.dumps(key_parts, default=str).encode()
            ).hexdigest()

            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def get_redis_client() -> Any | None:
    """Get a Redis client instance.

    Returns:
        Redis client or None if Redis is not available.
    """
    try:
        import redis.asyncio as aioredis

        settings = get_settings()
        return aioredis.from_url(settings.redis_url, decode_responses=True)
    except ImportError:
        return None
