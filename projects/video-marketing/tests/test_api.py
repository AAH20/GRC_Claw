"""Tests for Video Marketing API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from video_marketing.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "video-marketing-api"

    def test_readiness_check(self, client: TestClient) -> None:
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_root_endpoint(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Video Marketing API"
        assert "version" in data


class TestVideoEndpoints:
    """Tests for video API endpoints."""

    def test_create_video(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/videos",
            json={
                "title": "Test Video",
                "topic": "AI in Marketing",
                "description": "A test video about AI",
                "target_duration_seconds": 120.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Video"
        assert data["topic"] == "AI in Marketing"
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_video_validation_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/videos",
            json={"title": "", "topic": "Test"},
        )
        assert response.status_code == 422

    def test_list_videos(self, client: TestClient) -> None:
        # Create a video first
        client.post(
            "/api/v1/videos",
            json={"title": "List Test", "topic": "Testing"},
        )

        response = client.get("/api/v1/videos")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_video(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Get Test", "topic": "Testing"},
        )
        video_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        assert data["title"] == "Get Test"

    def test_get_video_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/videos/nonexistent-id")
        assert response.status_code == 404

    def test_update_video(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Update Test", "topic": "Testing"},
        )
        video_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/v1/videos/{video_id}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_delete_video(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Delete Test", "topic": "Testing"},
        )
        video_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/videos/{video_id}")
        assert response.status_code == 204

        # Verify deletion
        get_resp = client.get(f"/api/v1/videos/{video_id}")
        assert get_resp.status_code == 404

    def test_generate_script(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={
                "title": "Script Test",
                "topic": "AI in Marketing",
                "target_duration_seconds": 60.0,
            },
        )
        video_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/videos/{video_id}/generate-script")
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert data["status"] == "completed"
        assert "script" in data
        assert "title" in data["script"]
        assert "sections" in data["script"]

    def test_start_production_without_script_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Prod Test", "topic": "Testing"},
        )
        video_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/videos/{video_id}/start-production")
        assert response.status_code == 400

    def test_start_production_with_script(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Prod Test 2", "topic": "Testing", "target_duration_seconds": 60.0},
        )
        video_id = create_resp.json()["id"]

        # Generate script first
        client.post(f"/api/v1/videos/{video_id}/generate-script")

        response = client.post(f"/api/v1/videos/{video_id}/start-production")
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert "production_id" in data

    def test_get_video_status(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/videos",
            json={"title": "Status Test", "topic": "Testing"},
        )
        video_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/videos/{video_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert data["status"] == "draft"
        assert data["has_script"] is False


class TestCampaignEndpoints:
    """Tests for campaign API endpoints."""

    def test_create_campaign(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Test Campaign",
                "description": "A test campaign",
                "budget": 10000.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_campaign_validation_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/campaigns",
            json={"name": ""},
        )
        assert response.status_code == 422

    def test_list_campaigns(self, client: TestClient) -> None:
        client.post(
            "/api/v1/campaigns",
            json={"name": "List Campaign Test"},
        )

        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert data["total"] >= 1

    def test_get_campaign(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Get Campaign Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/campaigns/nonexistent-id")
        assert response.status_code == 404

    def test_update_campaign(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Update Campaign Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/v1/campaigns/{campaign_id}",
            json={"name": "Updated Campaign Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign Name"

    def test_delete_campaign(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Delete Campaign Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 204

        get_resp = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_resp.status_code == 404

    def test_add_video_to_campaign(self, client: TestClient) -> None:
        # Create campaign
        campaign_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Video Add Test"},
        )
        campaign_id = campaign_resp.json()["id"]

        # Create video
        video_resp = client.post(
            "/api/v1/videos",
            json={"title": "Campaign Video", "topic": "Testing"},
        )
        video_id = video_resp.json()["id"]

        response = client.post(
            f"/api/v1/campaigns/{campaign_id}/videos",
            json={"video_id": video_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert video_id in data["video_ids"]
        assert data["video_count"] == 1

    def test_remove_video_from_campaign(self, client: TestClient) -> None:
        # Create campaign and video
        campaign_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Video Remove Test"},
        )
        campaign_id = campaign_resp.json()["id"]

        video_resp = client.post(
            "/api/v1/videos",
            json={"title": "Remove Video", "topic": "Testing"},
        )
        video_id = video_resp.json()["id"]

        # Add video
        client.post(
            f"/api/v1/campaigns/{campaign_id}/videos",
            json={"video_id": video_id},
        )

        # Remove video
        response = client.delete(
            f"/api/v1/campaigns/{campaign_id}/videos/{video_id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert video_id not in data["video_ids"]
        assert data["video_count"] == 0

    def test_launch_campaign(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Launch Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/campaigns/{campaign_id}/launch")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_launch_already_active_campaign_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Double Launch Test"},
        )
        campaign_id = create_resp.json()["id"]

        client.post(f"/api/v1/campaigns/{campaign_id}/launch")

        response = client.post(f"/api/v1/campaigns/{campaign_id}/launch")
        assert response.status_code == 400

    def test_pause_campaign(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Pause Test"},
        )
        campaign_id = create_resp.json()["id"]

        client.post(f"/api/v1/campaigns/{campaign_id}/launch")

        response = client.post(f"/api/v1/campaigns/{campaign_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    def test_pause_inactive_campaign_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Pause Inactive Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/campaigns/{campaign_id}/pause")
        assert response.status_code == 400

    def test_get_campaign_analytics(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/campaigns",
            json={"name": "Analytics Test"},
        )
        campaign_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/campaigns/{campaign_id}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert "total_views" in data
        assert "overall_engagement_rate" in data
