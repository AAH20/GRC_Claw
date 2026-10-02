"""Tests for compliance score API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_scores_empty(client: TestClient) -> None:
    """Test listing scores when none exist."""
    response = client.get("/api/v1/scores")
    assert response.status_code == 200
    assert response.json() == []


def test_compute_score(client: TestClient) -> None:
    """Test computing a compliance score."""
    policy_data = {"name": "Test Policy", "category": "security"}
    policy_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = policy_response.json()["id"]

    score_data = {
        "policy_id": policy_id,
        "domain": "security",
        "factors": {"access_control": 0.9, "encryption": 0.8},
    }
    response = client.post("/api/v1/scores", json=score_data)
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "security"
    assert "score" in data
    assert 0 <= data["score"] <= 100


def test_get_score(client: TestClient) -> None:
    """Test getting a compliance score by ID."""
    policy_data = {"name": "Test Policy", "category": "security"}
    policy_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = policy_response.json()["id"]

    score_data = {"policy_id": policy_id, "domain": "privacy"}
    create_response = client.post("/api/v1/scores", json=score_data)
    score_id = create_response.json()["id"]

    response = client.get(f"/api/v1/scores/{score_id}")
    assert response.status_code == 200
    assert response.json()["id"] == score_id


def test_get_score_not_found(client: TestClient) -> None:
    """Test getting a non-existent score."""
    response = client.get("/api/v1/scores/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
