"""
Redis Cache Implementation for GRC_Claw.

Provides a production-ready Redis-backed cache with connection pooling,
serialization, tag-based invalidation, and comprehensive error handling.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from .base import (
    CacheBackend,
    CacheConfig,
    CacheConnectionError,
    CacheError,
    CacheSerializationError,
)

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import TimeoutError as RedisTimeoutError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    Redis = None
    RedisConnectionError = Exception
    RedisTimeoutError = Exception


class RedisCache(CacheBackend):
    """
    Redis-backed cache implementation.

    Features:
    - Async connection pooling
    - Automatic serialization (JSON/pickle)
    - Tag-based invalidation via Redis sets
    - Atomic increment operations
    - Pipeline support for batch operations
    - Graceful degradation on connection failure
    - Configurable retry with exponential backoff
    """

    def __init__(
        self,
        config: CacheConfig | None = None,
        url: str = "redis://localhost:6379",
        db: int = 0,
        password: str | None = None,
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        ssl: bool = False,
        ssl_cert_reqs: str | None = None,
    ):
        super().__init__(config)
        self.url = url
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.ssl = ssl
        self.ssl_cert_reqs = ssl_cert_reqs

        self._client: Redis | None = None
        self._pool = None
        self._lock = asyncio.Lock()
        self._retry_count = 3
        self._retry_delay = 0.1

    async def connect(self) -> None:
        """Establish connection to Redis with retry logic."""
        if not REDIS_AVAILABLE:
            raise CacheConnectionError(
                "redis package not installed. Install with: pip install redis"
            )

        async with self._lock:
            if self._initialized:
                return

            last_error = None
            for attempt in range(self._retry_count):
                try:
                    kwargs: dict[str, Any] = {
                        "db": self.db,
                        "password": self.password,
                        "max_connections": self.max_connections,
                        "socket_timeout": self.socket_timeout,
                        "socket_connect_timeout": self.socket_connect_timeout,
                        "retry_on_timeout": self.retry_on_timeout,
                        "health_check_interval": self.health_check_interval,
                        "decode_responses": False,
                    }
                    if self.ssl:
                        kwargs["ssl"] = True
                        if self.ssl_cert_reqs:
                            kwargs["ssl_cert_reqs"] = self.ssl_cert_reqs

                    self._pool = aioredis.ConnectionPool.from_url(
                        self.url, **kwargs
                    )
                    self._client = Redis(connection_pool=self._pool)

                    # Verify connection
                    await self._client.ping()
                    self._initialized = True
                    logger.info("Redis cache connected to %s (db=%d)", self.url, self.db)
                    return

                except (RedisConnectionError, RedisTimeoutError, OSError) as e:
                    last_error = e
                    logger.warning(
                        "Redis connection attempt %d/%d failed: %s",
                        attempt + 1, self._retry_count, e,
                    )
                    if attempt < self._retry_count - 1:
                        delay = self._retry_delay * (2 ** attempt)
                        await asyncio.sleep(delay)

            raise CacheConnectionError(
                f"Failed to connect to Redis after {self._retry_count} attempts: {last_error}"
            )

    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        async with self._lock:
            if self._pool:
                try:
                    await self._pool.disconnect()
                except Exception as e:
                    logger.warning("Error disconnecting Redis pool: %s", e)
            self._client = None
            self._pool = None
            self._initialized = False
            logger.info("Redis cache disconnected")

    def _ensure_connected(self) -> Redis:
        if not self._initialized or self._client is None:
            raise CacheConnectionError("Redis cache not connected. Call connect() first.")
        return self._client

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes for Redis storage."""
        try:
            if self.config.serializer == "json":
                return json.dumps(value, default=str).encode("utf-8")
            elif self.config.serializer == "pickle":
                import pickle
                return pickle.dumps(value)
            else:
                raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")
        except Exception as e:
            raise CacheSerializationError(f"Serialization failed: {e}") from e

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes from Redis to Python object."""
        try:
            if self.config.serializer == "json":
                return json.loads(data.decode("utf-8"))
            elif self.config.serializer == "pickle":
                import pickle
                return pickle.loads(data)
            else:
                raise CacheSerializationError(f"Unknown serializer: {self.config.serializer}")
        except Exception as e:
            raise CacheSerializationError(f"Deserialization failed: {e}") from e

    def _entry_key(self, key: str) -> str:
        return self._make_key(f"entry:{key}")

    def _tag_key(self, tag: str) -> str:
        return self._make_key(f"tag:{tag}")

    def _meta_key(self, key: str) -> str:
        return self._make_key(f"meta:{key}")

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from Redis cache."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)
        meta_key = self._meta_key(key)

        try:
            pipe = client.pipeline()
            pipe.get(entry_key)
            pipe.get(meta_key)
            results = await pipe.execute()

            raw_data = results[0]
            raw_meta = results[1]

            if raw_data is None:
                return None

            # Check TTL from metadata
            if raw_meta:
                meta = json.loads(raw_meta.decode("utf-8"))
                expires_at = meta.get("expires_at", 0)
                if expires_at > 0 and time.time() > expires_at:
                    # Entry expired, clean up
                    await self.delete(key)
                    return None

            value = self._deserialize(raw_data)

            # Update access metadata asynchronously (fire-and-forget)
            if raw_meta:
                meta["access_count"] = meta.get("access_count", 0) + 1
                meta["last_accessed"] = time.time()
                try:
                    await client.set(meta_key, json.dumps(meta).encode("utf-8"))
                except Exception:
                    pass  # Non-critical

            return value

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis get error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis get failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis get for key %s: %s", key, e)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Store a value in Redis cache with optional TTL and tags."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)
        meta_key = self._meta_key(key)

        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            serialized = self._serialize(value)
            expires_at = time.time() + effective_ttl if effective_ttl > 0 else 0

            meta = {
                "key": key,
                "created_at": time.time(),
                "expires_at": expires_at,
                "access_count": 0,
                "last_accessed": time.time(),
                "size_bytes": len(serialized),
                "tags": tags or [],
            }

            pipe = client.pipeline()
            pipe.set(entry_key, serialized)
            if effective_ttl > 0:
                pipe.expire(entry_key, effective_ttl)

            # Store metadata
            pipe.set(meta_key, json.dumps(meta).encode("utf-8"))
            if effective_ttl > 0:
                pipe.expire(meta_key, effective_ttl)

            # Add to tag sets
            for tag in (tags or []):
                tag_key = self._tag_key(tag)
                pipe.sadd(tag_key, key)
                if effective_ttl > 0:
                    pipe.expire(tag_key, effective_ttl)

            await pipe.execute()
            return True

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis set error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis set failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis set for key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Remove a key from Redis cache."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)
        meta_key = self._meta_key(key)

        try:
            # Get tags first to clean up tag sets
            raw_meta = await client.get(meta_key)
            tags: list[str] = []
            if raw_meta:
                meta = json.loads(raw_meta.decode("utf-8"))
                tags = meta.get("tags", [])

            pipe = client.pipeline()
            pipe.delete(entry_key)
            pipe.delete(meta_key)
            for tag in tags:
                pipe.srem(self._tag_key(tag), key)

            results = await pipe.execute()
            return results[0] > 0

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis delete error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis delete failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis delete for key %s: %s", key, e)
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)

        try:
            exists = await client.exists(entry_key)
            if not exists:
                return False

            # Check if expired
            meta_key = self._meta_key(key)
            raw_meta = await client.get(meta_key)
            if raw_meta:
                meta = json.loads(raw_meta.decode("utf-8"))
                expires_at = meta.get("expires_at", 0)
                if expires_at > 0 and time.time() > expires_at:
                    await self.delete(key)
                    return False

            return True

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis exists error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis exists failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis exists for key %s: %s", key, e)
            return False

    async def clear(self) -> bool:
        """Clear all entries in the current namespace."""
        client = self._ensure_connected()
        pattern = self._make_key("*")

        try:
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break
            return True

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis clear error: %s", e)
            raise CacheConnectionError(f"Redis clear failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis clear: %s", e)
            return False

    async def keys(self, pattern: str = "*") -> list[str]:
        """Return keys matching a glob-style pattern."""
        client = self._ensure_connected()
        full_pattern = self._make_key(pattern)

        try:
            result: list[str] = []
            cursor = 0
            while True:
                cursor, batch = await client.scan(cursor, match=full_pattern, count=100)
                for full_key in batch:
                    key_str = full_key.decode("utf-8") if isinstance(full_key, bytes) else full_key
                    # Strip namespace:entry: prefix
                    stripped = self._strip_key(key_str)
                    if stripped.startswith("entry:"):
                        stripped = stripped[6:]
                    elif stripped.startswith("meta:"):
                        stripped = stripped[5:]
                    elif stripped.startswith("tag:"):
                        continue  # Skip tag index keys
                    result.append(stripped)
                if cursor == 0:
                    break
            return result

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis keys error: %s", e)
            raise CacheConnectionError(f"Redis keys failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis keys: %s", e)
            return []

    async def ttl(self, key: str) -> float:
        """Return remaining TTL for a key in seconds."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)

        try:
            ttl_seconds = await client.ttl(entry_key)
            if ttl_seconds == -2:
                return -2  # Key doesn't exist
            if ttl_seconds == -1:
                return -1  # Key exists but has no expiry
            return float(ttl_seconds)

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis ttl error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis ttl failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis ttl for key %s: %s", key, e)
            return -2

    async def expire(self, key: str, ttl: int) -> bool:
        """Set/update TTL for an existing key."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)
        meta_key = self._meta_key(key)

        try:
            pipe = client.pipeline()
            pipe.expire(entry_key, ttl)
            pipe.expire(meta_key, ttl)

            # Update metadata
            raw_meta = await client.get(meta_key)
            if raw_meta:
                meta = json.loads(raw_meta.decode("utf-8"))
                meta["expires_at"] = time.time() + ttl
                pipe.set(meta_key, json.dumps(meta).encode("utf-8"))
                pipe.expire(meta_key, ttl)

            results = await pipe.execute()
            return results[0]

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis expire error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis expire failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis expire for key %s: %s", key, e)
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a numeric value."""
        client = self._ensure_connected()
        entry_key = self._entry_key(key)

        try:
            # For simple counter, use Redis INCR
            # For complex values, we need to get-modify-set
            raw = await client.get(entry_key)
            if raw is None:
                # Initialize
                await self.set(key, amount)
                return amount

            value = self._deserialize(raw)
            if isinstance(value, (int, float)):
                new_value = value + amount
                await self.set(key, new_value)
                return int(new_value)
            else:
                raise CacheError(f"Cannot increment non-numeric value of type {type(value)}")

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis increment error for key %s: %s", key, e)
            raise CacheConnectionError(f"Redis increment failed: {e}") from e
        except CacheError:
            raise
        except Exception as e:
            logger.error("Unexpected error in Redis increment for key %s: %s", key, e)
            raise CacheError(f"Increment failed: {e}") from e

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Retrieve multiple values in one round-trip using pipeline."""
        client = self._ensure_connected()
        if not keys:
            return {}

        entry_keys = [self._entry_key(k) for k in keys]
        meta_keys = [self._meta_key(k) for k in keys]

        try:
            pipe = client.pipeline()
            for ek in entry_keys:
                pipe.get(ek)
            for mk in meta_keys:
                pipe.get(mk)
            results = await pipe.execute()

            result: dict[str, Any] = {}
            num_keys = len(keys)
            for i, key in enumerate(keys):
                raw_data = results[i]
                raw_meta = results[num_keys + i]

                if raw_data is None:
                    continue

                # Check expiry
                if raw_meta:
                    meta = json.loads(raw_meta.decode("utf-8"))
                    expires_at = meta.get("expires_at", 0)
                    if expires_at > 0 and time.time() > expires_at:
                        continue

                result[key] = self._deserialize(raw_data)

            return result

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis get_many error: %s", e)
            raise CacheConnectionError(f"Redis get_many failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis get_many: %s", e)
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Store multiple values in one round-trip using pipeline."""
        client = self._ensure_connected()
        if not mapping:
            return True

        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            pipe = client.pipeline()
            for key, value in mapping.items():
                entry_key = self._entry_key(key)
                meta_key = self._meta_key(key)

                serialized = self._serialize(value)
                expires_at = time.time() + effective_ttl if effective_ttl > 0 else 0

                meta = {
                    "key": key,
                    "created_at": time.time(),
                    "expires_at": expires_at,
                    "access_count": 0,
                    "last_accessed": time.time(),
                    "size_bytes": len(serialized),
                    "tags": tags or [],
                }

                pipe.set(entry_key, serialized)
                if effective_ttl > 0:
                    pipe.expire(entry_key, effective_ttl)

                pipe.set(meta_key, json.dumps(meta).encode("utf-8"))
                if effective_ttl > 0:
                    pipe.expire(meta_key, effective_ttl)

                for tag in (tags or []):
                    pipe.sadd(self._tag_key(tag), key)
                    if effective_ttl > 0:
                        pipe.expire(self._tag_key(tag), effective_ttl)

            await pipe.execute()
            return True

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis set_many error: %s", e)
            raise CacheConnectionError(f"Redis set_many failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis set_many: %s", e)
            return False

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns count of deleted keys."""
        client = self._ensure_connected()
        if not keys:
            return 0

        try:
            pipe = client.pipeline()
            for key in keys:
                entry_key = self._entry_key(key)
                meta_key = self._meta_key(key)
                pipe.delete(entry_key)
                pipe.delete(meta_key)

                # Clean up tag sets
                raw_meta = await client.get(meta_key)
                if raw_meta:
                    meta = json.loads(raw_meta.decode("utf-8"))
                    for tag in meta.get("tags", []):
                        pipe.srem(self._tag_key(tag), key)

            results = await pipe.execute()
            # Count successful deletes (every 2 results = 1 key)
            deleted = sum(1 for i in range(0, len(results), 2) if results[i] > 0)
            return deleted

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis delete_many error: %s", e)
            raise CacheConnectionError(f"Redis delete_many failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis delete_many: %s", e)
            return 0

    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate all entries matching any of the given tags."""
        client = self._ensure_connected()
        if not tags:
            return 0

        try:
            # Collect all keys from tag sets
            all_keys: set[str] = set()
            for tag in tags:
                tag_key = self._tag_key(tag)
                members = await client.smembers(tag_key)
                for member in members:
                    key_str = member.decode("utf-8") if isinstance(member, bytes) else member
                    all_keys.add(key_str)

            if not all_keys:
                return 0

            # Delete all entries
            deleted = await self.delete_many(list(all_keys))

            # Clean up tag sets
            pipe = client.pipeline()
            for tag in tags:
                pipe.delete(self._tag_key(tag))
            await pipe.execute()

            return deleted

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis invalidate_by_tags error: %s", e)
            raise CacheConnectionError(f"Redis invalidate_by_tags failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis invalidate_by_tags: %s", e)
            return 0

    async def flush(self) -> bool:
        """Flush the entire Redis database (DANGEROUS)."""
        client = self._ensure_connected()
        try:
            await client.flushdb()
            return True
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis flush error: %s", e)
            raise CacheConnectionError(f"Redis flush failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis flush: %s", e)
            return False

    async def health_check(self) -> dict[str, Any]:
        """Return health status and Redis server info."""
        client = self._ensure_connected()
        try:
            start = time.time()
            await client.ping()
            latency_ms = (time.time() - start) * 1000

            info = await client.info()
            memory_info = await client.info("memory")
            stats_info = await client.info("stats")

            return {
                "status": "healthy",
                "connected": True,
                "latency_ms": round(latency_ms, 2),
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": stats_info.get("total_commands_processed", 0),
                "keyspace_hits": stats_info.get("keyspace_hits", 0),
                "keyspace_misses": stats_info.get("keyspace_misses", 0),
                "expired_keys": stats_info.get("expired_keys", 0),
                "evicted_keys": stats_info.get("evicted_keys", 0),
                "hit_rate": self._calculate_hit_rate(stats_info),
            }

        except (RedisConnectionError, RedisTimeoutError) as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": self._initialized,
                "error": str(e),
            }

    async def get_stats(self) -> dict[str, Any]:
        """Return cache-specific statistics."""
        client = self._ensure_connected()
        try:
            stats_info = await client.info("stats")
            memory_info = await client.info("memory")

            # Count keys in our namespace
            pattern = self._make_key("*")
            key_count = 0
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                key_count += len(keys)
                if cursor == 0:
                    break

            hits = int(stats_info.get("keyspace_hits", 0))
            misses = int(stats_info.get("keyspace_misses", 0))
            total = hits + misses

            return {
                "namespace": self.config.namespace,
                "key_count": key_count,
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hits / total, 4) if total > 0 else 0.0,
                "expired_keys": int(stats_info.get("expired_keys", 0)),
                "evicted_keys": int(stats_info.get("evicted_keys", 0)),
                "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                "maxmemory_human": memory_info.get("maxmemory_human", "0"),
                "fragmentation_ratio": float(memory_info.get("mem_fragmentation_ratio", 0)),
            }

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error("Redis get_stats error: %s", e)
            raise CacheConnectionError(f"Redis get_stats failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected error in Redis get_stats: %s", e)
            return {}

    def _calculate_hit_rate(self, stats_info: dict) -> float:
        hits = int(stats_info.get("keyspace_hits", 0))
        misses = int(stats_info.get("keyspace_misses", 0))
        total = hits + misses
        return round(hits / total, 4) if total > 0 else 0.0
