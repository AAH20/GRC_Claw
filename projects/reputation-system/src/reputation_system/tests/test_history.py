"""Tests for reputation history endpoints."""

from fastapi.testclient import TestClient


def test_create_history_entry(client: TestClient) -> None:
    """Test creating a history entry."""
    response = client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "contribution",
            "score_change": 50,
            "previous_score": 100,
            "new_score": 150,
            "reason": "Submitted a high-quality contribution",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["member_id"] == "user-123"
    assert data["action"] == "contribution"
    assert data["score_change"] == 50


def test_get_history_entry(client: TestClient) -> None:
    """Test getting a history entry."""
    create_response = client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "contribution",
            "score_change": 50,
            "previous_score": 100,
            "new_score": 150,
        },
    )
    entry_id = create_response.json()["id"]
    response = client.get(f"/api/v1/history/{entry_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "contribution"


def test_get_member_history(client: TestClient) -> None:
    """Test getting member history."""
    client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "contribution",
            "score_change": 50,
            "previous_score": 100,
            "new_score": 150,
        },
    )
    client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "badge_earned",
            "score_change": 20,
            "previous_score": 150,
            "new_score": 170,
        },
    )
    response = client.get("/api/v1/history/member/user-123")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_analyze_member_history(client: TestClient) -> None:
    """Test analyzing member history with agent."""
    # Create some history entries
    client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "contribution",
            "score_change": 50,
            "previous_score": 100,
            "new_score": 150,
        },
    )
    client.post(
        "/api/v1/history",
        json={
            "member_id": "user-123",
            "action": "contribution",
            "score_change": 30,
            "previous_score": 150,
            "new_score": 180,
        },
    )
    response = client.post("/api/v1/history/analyze/user-123")
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert "net_change" in data
    assert "trend" in data
    assert "insights" in data


def test_analyze_empty_history(client: TestClient) -> None:
    """Test analyzing history for member with no entries."""
    response = client.post("/api/v1/history/analyze/nonexistent-user")
    assert response.status_code == 404
