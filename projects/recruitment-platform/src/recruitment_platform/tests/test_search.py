"""Tests for search module."""

from __future__ import annotations

import pytest

from recruitment_platform.search.search_service import SearchService


class TestSearchService:
    """Test search service."""

    @pytest.mark.asyncio
    async def test_search_jobs(self) -> None:
        """Test job search."""
        service = SearchService()
        result = await service.search_jobs("python developer")
        assert "query" in result
        assert "results" in result
        assert "total" in result

    @pytest.mark.asyncio
    async def test_search_candidates(self) -> None:
        """Test candidate search."""
        service = SearchService()
        result = await service.search_candidates("software engineer")
        assert "query" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_skills(self) -> None:
        """Test skills search."""
        service = SearchService()
        result = await service.search_skills("python")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_autocomplete(self) -> None:
        """Test autocomplete."""
        service = SearchService()
        result = await service.autocomplete("pyt", "job")
        assert isinstance(result, list)
