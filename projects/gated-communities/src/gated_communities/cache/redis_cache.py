"""Redis-based caching layer for gated communities."""

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
        key_prefix: str = "gated_communities:",
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        max_connections: int = 10,
    ):
        self._key_prefix = key_prefix
        self._pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            max_connections=max_connections,
            decode_responses=True,
        )
        self._client = redis.Redis(connection_pool=self._pool)

    def _make_key(self, key: str) -> str:
        """Prefix a key with the namespace prefix."""
        return f"{self._key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key. Returns None if not found or on error."""
        try:
            raw = self._client.get(self._make_key(key))
            if raw is None:
                return None
            return json.loads(raw)
        except (redis.RedisError, json.JSONDecodeError) as exc:
            logger.warning("Cache get failed for key %s: %s", key, exc)
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set a cached value with TTL in seconds. Returns True on success."""
        try:
            serialized = json.dumps(value)
            return self._client.setex(self._make_key(key), ttl, serialized)
        except (redis.RedisError, TypeError) as exc:
            logger.warning("Cache set failed for key %s: %s", key, exc)
            return False

    def delete(self, key: str) -> bool:
        """Delete a cached value by key. Returns True if key was removed."""
        try:
            return self._client.delete(self._make_key(key)) > 0
        except redis.RedisError as exc:
            logger.warning("Cache delete failed for key %s: %s", key, exc)
            return False

    def clear(self) -> bool:
        """Clear all cached values with this prefix. Returns True on success."""
        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=100)
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

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
