"""Tests for reputation score endpoints."""

from fastapi.testclient import TestClient


def test_create_reputation_score(client: TestClient) -> None:
    """Test creating a reputation score."""
    response = client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 100},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["member_id"] == "user-123"
    assert data["score"] == 100
    assert data["trust_tier"] == "bronze"


def test_create_duplicate_reputation_score(client: TestClient) -> None:
    """Test creating a duplicate reputation score fails."""
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 100},
    )
    response = client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 200},
    )
    assert response.status_code == 409


def test_get_reputation_score(client: TestClient) -> None:
    """Test getting a reputation score."""
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 100},
    )
    response = client.get("/api/v1/reputation/scores/user-123")
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert data["score"] == 100


def test_get_nonexistent_reputation_score(client: TestClient) -> None:
    """Test getting a non-existent reputation score."""
    response = client.get("/api/v1/reputation/scores/nonexistent")
    assert response.status_code == 404


def test_update_reputation_score(client: TestClient) -> None:
    """Test updating a reputation score."""
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 100},
    )
    response = client.put(
        "/api/v1/reputation/scores/user-123",
        json={"score": 500},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 500


def test_delete_reputation_score(client: TestClient) -> None:
    """Test deleting a reputation score."""
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-123", "initial_score": 100},
    )
    response = client.delete("/api/v1/reputation/scores/user-123")
    assert response.status_code == 204


def test_list_reputation_scores(client: TestClient) -> None:
    """Test listing reputation scores."""
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-1", "initial_score": 100},
    )
    client.post(
        "/api/v1/reputation/scores",
        json={"member_id": "user-2", "initial_score": 200},
    )
    response = client.get("/api/v1/reputation/scores")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_calculate_reputation_score(client: TestClient) -> None:
    """Test calculating reputation score with agent."""
    response = client.post(
        "/api/v1/reputation/scores/user-123/calculate",
        params={
            "contributions": 50,
            "positive_feedback": 30,
            "negative_feedback": 5,
            "account_age_days": 180,
            "badge_count": 3,
            "recent_activity_score": 0.8,
            "quality_score": 0.9,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert 0 <= data["score"] <= 1000
    assert data["trust_tier"] in ["bronze", "silver", "gold", "platinum", "diamond"]
    assert "factors" in data
    assert "confidence" in data
