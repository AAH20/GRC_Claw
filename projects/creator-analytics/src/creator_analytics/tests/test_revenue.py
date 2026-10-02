"""Tests for revenue tracking endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_revenue_report(client: AsyncClient, sample_revenue_data: dict) -> None:
    """Test revenue report generation endpoint.

    Args:
        client: Test client.
        sample_revenue_data: Sample revenue data.
    """
    response = await client.post("/api/v1/revenue/report", json=sample_revenue_data)
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == sample_revenue_data["creator_id"]
    assert "breakdown" in data
    assert "total_revenue" in data


@pytest.mark.asyncio
async def test_get_revenue_report(client: AsyncClient) -> None:
    """Test get revenue report endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/revenue/test-creator-123")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"


@pytest.mark.asyncio
async def test_get_revenue_breakdown(client: AsyncClient) -> None:
    """Test get revenue breakdown endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/revenue/test-creator-123/breakdown")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"
    assert "breakdown" in data
