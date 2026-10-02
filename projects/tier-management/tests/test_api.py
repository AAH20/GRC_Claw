"""Tests for tier management API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient) -> None:
    """Test readiness probe returns 200."""
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient) -> None:
    """Test liveness probe returns 200."""
    response = await client.get("/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test root endpoint returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_list_tiers_empty(client: AsyncClient) -> None:
    """Test listing tiers when none exist."""
    response = await client.get("/api/v1/tiers")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_tier(client: AsyncClient, sample_tier_data: dict) -> None:
    """Test creating a new tier."""
    response = await client.post("/api/v1/tiers", json=sample_tier_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_tier_data["name"]
    assert data["level"] == sample_tier_data["level"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_tier(client: AsyncClient, sample_tier_data: dict) -> None:
    """Test getting a specific tier."""
    # Create a tier first
    create_response = await client.post("/api/v1/tiers", json=sample_tier_data)
    tier_id = create_response.json()["id"]

    # Get the tier
    response = await client.get(f"/api/v1/tiers/{tier_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tier_id
    assert data["name"] == sample_tier_data["name"]


@pytest.mark.asyncio
async def test_get_tier_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent tier returns 404."""
    from uuid import uuid4

    response = await client.get(f"/api/v1/tiers/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_tier(client: AsyncClient, sample_tier_data: dict) -> None:
    """Test updating a tier."""
    # Create a tier first
    create_response = await client.post("/api/v1/tiers", json=sample_tier_data)
    tier_id = create_response.json()["id"]

    # Update the tier
    update_data = {"name": "Updated Gold Tier"}
    response = await client.put(f"/api/v1/tiers/{tier_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Gold Tier"


@pytest.mark.asyncio
async def test_delete_tier(client: AsyncClient, sample_tier_data: dict) -> None:
    """Test deleting a tier."""
    # Create a tier first
    create_response = await client.post("/api/v1/tiers", json=sample_tier_data)
    tier_id = create_response.json()["id"]

    # Delete the tier
    response = await client.delete(f"/api/v1/tiers/{tier_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/tiers/{tier_id}")
    assert get_response.status_code == 404
