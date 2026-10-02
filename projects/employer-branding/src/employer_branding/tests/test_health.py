"""Tests for health check endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test basic health check endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_readiness_check(client):
    """Test readiness probe endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_liveness_check(client):
    """Test liveness probe endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
