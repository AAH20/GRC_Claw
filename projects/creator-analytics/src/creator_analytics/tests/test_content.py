"""Tests for content performance endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_content(client: AsyncClient, sample_content_data: dict) -> None:
    """Test content analysis endpoint.

    Args:
        client: Test client.
        sample_content_data: Sample content data.
    """
    response = await client.post("/api/v1/content/analyze", json=sample_content_data)
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == sample_content_data["content_id"]
    assert "metrics" in data
    assert "performance_score" in data


@pytest.mark.asyncio
async def test_get_content_performance(client: AsyncClient) -> None:
    """Test get content performance endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/content/content-456")
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == "content-456"


@pytest.mark.asyncio
async def test_get_creator_content(client: AsyncClient) -> None:
    """Test get creator content endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/content/creator/test-creator-123")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"
    assert "content" in data
