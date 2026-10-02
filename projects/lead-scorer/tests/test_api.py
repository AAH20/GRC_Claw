"""Tests for lead scorer API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lead_scorer.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestLeadEndpoints:
    """Tests for lead management endpoints."""

    def test_create_lead(self, client: TestClient) -> None:
        """Test creating a new lead."""
        response = client.post(
            "/api/v1/leads",
            json={
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Example Corp",
                "domain": "example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["id"] != ""

    def test_create_lead_invalid_email(self, client: TestClient) -> None:
        """Test creating a lead with invalid email."""
        response = client.post(
            "/api/v1/leads",
            json={"email": "invalid-email"},
        )
        assert response.status_code == 422

    def test_get_lead(self, client: TestClient) -> None:
        """Test getting a lead by ID."""
        # Create a lead first
        create_response = client.post(
            "/api/v1/leads",
            json={"email": "get@example.com", "first_name": "Jane"},
        )
        lead_id = create_response.json()["data"]["id"]

        # Get the lead
        response = client.get(f"/api/v1/leads/{lead_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "get@example.com"

    def test_get_lead_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent lead."""
        response = client.get("/api/v1/leads/nonexistent")
        assert response.status_code == 404

    def test_delete_lead(self, client: TestClient) -> None:
        """Test deleting a lead."""
        # Create a lead first
        create_response = client.post(
            "/api/v1/leads",
            json={"email": "delete@example.com"},
        )
        lead_id = create_response.json()["data"]["id"]

        # Delete the lead
        response = client.delete(f"/api/v1/leads/{lead_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/leads/{lead_id}")
        assert get_response.status_code == 404


class TestScoringEndpoints:
    """Tests for scoring endpoints."""

    def test_batch_score(self, client: TestClient) -> None:
        """Test batch scoring endpoint."""
        response = client.post(
            "/api/v1/scoring/batch",
            json={
                "leads": [
                    {
                        "lead_id": "lead-1",
                        "domain": "example.com",
                        "company_name": "Example Corp",
                    },
                    {
                        "lead_id": "lead-2",
                        "domain": "test.com",
                        "company_name": "Test Inc",
                    },
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert len(data["results"]) == 2

    def test_batch_score_empty_list(self, client: TestClient) -> None:
        """Test batch scoring with empty list."""
        response = client.post(
            "/api/v1/scoring/batch",
            json={"leads": []},
        )
        assert response.status_code == 422


class TestEnrichmentEndpoints:
    """Tests for enrichment endpoints."""

    def test_enrich_lead(self, client: TestClient) -> None:
        """Test lead enrichment endpoint."""
        response = client.post(
            "/api/v1/leads/lead-enrich-1/enrich",
            json={
                "lead_id": "lead-enrich-1",
                "domain": "enrich-example.com",
                "company_name": "Enrich Example",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["lead_id"] == "lead-enrich-1"
        assert data["research"] is not None
        assert data["evidence"] is not None

    def test_enrich_lead_missing_domain(self, client: TestClient) -> None:
        """Test enrichment with missing domain."""
        response = client.post(
            "/api/v1/leads/lead-enrich-2/enrich",
            json={"lead_id": "lead-enrich-2", "domain": ""},
        )
        assert response.status_code == 422
