"""Tests for API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health and info endpoints."""

    def test_root_health(self, client: TestClient) -> None:
        """Test root health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_info(self, client: TestClient) -> None:
        """Test API info endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestTalentPoolEndpoints:
    """Tests for talent pool endpoints."""

    def test_create_pool(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test creating a talent pool."""
        response = client.post("/api/v1/pools", json=sample_pool_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_pool_data["name"]
        assert "id" in data

    def test_list_pools(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test listing talent pools."""
        # Create a pool first
        client.post("/api/v1/pools", json=sample_pool_data)

        response = client.get("/api/v1/pools")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_pool(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test getting a specific talent pool."""
        create_response = client.post("/api/v1/pools", json=sample_pool_data)
        pool_id = create_response.json()["id"]

        response = client.get(f"/api/v1/pools/{pool_id}")
        assert response.status_code == 200
        assert response.json()["id"] == pool_id

    def test_get_nonexistent_pool(self, client: TestClient) -> None:
        """Test getting a non-existent talent pool."""
        response = client.get(f"/api/v1/pools/{uuid4()}")
        assert response.status_code == 404

    def test_update_pool(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test updating a talent pool."""
        create_response = client.post("/api/v1/pools", json=sample_pool_data)
        pool_id = create_response.json()["id"]

        update_data = {"name": "Updated Pool Name"}
        response = client.put(f"/api/v1/pools/{pool_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Pool Name"

    def test_delete_pool(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test deleting a talent pool."""
        create_response = client.post("/api/v1/pools", json=sample_pool_data)
        pool_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/pools/{pool_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/pools/{pool_id}")
        assert get_response.status_code == 404

    def test_get_pool_stats(self, client: TestClient, sample_pool_data: dict) -> None:
        """Test getting pool statistics."""
        create_response = client.post("/api/v1/pools", json=sample_pool_data)
        pool_id = create_response.json()["id"]

        response = client.get(f"/api/v1/pools/{pool_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_candidates" in data
        assert "average_score" in data


class TestCandidateEndpoints:
    """Tests for candidate endpoints."""

    def test_create_candidate(self, client: TestClient, sample_candidate_data: dict) -> None:
        """Test creating a candidate."""
        # First create a pool
        pool_response = client.post(
            "/api/v1/pools",
            json={
                "name": "Test Pool",
                "organization_id": str(uuid4()),
            },
        )
        pool_id = pool_response.json()["id"]
        sample_candidate_data["pool_id"] = pool_id

        response = client.post("/api/v1/candidates", json=sample_candidate_data)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == sample_candidate_data["first_name"]
        assert "id" in data

    def test_list_candidates(self, client: TestClient) -> None:
        """Test listing candidates."""
        response = client.get("/api/v1/candidates")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_candidate(self, client: TestClient, sample_candidate_data: dict) -> None:
        """Test getting a specific candidate."""
        # Create pool and candidate
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]
        sample_candidate_data["pool_id"] = pool_id

        create_response = client.post("/api/v1/candidates", json=sample_candidate_data)
        candidate_id = create_response.json()["id"]

        response = client.get(f"/api/v1/candidates/{candidate_id}")
        assert response.status_code == 200
        assert response.json()["id"] == candidate_id

    def test_update_candidate(self, client: TestClient, sample_candidate_data: dict) -> None:
        """Test updating a candidate."""
        # Create pool and candidate
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]
        sample_candidate_data["pool_id"] = pool_id

        create_response = client.post("/api/v1/candidates", json=sample_candidate_data)
        candidate_id = create_response.json()["id"]

        update_data = {"headline": "Updated Headline"}
        response = client.put(f"/api/v1/candidates/{candidate_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["headline"] == "Updated Headline"

    def test_delete_candidate(self, client: TestClient, sample_candidate_data: dict) -> None:
        """Test deleting a candidate."""
        # Create pool and candidate
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]
        sample_candidate_data["pool_id"] = pool_id

        create_response = client.post("/api/v1/candidates", json=sample_candidate_data)
        candidate_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/candidates/{candidate_id}")
        assert response.status_code == 204


class TestSegmentEndpoints:
    """Tests for segment endpoints."""

    def test_create_segment(self, client: TestClient, sample_segment_data: dict) -> None:
        """Test creating a segment."""
        # Create pool first
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]
        sample_segment_data["pool_id"] = pool_id

        response = client.post("/api/v1/segments", json=sample_segment_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_segment_data["name"]

    def test_list_segments(self, client: TestClient) -> None:
        """Test listing segments."""
        response = client.get("/api/v1/segments")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestEngagementEndpoints:
    """Tests for engagement endpoints."""

    def test_create_engagement(self, client: TestClient, sample_engagement_data: dict) -> None:
        """Test creating an engagement."""
        # Create pool and candidate first
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]

        candidate_response = client.post(
            "/api/v1/candidates",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "pool_id": pool_id,
            },
        )
        candidate_id = candidate_response.json()["id"]
        sample_engagement_data["candidate_id"] = candidate_id

        response = client.post("/api/v1/engagements", json=sample_engagement_data)
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == sample_engagement_data["subject"]

    def test_list_engagements(self, client: TestClient) -> None:
        """Test listing engagements."""
        response = client.get("/api/v1/engagements")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestOutreachEndpoints:
    """Tests for outreach endpoints."""

    def test_create_outreach_template(
        self, client: TestClient, sample_outreach_template_data: dict
    ) -> None:
        """Test creating an outreach template."""
        response = client.post("/api/v1/outreach/templates", json=sample_outreach_template_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_outreach_template_data["name"]

    def test_list_outreach_templates(self, client: TestClient) -> None:
        """Test listing outreach templates."""
        response = client.get("/api/v1/outreach/templates")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_outreach_campaign(
        self, client: TestClient, sample_outreach_campaign_data: dict
    ) -> None:
        """Test creating an outreach campaign."""
        # Create template first
        template_response = client.post(
            "/api/v1/outreach/templates",
            json={
                "name": "Test Template",
                "subject_template": "Subject",
                "body_template": "Body",
            },
        )
        template_id = template_response.json()["id"]
        sample_outreach_campaign_data["template_id"] = template_id

        response = client.post("/api/v1/outreach/campaigns", json=sample_outreach_campaign_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_outreach_campaign_data["name"]

    def test_list_outreach_campaigns(self, client: TestClient) -> None:
        """Test listing outreach campaigns."""
        response = client.get("/api/v1/outreach/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestAgentEndpoints:
    """Tests for agent endpoints."""

    def test_discover_candidates(self, client: TestClient) -> None:
        """Test candidate discovery agent endpoint."""
        # Create pool first
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]

        request_data = {
            "pool_id": pool_id,
            "query": "Senior Python Engineer",
            "sources": ["linkedin", "github"],
            "max_results": 10,
        }
        response = client.post("/api/v1/agents/discover", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "candidates_found" in data
        assert "duration_seconds" in data

    def test_segment_pool(self, client: TestClient) -> None:
        """Test pool segmentation agent endpoint."""
        # Create pool first
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]

        request_data = {
            "pool_id": pool_id,
            "segment_count": 3,
            "segment_type": "skill_based",
        }
        response = client.post("/api/v1/agents/segment", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert "quality_score" in data

    def test_score_candidates(self, client: TestClient) -> None:
        """Test talent scoring agent endpoint."""
        request_data = {
            "candidate_ids": [str(uuid4())],
            "criteria": {"skills": ["Python"]},
        }
        response = client.post("/api/v1/agents/score", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "scores" in data
        assert "factors" in data

    def test_run_outreach(self, client: TestClient) -> None:
        """Test outreach agent endpoint."""
        # Create template first
        template_response = client.post(
            "/api/v1/outreach/templates",
            json={
                "name": "Test Template",
                "subject_template": "Subject",
                "body_template": "Body",
            },
        )
        template_id = template_response.json()["id"]

        request_data = {
            "campaign_id": str(uuid4()),
            "candidate_ids": [str(uuid4())],
            "template_id": template_id,
        }
        response = client.post("/api/v1/agents/outreach", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "messages_generated" in data

    def test_optimize_engagement(self, client: TestClient) -> None:
        """Test engagement optimization agent endpoint."""
        # Create pool first
        pool_response = client.post(
            "/api/v1/pools",
            json={"name": "Test Pool", "organization_id": str(uuid4())},
        )
        pool_id = pool_response.json()["id"]

        request_data = {
            "pool_id": pool_id,
            "optimization_goal": "response_rate",
        }
        response = client.post("/api/v1/agents/optimize-engagement", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "predicted_improvement" in data
