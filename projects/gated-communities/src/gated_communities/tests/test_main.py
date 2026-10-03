"""Tests for main application."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_check(client):
    """Test readiness endpoint."""
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "moderation_analytics" in response.text


@pytest.mark.asyncio
async def test_analytics_summary(client):
    """Test analytics summary endpoint."""
    response = await client.post("/api/v1/analytics/summary?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "analytics" in data
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_get_trends(client):
    """Test trends endpoint."""
    response = await client.get("/api/v1/trends?days=30")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_moderators(client):
    """Test list moderators endpoint."""
    response = await client.get("/api/v1/moderators")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_policies(client):
    """Test list policies endpoint."""
    response = await client.get("/api/v1/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_explain_analytics(client):
    """Test explain endpoint."""
    response = await client.post(
        "/api/v1/explain",
        json={"total_events": 100, "total_actions": 80},
    )
    assert response.status_code == 200
    assert "explanation" in response.json()
