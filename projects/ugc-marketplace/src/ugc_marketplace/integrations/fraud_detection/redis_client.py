"""Redis client integration for fraud detection."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_client: Any = None


async def get_redis_client() -> Any:
    """Get or create Redis client.

    Returns:
        Redis client instance.
    """
    global _client
    if _client is None:
        try:
            import redis.asyncio as redis

            from ugc_marketplace.config import get_settings

            settings = get_settings()
            _client = redis.from_url(settings.redis_url)
            logger.info("Redis client created")
        except ImportError:
            logger.warning("redis not installed, Redis integration disabled")
            return None
    return _client


async def close_redis() -> None:
    """Close Redis client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Redis client closed")


async def cache_transaction(transaction_id: str, data: dict[str, Any], ttl: int = 3600) -> None:
    """Cache transaction data.

    Args:
        transaction_id: Transaction identifier.
        data: Data to cache.
        ttl: Time-to-live in seconds.
    """
    client = await get_redis_client()
    if client is not None:
        await client.setex(f"transaction:{transaction_id}", ttl, str(data))
        logger.debug("Transaction cached", transaction_id=transaction_id)


async def get_cached_transaction(transaction_id: str) -> dict[str, Any] | None:
    """Get cached transaction data.

    Args:
        transaction_id: Transaction identifier.

    Returns:
        Cached data or None.
    """
    client = await get_redis_client()
    if client is not None:
        data = await client.get(f"transaction:{transaction_id}")
        if data is not None:
            return {"transaction_id": transaction_id, "data": data}
    return None
