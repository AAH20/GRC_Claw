"""Tests for analytics endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_analytics(client: AsyncClient) -> None:
    """Test getting governance analytics."""
    response = await client.get("/api/v1/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "period_start" in data
    assert "period_end" in data
    assert "health_score" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_get_analytics_with_period(client: AsyncClient) -> None:
    """Test getting analytics with custom period."""
    response = await client.get("/api/v1/analytics?period_days=7")
    assert response.status_code == 200
    data = response.json()
    assert "health_score" in data


@pytest.mark.asyncio
async def test_get_summary(client: AsyncClient) -> None:
    """Test getting governance summary."""
    response = await client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_active_rules" in data
    assert "total_active_policies" in data
    assert "open_disputes" in data
    assert "health_score" in data
