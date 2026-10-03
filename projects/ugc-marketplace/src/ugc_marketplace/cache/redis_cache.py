"""Redis-backed caching layer for ugc-marketplace."""

import json
import logging
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache with connection pooling and proper error handling."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "ugc_marketplace:",
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        max_connections: int = 10,
    ) -> None:
        self._key_prefix = key_prefix
        self._pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,
        )
        self._client = redis.Redis(connection_pool=self._pool)

    def _prefixed(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key. Returns None if not found or on error."""
        try:
            raw = self._client.get(self._prefixed(key))
            if raw is None:
                return None
            return json.loads(raw)
        except (redis.RedisError, json.JSONDecodeError) as exc:
            logger.warning("Cache get failed for key %s: %s", key, exc)
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cached value with TTL in seconds. Returns True on success."""
        try:
            serialized = json.dumps(value)
            return bool(
                self._client.set(self._prefixed(key), serialized, ex=ttl)
            )
        except (redis.RedisError, TypeError) as exc:
            logger.warning("Cache set failed for key %s: %s", key, exc)
            return False

    def delete(self, key: str) -> bool:
        """Delete cached value by key. Returns True if key was removed."""
        try:
            return bool(self._client.delete(self._prefixed(key)))
        except redis.RedisError as exc:
            logger.warning("Cache delete failed for key %s: %s", key, exc)
            return False

    def clear(self) -> bool:
        """Clear all cache entries with this instance's key prefix."""
        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    self._client.delete(*keys)
                if cursor == 0:
                    break
            return True
        except redis.RedisError as exc:
            logger.warning("Cache clear failed: %s", exc)
            return False

    def close(self) -> None:
        """Close the connection pool."""
        try:
            self._pool.disconnect()
        except redis.RedisError:
            pass

    def __enter__(self) -> "RedisCache":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
