"""Tests for trust scoring."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_trust_score(client: TestClient) -> None:
    """Test creating a trust score."""
    response = client.post(
        "/api/v1/trust",
        json={
            "user_id": "user_123",
            "transaction_count": 10,
            "successful_transactions": 9,
            "dispute_count": 1,
            "average_rating": 4.5,
            "account_age_days": 365,
            "verification_status": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user_123"
    assert 0.0 <= data["score"] <= 1.0
    assert data["level"] in ["untrusted", "low", "medium", "high", "verified"]


def test_get_trust_score(client: TestClient) -> None:
    """Test getting a trust score."""
    client.post(
        "/api/v1/trust",
        json={
            "user_id": "user_456",
            "transaction_count": 5,
            "successful_transactions": 5,
            "average_rating": 5.0,
            "account_age_days": 730,
            "verification_status": True,
        },
    )

    response = client.get("/api/v1/trust/user_456")
    assert response.status_code == 200
    assert response.json()["user_id"] == "user_456"


def test_update_trust_score(client: TestClient) -> None:
    """Test updating a trust score."""
    client.post(
        "/api/v1/trust",
        json={
            "user_id": "user_789",
            "transaction_count": 5,
            "successful_transactions": 4,
            "average_rating": 4.0,
            "account_age_days": 180,
        },
    )

    response = client.post(
        "/api/v1/trust/user_789/update?transaction_success=true&new_rating=5.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_count"] == 6
