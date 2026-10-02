"""Tests for policy management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient, sample_policy_data: dict) -> None:
    """Test creating a new policy."""
    response = await client.post("/api/v1/policies", json=sample_policy_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_policy_data["name"]
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_policies(client: AsyncClient, sample_policy_data: dict) -> None:
    """Test listing all policies."""
    # Create a policy first
    await client.post("/api/v1/policies", json=sample_policy_data)

    response = await client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_policy(client: AsyncClient, sample_policy_data: dict) -> None:
    """Test getting a specific policy."""
    # Create a policy first
    create_response = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy_id
    assert data["name"] == sample_policy_data["name"]


@pytest.mark.asyncio
async def test_get_policy_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent policy returns 404."""
    response = await client.get("/api/v1/policies/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, sample_policy_data: dict) -> None:
    """Test updating an existing policy."""
    # Create a policy first
    create_response = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_response.json()["id"]

    update_data = {"status": "active", "enforcement_level": "strict"}
    response = await client.put(f"/api/v1/policies/{policy_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["enforcement_level"] == "strict"


@pytest.mark.asyncio
async def test_delete_policy(client: AsyncClient, sample_policy_data: dict) -> None:
    """Test deleting a policy."""
    # Create a policy first
    create_response = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(f"/api/v1/policies/{policy_id}")
    assert get_response.status_code == 404
