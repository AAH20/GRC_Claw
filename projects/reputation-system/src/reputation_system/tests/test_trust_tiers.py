"""Tests for trust tier endpoints."""

from fastapi.testclient import TestClient


def test_create_trust_tier(client: TestClient) -> None:
    """Test creating a trust tier."""
    response = client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "gold",
            "name": "Gold Tier",
            "description": "Gold tier for trusted members",
            "min_score": 500,
            "max_score": 699,
            "benefits": ["Premium support", "Exclusive content"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["level"] == "gold"
    assert data["name"] == "Gold Tier"


def test_get_trust_tier(client: TestClient) -> None:
    """Test getting a trust tier."""
    create_response = client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "silver",
            "name": "Silver Tier",
            "description": "Silver tier",
            "min_score": 300,
            "max_score": 499,
        },
    )
    tier_id = create_response.json()["id"]
    response = client.get(f"/api/v1/trust-tiers/{tier_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "silver"


def test_list_trust_tiers(client: TestClient) -> None:
    """Test listing trust tiers."""
    client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "bronze",
            "name": "Bronze",
            "description": "Entry tier",
            "min_score": 0,
            "max_score": 299,
        },
    )
    client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "diamond",
            "name": "Diamond",
            "description": "Top tier",
            "min_score": 900,
            "max_score": 1000,
        },
    )
    response = client.get("/api/v1/trust-tiers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_update_trust_tier(client: TestClient) -> None:
    """Test updating a trust tier."""
    create_response = client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "silver",
            "name": "Silver",
            "description": "Silver tier",
            "min_score": 300,
            "max_score": 499,
        },
    )
    tier_id = create_response.json()["id"]
    response = client.put(
        f"/api/v1/trust-tiers/{tier_id}",
        json={"benefits": ["Priority support"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Priority support" in data["benefits"]


def test_delete_trust_tier(client: TestClient) -> None:
    """Test deleting a trust tier."""
    create_response = client.post(
        "/api/v1/trust-tiers",
        json={
            "level": "bronze",
            "name": "Bronze",
            "description": "Entry tier",
            "min_score": 0,
            "max_score": 299,
        },
    )
    tier_id = create_response.json()["id"]
    response = client.delete(f"/api/v1/trust-tiers/{tier_id}")
    assert response.status_code == 204


def test_evaluate_trust_tier(client: TestClient) -> None:
    """Test evaluating trust tier with agent."""
    response = client.post(
        "/api/v1/trust-tiers/evaluate/user-123",
        params={
            "current_score": 600,
            "current_tier": "silver",
            "account_age_days": 120,
            "violation_count": 0,
            "verification_status": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "user-123"
    assert "recommended_tier" in data
    assert "can_upgrade" in data
    assert "requirements_met" in data
    assert "benefits" in data
