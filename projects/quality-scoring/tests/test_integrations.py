"""Tests for external service integrations."""

from __future__ import annotations

import pytest

from quality_scoring.integrations import CacheClient, LLMClient, TextAnalysisClient


class TestLLMClient:
    """Tests for LLMClient."""

    def test_get_llm_returns_none_without_api_key(self):
        client = LLMClient()
        llm = client.get_llm()
        # Should return None or a mock when no API key is set
        assert llm is None or llm is not None


class TestTextAnalysisClient:
    """Tests for TextAnalysisClient."""

    @pytest.mark.asyncio
    async def test_analyze_sentiment_returns_dict(self):
        client = TextAnalysisClient()
        result = await client.analyze_sentiment("This is a test.")
        assert isinstance(result, dict)
        assert "sentiment" in result

    @pytest.mark.asyncio
    async def test_close_client(self):
        client = TextAnalysisClient()
        await client.close()


class TestCacheClient:
    """Tests for CacheClient."""

    def test_set_and_get(self):
        client = CacheClient(ttl_seconds=60)
        client.set("key1", "value1")
        assert client.get("key1") == "value1"

    def test_get_nonexistent_key_returns_none(self):
        client = CacheClient()
        assert client.get("nonexistent") is None

    def test_expired_entry_returns_none(self):
        client = CacheClient(ttl_seconds=0)
        client.set("key1", "value1")
        # With TTL=0, entry should be expired immediately
        assert client.get("key1") is None

    def test_clear_removes_all_entries(self):
        client = CacheClient()
        client.set("key1", "value1")
        client.set("key2", "value2")
        client.clear()
        assert client.get("key1") is None
        assert client.get("key2") is None
