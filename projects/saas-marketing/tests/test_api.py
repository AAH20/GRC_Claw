"""Tests for API endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from saas_marketing.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestCampaignEndpoints:
    """Tests for campaign API endpoints."""

    def test_create_campaign(self, client: TestClient) -> None:
        """Test creating a campaign."""
        payload = {
            "name": "Q4 Product Launch",
            "campaign_type": "email",
            "target_audience": "SaaS founders",
            "budget": 5000.0,
            "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "goals": ["awareness", "signups"],
            "channels": ["email", "social"],
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Q4 Product Launch"
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_campaign_invalid_dates(self, client: TestClient) -> None:
        """Test creating a campaign with invalid dates."""
        payload = {
            "name": "Invalid Campaign",
            "campaign_type": "email",
            "target_audience": "test",
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 422

    def test_get_campaign(self, client: TestClient) -> None:
        """Test getting a campaign by ID."""
        # First create a campaign
        payload = {
            "name": "Test Campaign",
            "campaign_type": "social",
            "target_audience": "developers",
            "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
        }
        create_response = client.post("/api/v1/campaigns", json=payload)
        campaign_id = create_response.json()["id"]

        # Then retrieve it
        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        assert response.json()["id"] == campaign_id

    def test_get_nonexistent_campaign(self, client: TestClient) -> None:
        """Test getting a campaign that doesn't exist."""
        response = client.get("/api/v1/campaigns/nonexistent-id")
        assert response.status_code == 404

    def test_list_campaigns(self, client: TestClient) -> None:
        """Test listing campaigns."""
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_delete_campaign(self, client: TestClient) -> None:
        """Test deleting a campaign."""
        # Create then delete
        payload = {
            "name": "Delete Me",
            "campaign_type": "content",
            "target_audience": "test",
            "start_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        create_response = client.post("/api/v1/campaigns", json=payload)
        campaign_id = create_response.json()["id"]

        delete_response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404


class TestUserEndpoints:
    """Tests for user API endpoints."""

    def test_score_user(self, client: TestClient) -> None:
        """Test scoring a user."""
        payload = {
            "feature_usage_count": 5,
            "total_sessions": 15,
            "avg_session_duration_seconds": 240,
            "days_since_signup": 10,
            "key_actions_completed": ["signup", "create_project"],
            "team_size": 3,
            "billing_page_visits": 1,
            "integration_attempts": 1,
            "nps_score": 8,
        }
        response = client.post("/api/v1/users/user_123/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert "score" in data
        assert "tier" in data
        assert "recommendation" in data

    def test_get_churn_risk(self, client: TestClient) -> None:
        """Test getting churn risk for a user."""
        response = client.get("/api/v1/users/user_123/churn-risk")
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "user_123"
        assert "risk_level" in data
        assert "risk_score" in data
        assert "recommended_actions" in data

    def test_get_user_health(self, client: TestClient) -> None:
        """Test getting overall user health."""
        response = client.get("/api/v1/users/user_123/health")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_123"
        assert "overall_health" in data
        assert "recommendations" in data
