"""Tests for integration clients."""

from __future__ import annotations

import pytest

from tier_management.integrations.cache import CacheClient
from tier_management.integrations.database import DatabaseClient
from tier_management.integrations.llm import LLMClient


@pytest.mark.asyncio
async def test_cache_client_without_redis() -> None:
    """Test CacheClient gracefully handles missing Redis."""
    client = CacheClient()
    # Should not raise even without Redis
    result = await client.get("test_key")
    assert result is None

    set_result = await client.set("test_key", {"data": "value"})
    assert set_result is False

    delete_result = await client.delete("test_key")
    assert delete_result is False

    health = await client.health_check()
    assert health is False


@pytest.mark.asyncio
async def test_database_client_without_connection() -> None:
    """Test DatabaseClient gracefully handles missing connection."""
    client = DatabaseClient()
    health = await client.health_check()
    assert health is False
    assert client.engine is None


@pytest.mark.asyncio
async def test_llm_client_without_api_key() -> None:
    """Test LLMClient raises error without API key."""
    from tier_management.config.settings import Settings

    settings = Settings(openai_api_key="")
    client = LLMClient(settings=settings)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        client.get_model()

    health = await client.health_check()
    assert health is False


@pytest.mark.asyncio
async def test_llm_client_health_check_no_key() -> None:
    """Test LLMClient health check returns False without key."""
    from tier_management.config.settings import Settings

    settings = Settings(openai_api_key="")
    client = LLMClient(settings=settings)
    assert await client.health_check() is False
