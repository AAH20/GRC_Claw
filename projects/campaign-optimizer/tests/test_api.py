"""Tests for the Campaign Optimizer API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from campaign_optimizer.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ─── Health Check Tests ─────────────────────────────────────────────


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


# ─── Campaign API Tests ─────────────────────────────────────────────


class TestCampaignAPI:
    """Tests for the campaign endpoints."""

    def test_create_campaign(self, client: TestClient) -> None:
        """Test creating a new campaign."""
        payload = {
            "name": "Test Campaign",
            "business_goal": "Increase online sales",
            "total_budget": 5000.0,
            "duration_days": 30,
            "platforms": ["meta", "google"],
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["total_budget"] == 5000.0
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_campaign_invalid_budget(self, client: TestClient) -> None:
        """Test that invalid budget returns 422."""
        payload = {
            "name": "Test Campaign",
            "business_goal": "Test",
            "total_budget": -100.0,
            "duration_days": 30,
        }
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 422

    def test_list_campaigns(self, client: TestClient) -> None:
        """Test listing campaigns."""
        # Create a campaign first
        client.post(
            "/api/v1/campaigns",
            json={
                "name": "List Test Campaign",
                "business_goal": "Test",
                "total_budget": 1000.0,
                "duration_days": 14,
            },
        )
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_campaign(self, client: TestClient) -> None:
        """Test getting a specific campaign."""
        # Create a campaign
        create_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Get Test Campaign",
                "business_goal": "Test",
                "total_budget": 2000.0,
                "duration_days": 21,
            },
        )
        campaign_id = create_response.json()["id"]

        # Get the campaign
        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id
        assert data["name"] == "Get Test Campaign"

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent campaign returns 404."""
        response = client.get("/api/v1/campaigns/nonexistent-id")
        assert response.status_code == 404

    def test_update_campaign(self, client: TestClient) -> None:
        """Test updating a campaign."""
        # Create a campaign
        create_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Update Test Campaign",
                "business_goal": "Test",
                "total_budget": 3000.0,
                "duration_days": 30,
            },
        )
        campaign_id = create_response.json()["id"]

        # Update the campaign
        response = client.patch(
            f"/api/v1/campaigns/{campaign_id}",
            json={"status": "active", "total_budget": 4000.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["total_budget"] == 4000.0

    def test_delete_campaign(self, client: TestClient) -> None:
        """Test deleting a campaign."""
        # Create a campaign
        create_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Delete Test Campaign",
                "business_goal": "Test",
                "total_budget": 1000.0,
                "duration_days": 7,
            },
        )
        campaign_id = create_response.json()["id"]

        # Delete the campaign
        response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404

    def test_optimize_campaign(self, client: TestClient) -> None:
        """Test triggering campaign optimization."""
        # Create a campaign
        create_response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Optimize Test Campaign",
                "business_goal": "Increase sales",
                "total_budget": 10000.0,
                "duration_days": 30,
            },
        )
        campaign_id = create_response.json()["id"]

        # Trigger optimization
        response = client.post(f"/api/v1/campaigns/{campaign_id}/optimize")
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert data["status"] == "completed"
        assert len(data["recommendations"]) > 0


# ─── Budget API Tests ───────────────────────────────────────────────


class TestBudgetAPI:
    """Tests for the budget endpoints."""

    def test_get_budget_not_found(self, client: TestClient) -> None:
        """Test getting budget for non-existent campaign returns 404."""
        response = client.get("/api/v1/budget/nonexistent-id")
        assert response.status_code == 404

    def test_update_budget_allocation(self, client: TestClient) -> None:
        """Test updating budget allocation."""
        payload = {
            "campaign_id": "camp_001",
            "platform_allocations": {"meta": 2000.0, "google": 1500.0},
            "daily_budget": 150.0,
            "strategy": "performance",
        }
        response = client.put("/api/v1/budget/camp_001", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_budget"] == 3500.0
        assert data["daily_budget"] == 150.0

    def test_update_budget_invalid_allocation(self, client: TestClient) -> None:
        """Test that zero total budget returns 400."""
        payload = {
            "campaign_id": "camp_001",
            "platform_allocations": {"meta": 0.0},
        }
        response = client.put("/api/v1/budget/camp_001", json=payload)
        assert response.status_code == 400

    def test_get_budget_status(self, client: TestClient) -> None:
        """Test getting budget status."""
        # First create a budget
        client.put(
            "/api/v1/budget/camp_status_test",
            json={
                "campaign_id": "camp_status_test",
                "platform_allocations": {"meta": 5000.0},
                "daily_budget": 200.0,
            },
        )
        response = client.get("/api/v1/budget/camp_status_test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == "camp_status_test"
        assert data["total_budget"] == 5000.0


# ─── Analytics API Tests ────────────────────────────────────────────


class TestAnalyticsAPI:
    """Tests for the analytics endpoints."""

    def test_get_analytics_not_found(self, client: TestClient) -> None:
        """Test getting analytics for non-existent campaign returns 404."""
        response = client.get("/api/v1/analytics/nonexistent-id")
        assert response.status_code == 404

    def test_generate_report_not_found(self, client: TestClient) -> None:
        """Test generating report for non-existent campaign returns 404."""
        payload = {"campaign_id": "nonexistent-id"}
        response = client.post("/api/v1/analytics/nonexistent-id/report", json=payload)
        assert response.status_code == 404

    def test_get_funnel_not_found(self, client: TestClient) -> None:
        """Test getting funnel for non-existent campaign returns 404."""
        response = client.get("/api/v1/analytics/nonexistent-id/funnel")
        assert response.status_code == 404


# ─── Metrics Endpoint Test ──────────────────────────────────────────


class TestMetricsEndpoint:
    """Tests for the Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, client: TestClient) -> None:
        """Test that metrics endpoint returns Prometheus data."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
