"""Unit tests for API routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestCampaignCreate:
    """Tests for campaign creation endpoint."""

    def test_create_campaign_success(self, client: TestClient, sample_campaign_data: dict) -> None:
        """Test successful campaign creation."""
        response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_campaign_data["name"]
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    def test_create_campaign_validation_error(self, client: TestClient) -> None:
        """Test campaign creation with invalid data."""
        invalid_data = {"name": "", "total_budget": -100}
        response = client.post("/api/v1/campaigns", json=invalid_data)
        assert response.status_code == 422

    def test_create_campaign_missing_required(self, client: TestClient) -> None:
        """Test campaign creation with missing required fields."""
        response = client.post("/api/v1/campaigns", json={})
        assert response.status_code == 422


class TestCampaignList:
    """Tests for campaign listing endpoint."""

    def test_list_campaigns_empty(self, client: TestClient) -> None:
        """Test listing campaigns when none exist."""
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["campaigns"] == []
        assert data["total"] == 0

    def test_list_campaigns_with_data(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test listing campaigns with existing data."""
        # Create a campaign first
        client.post("/api/v1/campaigns", json=sample_campaign_data)

        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["campaigns"]) >= 1


class TestCampaignGet:
    """Tests for campaign detail endpoint."""

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent campaign."""
        response = client.get("/api/v1/campaigns/nonexistent")
        assert response.status_code == 404

    def test_get_campaign_success(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test getting an existing campaign."""
        create_response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id


class TestCampaignUpdate:
    """Tests for campaign update endpoint."""

    def test_update_campaign_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent campaign."""
        response = client.put("/api/v1/campaigns/nonexistent", json={"name": "New Name"})
        assert response.status_code == 404

    def test_update_campaign_success(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test successful campaign update."""
        create_response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        update_data = {"name": "Updated Campaign Name"}
        response = client.put(f"/api/v1/campaigns/{campaign_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign Name"


class TestCampaignDelete:
    """Tests for campaign deletion endpoint."""

    def test_delete_campaign_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent campaign."""
        response = client.delete("/api/v1/campaigns/nonexistent")
        assert response.status_code == 404

    def test_delete_campaign_success(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test successful campaign deletion."""
        create_response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404


class TestCampaignOptimize:
    """Tests for campaign optimization endpoint."""

    def test_optimize_campaign_not_found(self, client: TestClient) -> None:
        """Test optimizing a non-existent campaign."""
        response = client.post("/api/v1/campaigns/nonexistent/optimize", json={})
        assert response.status_code == 404

    def test_optimize_campaign_success(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test successful campaign optimization."""
        create_response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/campaigns/{campaign_id}/optimize",
            json={"optimization_type": "full"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert data["status"] == "completed"
        assert "recommendations" in data


class TestCampaignStatus:
    """Tests for campaign status endpoint."""

    def test_get_status_not_found(self, client: TestClient) -> None:
        """Test getting status of non-existent campaign."""
        response = client.get("/api/v1/campaigns/nonexistent/status")
        assert response.status_code == 404

    def test_get_status_success(
        self, client: TestClient, sample_campaign_data: dict
    ) -> None:
        """Test getting status of existing campaign."""
        create_response = client.post("/api/v1/campaigns", json=sample_campaign_data)
        campaign_id = create_response.json()["id"]

        response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert "status" in data
