"""Redis integration module."""

from __future__ import annotations

import ast
from typing import Any

import redis.asyncio as redis

from fraud_detection.config.logging_config import get_logger
from fraud_detection.config.settings import get_settings

logger = get_logger(__name__)

_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client.

    Returns:
        Redis client instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    """Close Redis connection."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Redis connection closed")


async def cache_transaction(transaction_id: str, data: dict[str, Any], ttl: int = 3600) -> None:
    """Cache transaction data in Redis.

    Args:
        transaction_id: Transaction identifier.
        data: Data to cache.
        ttl: Time to live in seconds.
    """
    client = await get_redis_client()
    await client.setex(f"transaction:{transaction_id}", ttl, str(data))


async def get_cached_transaction(transaction_id: str) -> dict[str, Any] | None:
    """Get cached transaction data.

    Args:
        transaction_id: Transaction identifier.

    Returns:
        Cached data if found, None otherwise.
    """
    client = await get_redis_client()
    data = await client.get(f"transaction:{transaction_id}")
    if data:
        return ast.literal_eval(data)
    return None
