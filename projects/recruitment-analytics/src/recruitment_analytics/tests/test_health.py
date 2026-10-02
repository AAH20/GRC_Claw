"""Tests for health check endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient




class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, test_client: TestClient) -> None:
        """Test health check returns 200."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, test_client: TestClient) -> None:
        """Test readiness check returns 200."""
        response = test_client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check(self, test_client: TestClient) -> None:
        """Test liveness check returns 200."""
        response = test_client.get("/api/v1/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
