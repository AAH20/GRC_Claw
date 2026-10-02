"""Tests for audience analysis endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_audience(client: AsyncClient, sample_audience_data: dict) -> None:
    """Test audience analysis endpoint.

    Args:
        client: Test client.
        sample_audience_data: Sample audience data.
    """
    response = await client.post("/api/v1/audience/analyze", json=sample_audience_data)
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == sample_audience_data["creator_id"]
    assert "demographics" in data
    assert "insights" in data


@pytest.mark.asyncio
async def test_get_audience(client: AsyncClient) -> None:
    """Test get audience endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/audience/test-creator-123")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"


@pytest.mark.asyncio
async def test_get_audience_segments(client: AsyncClient) -> None:
    """Test get audience segments endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/audience/test-creator-123/segments")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"
    assert "segments" in data
