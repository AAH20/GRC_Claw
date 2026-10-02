"""Integration tests for the Campaign Optimizer API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app


class TestCampaignLifecycle:
    """Integration tests for the full campaign lifecycle."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_full_campaign_lifecycle(self, client: TestClient) -> None:
        """Test the complete campaign lifecycle from creation to deletion."""
        # 1. Create campaign
        create_data = {
            "name": "Integration Test Campaign",
            "description": "Full lifecycle test",
            "goals": ["awareness", "conversion"],
            "total_budget": 25000.0,
            "daily_budget": 833.33,
            "channels": ["search", "social", "display"],
            "duration_days": 30,
            "target_audience": {
                "demographics": {"age_ranges": ["25-34", "35-44"], "locations": ["US"]},
            },
            "brand_voice": "professional",
            "key_message": "Integration test message",
            "industry": "technology",
        }

        create_response = client.post("/api/v1/campaigns", json=create_data)
        assert create_response.status_code == 201
        campaign = create_response.json()
        campaign_id = campaign["id"]
        assert campaign["status"] == "draft"

        # 2. Get campaign details
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Integration Test Campaign"

        # 3. Update campaign
        update_response = client.put(
            f"/api/v1/campaigns/{campaign_id}",
            json={"status": "active", "name": "Updated Integration Test"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "active"
        assert update_response.json()["name"] == "Updated Integration Test"

        # 4. Get campaign status
        status_response = client.get(f"/api/v1/campaigns/{campaign_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "active"

        # 5. Trigger optimization
        optimize_response = client.post(
            f"/api/v1/campaigns/{campaign_id}/optimize",
            json={"optimization_type": "full"},
        )
        assert optimize_response.status_code == 200
        assert optimize_response.json()["status"] == "completed"

        # 6. List campaigns and verify ours is there
        list_response = client.get("/api/v1/campaigns")
        assert list_response.status_code == 200
        campaign_ids = [c["id"] for c in list_response.json()["campaigns"]]
        assert campaign_id in campaign_ids

        # 7. Delete campaign
        delete_response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert delete_response.status_code == 204

        # 8. Verify deletion
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404

    def test_multiple_campaigns_pagination(self, client: TestClient) -> None:
        """Test pagination with multiple campaigns."""
        # Create multiple campaigns
        for i in range(5):
            client.post(
                "/api/v1/campaigns",
                json={
                    "name": f"Pagination Test {i}",
                    "goals": ["awareness"],
                    "total_budget": 1000.0,
                    "daily_budget": 100.0,
                    "channels": ["search"],
                    "duration_days": 10,
                },
            )

        # Test pagination
        response = client.get("/api/v1/campaigns?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["campaigns"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_concurrent_campaign_operations(self, client: TestClient) -> None:
        """Test that multiple campaigns can be created and managed independently."""
        campaign_ids = []

        # Create 3 campaigns
        for i in range(3):
            response = client.post(
                "/api/v1/campaigns",
                json={
                    "name": f"Concurrent Test {i}",
                    "goals": ["conversion"],
                    "total_budget": 5000.0,
                    "daily_budget": 500.0,
                    "channels": ["social"],
                    "duration_days": 10,
                },
            )
            assert response.status_code == 201
            campaign_ids.append(response.json()["id"])

        # Update each differently
        for i, cid in enumerate(campaign_ids):
            response = client.put(
                f"/api/v1/campaigns/{cid}",
                json={"name": f"Updated Concurrent {i}"},
            )
            assert response.status_code == 200

        # Verify all are independent
        for i, cid in enumerate(campaign_ids):
            response = client.get(f"/api/v1/campaigns/{cid}")
            assert response.status_code == 200
            assert response.json()["name"] == f"Updated Concurrent {i}"

        # Clean up
        for cid in campaign_ids:
            client.delete(f"/api/v1/campaigns/{cid}")


class TestAPIErrorHandling:
    """Integration tests for API error handling."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_invalid_json_body(self, client: TestClient) -> None:
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/api/v1/campaigns",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client: TestClient) -> None:
        """Test handling of missing content type."""
        response = client.post(
            "/api/v1/campaigns",
            content='{"name": "test"}',
        )
        assert response.status_code in (200, 201, 422)
