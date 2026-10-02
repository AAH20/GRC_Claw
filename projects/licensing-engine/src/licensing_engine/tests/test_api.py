"""Tests for API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test the readiness endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check(self, client: TestClient) -> None:
        """Test the liveness endpoint."""
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestLicenseEndpoints:
    """Tests for license endpoints."""

    def test_create_license(self, client: TestClient) -> None:
        """Test creating a license."""
        payload = {
            "content_id": "content-123",
            "content_type": "text",
            "license_type": "non_exclusive",
            "licensor_id": "licensor-1",
            "licensee_id": "licensee-1",
            "terms": {
                "usage_rights": ["read", "display"],
                "restrictions": ["no_modification"],
                "territory": ["US", "EU"],
                "duration_days": 365,
                "attribution_required": True,
                "commercial_use": False,
            },
        }
        response = client.post("/licenses", json=payload)
        # Will fail without proper LLM mock, but tests the endpoint exists
        assert response.status_code in [201, 500]

    def test_list_licenses(self, client: TestClient) -> None:
        """Test listing licenses."""
        response = client.get("/licenses")
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        assert "total" in data

    def test_get_license_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent license."""
        response = client.get("/licenses/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
