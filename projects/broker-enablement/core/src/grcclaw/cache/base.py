"""
Cache Abstraction Layer for GRC_Claw.

Defines the abstract base class and shared types for all cache implementations.
"""

from __future__ import annotations

import abc
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class CacheStrategy(str, Enum):
    """Cache eviction strategies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


class CacheLevel(str, Enum):
    """Cache hierarchy levels."""

    L1 = "l1"  # In-memory (hot)
    L2 = "l2"  # Redis (warm)
    L3 = "l3"  # Disk (cold)


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with metadata."""

    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0  # 0 means no expiration
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        return self.expires_at > 0 and time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        if self.expires_at <= 0:
            return float("inf")
        return max(0.0, self.expires_at - time.time())

    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheConfig:
    """Configuration for cache instances."""

    default_ttl: int = 300  # seconds
    max_size: int = 10_000  # max entries
    strategy: CacheStrategy = CacheStrategy.LRU
    namespace: str = "grcclaw"
    key_prefix: str = ""
    serializer: str = "json"  # json, pickle, msgpack
    compression: bool = False
    compression_threshold: int = 1024  # bytes


class CacheError(Exception):
    """Base exception for cache operations."""

    pass


class CacheConnectionError(CacheError):
    """Raised when cache backend is unreachable."""

    pass


class CacheSerializationError(CacheError):
    """Raised when serialization/deserialization fails."""

    pass


class CacheKeyError(CacheError):
    """Raised when a cache key is invalid or missing."""

    pass


class CacheBackend(abc.ABC, Generic[T]):
    """
    Abstract base class for all cache backends.

    Provides a unified interface for get, set, delete, and invalidate
    operations across different cache implementations.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._initialized = False

    @abc.abstractmethod
    async def connect(self) -> None:
        """Establish connection to the cache backend."""
        ...

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the cache backend."""
        ...

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Retrieve a value from cache. Returns None if not found or expired."""
        ...

    @abc.abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Store a value in cache with optional TTL and tags."""
        ...

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove a key from cache. Returns True if key existed."""
        ...

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        ...

    @abc.abstractmethod
    async def clear(self) -> bool:
        """Clear all entries in the cache."""
        ...

    @abc.abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Return keys matching a glob-style pattern."""
        ...

    @abc.abstractmethod
    async def ttl(self, key: str) -> float:
        """Return remaining TTL for a key. -1 if no expiry, -2 if missing."""
        ...

    @abc.abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set/update TTL for an existing key."""
        ...

    @abc.abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a numeric value."""
        ...

    @abc.abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, T]:
        """Retrieve multiple values in one round-trip."""
        ...

    @abc.abstractmethod
    async def set_many(
        self,
        mapping: dict[str, T],
        ttl: Optional[int] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Store multiple values in one round-trip."""
        ...

    @abc.abstractmethod
    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns count of deleted keys."""
        ...

    @abc.abstractmethod
    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate all entries matching any of the given tags."""
        ...

    @abc.abstractmethod
    async def flush(self) -> bool:
        """Flush all data (dangerous - use with caution)."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return health status and statistics."""
        ...

    @abc.abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Return cache statistics (hits, misses, hit_rate, etc.)."""
        ...

    def _make_key(self, key: str) -> str:
        """Build a fully-qualified key with namespace and prefix."""
        parts = [self.config.namespace]
        if self.config.key_prefix:
            parts.append(self.config.key_prefix)
        parts.append(key)
        return ":".join(parts)

    def _strip_key(self, full_key: str) -> str:
        """Strip namespace and prefix from a full key."""
        prefix = self._make_key("")
        if full_key.startswith(prefix):
            return full_key[len(prefix):]
        return full_key

    def _serialize(self, value: T) -> bytes:
        """Serialize a value to bytes."""
        if self.config.serializer == "json":
            return json.dumps(value, default=str).encode("utf-8")
        elif self.config.serializer == "pickle":
            import pickle
            return pickle.dumps(value)
        else:
            raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")

    def _deserialize(self, data: bytes) -> T:
        """Deserialize bytes to a value."""
        if self.config.serializer == "json":
            return json.loads(data.decode("utf-8"))
        elif self.config.serializer == "pickle":
            import pickle
            return pickle.loads(data)
        else:
            raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")

    def _hash_key(self, key: str) -> str:
        """Create a deterministic hash of a key for tag indexing."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def _is_connected(self) -> bool:
        return self._initialized

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class CacheDecorator:
    """
    Decorator for caching function results.

    Usage:
        @CacheDecorator(cache_backend, ttl=60, key_prefix="my_func")
        async def expensive_function(x, y):
            return x + y
    """

    def __init__(
        self,
        backend: CacheBackend,
        ttl: Optional[int] = None,
        key_prefix: str = "",
        tags: Optional[list[str]] = None,
        key_builder: Optional[Callable[..., str]] = None,
    ):
        self.backend = backend
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.tags = tags or []
        self.key_builder = key_builder

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            if self.key_builder:
                cache_key = self.key_builder(*args, **kwargs)
            else:
                cache_key = self._default_key(func, *args, **kwargs)

            # Try cache first
            cached = await self.backend.get(cache_key)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await self.backend.set(cache_key, result, ttl=self.ttl, tags=self.tags)
            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def _default_key(self, func: Callable, *args, **kwargs) -> str:
        """Build a default cache key from function name and arguments."""
        key_parts = [self.key_prefix or func.__name__]
        key_parts.extend(str(a) for a in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)


class CacheKeyBuilder:
    """Utility for building consistent cache keys."""

    @staticmethod
    def from_parts(*parts: Any, separator: str = ":") -> str:
        """Build a key from parts, converting each to string."""
        return separator.join(str(p) for p in parts if p is not None)

    @staticmethod
    def from_dict(data: dict[str, Any], prefix: str = "") -> str:
        """Build a key from a sorted dict."""
        items = sorted(data.items())
        key = ":".join(f"{k}={v}" for k, v in items)
        return f"{prefix}:{key}" if prefix else key

    @staticmethod
    def from_object(obj: Any, prefix: str = "") -> str:
        """Build a key from an object's attributes."""
        if hasattr(obj, "__dict__"):
            data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return CacheKeyBuilder.from_dict(data, prefix)
        return f"{prefix}:{id(obj)}" if prefix else str(id(obj))

    @staticmethod
    def hash_key(*parts: Any) -> str:
        """Build a SHA-256 hash key from parts."""
        raw = ":".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
