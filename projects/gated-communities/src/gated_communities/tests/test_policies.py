"""Tests for policy API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_policies_empty(client: TestClient) -> None:
    """Test listing policies when none exist."""
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    assert response.json() == []


def test_create_policy(client: TestClient) -> None:
    """Test creating a new policy."""
    policy_data = {
        "name": "Data Retention Policy",
        "description": "Policy for data retention requirements",
        "category": "privacy",
        "version": "1.0.0",
        "rules": ["retain for 7 years", "encrypt at rest"],
    }
    response = client.post("/api/v1/policies", json=policy_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == policy_data["name"]
    assert data["category"] == policy_data["category"]
    assert data["status"] == "draft"
    assert "id" in data


def test_get_policy(client: TestClient) -> None:
    """Test getting a policy by ID."""
    policy_data = {
        "name": "Access Control Policy",
        "description": "Policy for access control",
        "category": "security",
    }
    create_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = create_response.json()["id"]

    response = client.get(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 200
    assert response.json()["id"] == policy_id


def test_get_policy_not_found(client: TestClient) -> None:
    """Test getting a non-existent policy."""
    response = client.get("/api/v1/policies/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_delete_policy(client: TestClient) -> None:
    """Test deleting a policy."""
    policy_data = {"name": "Test Policy", "category": "test"}
    create_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/policies/{policy_id}")
    assert get_response.status_code == 404
