"""Tests for engagement analysis endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_engagement_report(
    client: AsyncClient, sample_engagement_data: dict
) -> None:
    """Test engagement report generation endpoint.

    Args:
        client: Test client.
        sample_engagement_data: Sample engagement data.
    """
    response = await client.post("/api/v1/engagement/report", json=sample_engagement_data)
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == sample_engagement_data["creator_id"]
    assert "metrics" in data
    assert "audience_loyalty_score" in data


@pytest.mark.asyncio
async def test_get_engagement_report(client: AsyncClient) -> None:
    """Test get engagement report endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/engagement/test-creator-123")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"


@pytest.mark.asyncio
async def test_get_engagement_metrics(client: AsyncClient) -> None:
    """Test get engagement metrics endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/engagement/test-creator-123/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"
    assert "metrics" in data
