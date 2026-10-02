"""Tests for PPC Manager API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ppc_manager.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient instance."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Test that health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ppc-manager"


class TestMetricsEndpoint:
    """Tests for the metrics endpoint."""

    def test_metrics_returns_prometheus_format(self, client: TestClient) -> None:
        """Test that metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestCampaignEndpoints:
    """Tests for campaign CRUD endpoints."""

    def test_list_campaigns_empty(self, client: TestClient) -> None:
        """Test listing campaigns when none exist."""
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_campaign(self, client: TestClient) -> None:
        """Test creating a campaign."""
        payload = {
            "name": "Test Campaign",
            "platform": "google",
            "budget": 100.0,
            "status": "active",
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["platform"] == "google"
        assert data["budget"] == 100.0
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_campaign_invalid_platform(self, client: TestClient) -> None:
        """Test creating a campaign with invalid platform."""
        payload = {
            "name": "Test Campaign",
            "platform": "invalid",
            "budget": 100.0,
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 422

    def test_create_campaign_negative_budget(self, client: TestClient) -> None:
        """Test creating a campaign with negative budget."""
        payload = {
            "name": "Test Campaign",
            "platform": "google",
            "budget": -10.0,
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 422

    def test_get_campaign(self, client: TestClient) -> None:
        """Test getting a campaign by ID."""
        # Create first
        payload = {"name": "Test", "platform": "meta", "budget": 50.0}
        create_response = client.post("/api/v1/campaigns", json=payload)
        campaign_id = create_response.json()["id"]

        # Get
        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        assert response.json()["id"] == campaign_id

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent campaign."""
        response = client.get("/api/v1/campaigns/nonexistent")
        assert response.status_code == 404

    def test_update_campaign(self, client: TestClient) -> None:
        """Test updating a campaign."""
        # Create first
        payload = {"name": "Test", "platform": "google", "budget": 100.0}
        create_response = client.post("/api/v1/campaigns", json=payload)
        campaign_id = create_response.json()["id"]

        # Update
        update_payload = {"budget": 200.0, "status": "paused"}
        response = client.put(f"/api/v1/campaigns/{campaign_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["budget"] == 200.0
        assert data["status"] == "paused"

    def test_delete_campaign(self, client: TestClient) -> None:
        """Test deleting a campaign."""
        # Create first
        payload = {"name": "Test", "platform": "google", "budget": 100.0}
        create_response = client.post("/api/v1/campaigns", json=payload)
        campaign_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404


class TestKeywordEndpoints:
    """Tests for keyword endpoints."""

    def test_list_keywords_empty(self, client: TestClient) -> None:
        """Test listing keywords when none exist."""
        response = client.get("/api/v1/keywords")
        assert response.status_code == 200
        assert response.json() == []

    def test_research_keywords(self, client: TestClient) -> None:
        """Test keyword research endpoint."""
        payload = {
            "seed_keyword": "ppc software",
            "language": "en",
            "location": "US",
        }
        response = client.post("/api/v1/keywords/research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_research_keywords_empty_seed(self, client: TestClient) -> None:
        """Test keyword research with empty seed."""
        payload = {
            "seed_keyword": "",
            "language": "en",
            "location": "US",
        }
        response = client.post("/api/v1/keywords/research", json=payload)
        assert response.status_code == 400
