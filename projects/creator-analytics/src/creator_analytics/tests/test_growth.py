"""Tests for growth prediction endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_predict_growth(client: AsyncClient, sample_growth_data: dict) -> None:
    """Test growth prediction endpoint.

    Args:
        client: Test client.
        sample_growth_data: Sample growth data.
    """
    response = await client.post("/api/v1/growth/predict", json=sample_growth_data)
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == sample_growth_data["creator_id"]
    assert "predicted_followers" in data
    assert "confidence_score" in data


@pytest.mark.asyncio
async def test_get_growth_prediction(client: AsyncClient) -> None:
    """Test get growth prediction endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/growth/test-creator-123")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"


@pytest.mark.asyncio
async def test_get_growth_scenarios(client: AsyncClient) -> None:
    """Test get growth scenarios endpoint.

    Args:
        client: Test client.
    """
    response = await client.get("/api/v1/growth/test-creator-123/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert data["creator_id"] == "test-creator-123"
    assert "scenarios" in data
