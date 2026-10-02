"""Tests for dispute management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_dispute(client: AsyncClient, sample_dispute_data: dict) -> None:
    """Test creating a new dispute."""
    response = await client.post("/api/v1/disputes", json=sample_dispute_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_dispute_data["title"]
    assert data["status"] == "open"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_disputes(client: AsyncClient, sample_dispute_data: dict) -> None:
    """Test listing all disputes."""
    # Create a dispute first
    await client.post("/api/v1/disputes", json=sample_dispute_data)

    response = await client.get("/api/v1/disputes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_dispute(client: AsyncClient, sample_dispute_data: dict) -> None:
    """Test getting a specific dispute."""
    # Create a dispute first
    create_response = await client.post("/api/v1/disputes", json=sample_dispute_data)
    dispute_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/disputes/{dispute_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dispute_id
    assert data["title"] == sample_dispute_data["title"]


@pytest.mark.asyncio
async def test_get_dispute_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent dispute returns 404."""
    response = await client.get("/api/v1/disputes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_dispute(client: AsyncClient, sample_dispute_data: dict) -> None:
    """Test updating an existing dispute."""
    # Create a dispute first
    create_response = await client.post("/api/v1/disputes", json=sample_dispute_data)
    dispute_id = create_response.json()["id"]

    update_data = {"priority": "high", "status": "under_review"}
    response = await client.put(f"/api/v1/disputes/{dispute_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "high"
    assert data["status"] == "under_review"


@pytest.mark.asyncio
async def test_resolve_dispute(client: AsyncClient, sample_dispute_data: dict) -> None:
    """Test resolving a dispute."""
    # Create a dispute first
    create_response = await client.post("/api/v1/disputes", json=sample_dispute_data)
    dispute_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/disputes/{dispute_id}/resolve")
    assert response.status_code == 200
    data = response.json()
    assert "resolution_type" in data
    assert "outcome" in data
    assert "rationale" in data
