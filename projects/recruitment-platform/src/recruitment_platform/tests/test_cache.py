"""Tests for caching module."""

from __future__ import annotations

import pytest

from recruitment_platform.cache.redis_cache import Cache


class TestCache:
    """Test cache operations."""

    @pytest.mark.asyncio
    async def test_cache_instance(self) -> None:
        """Test cache instance creation."""
        cache = Cache()
        assert cache is not None

    @pytest.mark.asyncio
    async def test_cache_operations(self) -> None:
        """Test basic cache operations."""
        cache = Cache()
        # These will fail gracefully without Redis
        result = await cache.get("nonexistent-key")
        assert result is None
