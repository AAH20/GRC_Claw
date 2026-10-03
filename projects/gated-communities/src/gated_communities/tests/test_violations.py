"""Tests for violation API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_list_violations_empty(client: TestClient) -> None:
    """Test listing violations when none exist."""
    response = client.get("/api/v1/violations")
    assert response.status_code == 200
    assert response.json() == []


def test_report_violation(client: TestClient) -> None:
    """Test reporting a new violation."""
    policy_data = {"name": "Test Policy", "category": "security"}
    policy_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = policy_response.json()["id"]

    violation_data = {
        "policy_id": policy_id,
        "title": "Unauthorized access detected",
        "description": "User accessed restricted resource without authorization",
        "severity": "high",
        "evidence": ["log entry 1", "log entry 2"],
    }
    response = client.post("/api/v1/violations", json=violation_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == violation_data["title"]
    assert data["severity"] == "high"
    assert data["status"] == "open"
    assert "id" in data


def test_get_violation(client: TestClient) -> None:
    """Test getting a violation by ID."""
    policy_data = {"name": "Test Policy", "category": "security"}
    policy_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = policy_response.json()["id"]

    violation_data = {
        "policy_id": policy_id,
        "title": "Test Violation",
        "severity": "medium",
    }
    create_response = client.post("/api/v1/violations", json=violation_data)
    violation_id = create_response.json()["id"]

    response = client.get(f"/api/v1/violations/{violation_id}")
    assert response.status_code == 200
    assert response.json()["id"] == violation_id


def test_get_violation_not_found(client: TestClient) -> None:
    """Test getting a non-existent violation."""
    response = client.get("/api/v1/violations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
