"""Tests for badge endpoints."""

from fastapi.testclient import TestClient


def test_create_badge(client: TestClient) -> None:
    """Test creating a badge."""
    response = client.post(
        "/api/v1/badges",
        json={
            "name": "Early Adopter",
            "description": "Joined during the beta period",
            "category": "special",
            "points": 50,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Early Adopter"
    assert data["category"] == "special"
    assert data["points"] == 50


def test_get_badge(client: TestClient) -> None:
    """Test getting a badge."""
    create_response = client.post(
        "/api/v1/badges",
        json={
            "name": "Early Adopter",
            "description": "Joined during the beta period",
            "category": "special",
        },
    )
    badge_id = create_response.json()["id"]
    response = client.get(f"/api/v1/badges/{badge_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Early Adopter"


def test_get_nonexistent_badge(client: TestClient) -> None:
    """Test getting a non-existent badge."""
    response = client.get("/api/v1/badges/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_badges(client: TestClient) -> None:
    """Test listing badges."""
    client.post(
        "/api/v1/badges",
        json={"name": "Badge 1", "description": "Test badge 1", "category": "contribution"},
    )
    client.post(
        "/api/v1/badges",
        json={"name": "Badge 2", "description": "Test badge 2", "category": "quality"},
    )
    response = client.get("/api/v1/badges")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_update_badge(client: TestClient) -> None:
    """Test updating a badge."""
    create_response = client.post(
        "/api/v1/badges",
        json={"name": "Badge 1", "description": "Test badge", "category": "contribution"},
    )
    badge_id = create_response.json()["id"]
    response = client.put(
        f"/api/v1/badges/{badge_id}",
        json={"points": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["points"] == 100


def test_delete_badge(client: TestClient) -> None:
    """Test deleting a badge."""
    create_response = client.post(
        "/api/v1/badges",
        json={"name": "Badge 1", "description": "Test badge", "category": "contribution"},
    )
    badge_id = create_response.json()["id"]
    response = client.delete(f"/api/v1/badges/{badge_id}")
    assert response.status_code == 204


def test_evaluate_member_badges(client: TestClient) -> None:
    """Test evaluating member badges with agent."""
    response = client.post(
        "/api/v1/badges/evaluate/user-123",
        json={
            "badge_criteria": {
                "contributor": {
                    "metric": "contributions",
                    "threshold": 10,
                    "category": "contribution",
                    "points": 20,
                },
            },
            "member_stats": {
                "contributions": 15,
                "positive_feedback": 10,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert "eligible_badges" in data
    assert "revoked_badges" in data
    assert "recommendations" in data
