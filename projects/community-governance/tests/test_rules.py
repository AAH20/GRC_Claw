"""Tests for rule management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_rule(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test creating a new rule."""
    response = await client.post("/api/v1/rules", json=sample_rule_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_rule_data["name"]
    assert data["description"] == sample_rule_data["description"]
    assert data["category"] == sample_rule_data["category"]
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_rules(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test listing all rules."""
    # Create a rule first
    await client.post("/api/v1/rules", json=sample_rule_data)

    response = await client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_rule(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test getting a specific rule."""
    # Create a rule first
    create_response = await client.post("/api/v1/rules", json=sample_rule_data)
    rule_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule_id
    assert data["name"] == sample_rule_data["name"]


@pytest.mark.asyncio
async def test_get_rule_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent rule returns 404."""
    response = await client.get("/api/v1/rules/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_rule(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test updating an existing rule."""
    # Create a rule first
    create_response = await client.post("/api/v1/rules", json=sample_rule_data)
    rule_id = create_response.json()["id"]

    update_data = {"name": "Updated Rule Name", "severity": "high"}
    response = await client.put(f"/api/v1/rules/{rule_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Rule Name"
    assert data["severity"] == "high"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_delete_rule(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test deleting a rule."""
    # Create a rule first
    create_response = await client.post("/api/v1/rules", json=sample_rule_data)
    rule_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(f"/api/v1/rules/{rule_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_enforce_rules(client: AsyncClient, sample_rule_data: dict) -> None:
    """Test enforcing rules against an action."""
    # Create a rule first
    await client.post("/api/v1/rules", json=sample_rule_data)

    action_data = {
        "action_type": "create",
        "target_id": "post_123",
        "target_type": "post",
        "actor_id": "user_456",
        "reason": "Testing rule enforcement",
    }
    response = await client.post("/api/v1/rules/enforce", json=action_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "is_violation" in data[0]
    assert "rule_name" in data[0]
