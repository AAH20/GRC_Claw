"""Tests for reputation explanation endpoints."""

from fastapi.testclient import TestClient


def test_create_explanation(client: TestClient) -> None:
    """Test creating an explanation."""
    response = client.post(
        "/api/v1/explanations",
        json={
            "member_id": "user-123",
            "explanation": "Your score is based on contributions and feedback.",
            "factors": [{"name": "contributions", "value": 50}],
            "recommendations": ["Increase contributions"],
            "confidence": 0.85,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["member_id"] == "user-123"
    assert data["confidence"] == 0.85


def test_get_explanation(client: TestClient) -> None:
    """Test getting an explanation."""
    create_response = client.post(
        "/api/v1/explanations",
        json={
            "member_id": "user-123",
            "explanation": "Test explanation",
            "confidence": 0.9,
        },
    )
    explanation_id = create_response.json()["id"]
    response = client.get(f"/api/v1/explanations/{explanation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["explanation"] == "Test explanation"


def test_get_member_explanations(client: TestClient) -> None:
    """Test getting member explanations."""
    client.post(
        "/api/v1/explanations",
        json={
            "member_id": "user-123",
            "explanation": "Explanation 1",
            "confidence": 0.8,
        },
    )
    client.post(
        "/api/v1/explanations",
        json={
            "member_id": "user-123",
            "explanation": "Explanation 2",
            "confidence": 0.9,
        },
    )
    response = client.get("/api/v1/explanations/member/user-123")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_generate_explanation(client: TestClient) -> None:
    """Test generating explanation with agent."""
    response = client.post(
        "/api/v1/explanations/generate/user-123",
        params={
            "current_score": 450,
            "trust_tier": "silver",
            "badge_count": 2,
            "account_age_days": 90,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert "explanation" in data
    assert "recommendations" in data
    assert "confidence" in data
