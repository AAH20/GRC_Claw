"""Tests for integration modules."""

from __future__ import annotations

import pytest

from ugc_marketplace.integrations.content_moderation import InMemoryStorage, WebhookClient
from ugc_marketplace.integrations.quality_scoring import CacheClient


@pytest.mark.asyncio
async def test_in_memory_storage() -> None:
    """Test in-memory storage."""
    storage = InMemoryStorage()
    assert storage is not None


@pytest.mark.asyncio
async def test_cache_client() -> None:
    """Test cache client."""
    cache = CacheClient()
    cache.set("key", "value")
    assert cache.get("key") == "value"
    cache.clear()
    assert cache.get("key") is None


@pytest.mark.asyncio
async def test_webhook_client() -> None:
    """Test webhook client."""
    client = WebhookClient()
    assert client is not None
