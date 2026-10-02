"""Tests for health check endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test the health check endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "agents" in data


@pytest.mark.asyncio
async def test_health_check_agents(client: AsyncClient) -> None:
    """Test that health check includes agent status."""
    response = await client.get("/health")
    data = response.json()
    assert "agents" in data
    assert isinstance(data["agents"], dict)
    assert len(data["agents"]) == 5
