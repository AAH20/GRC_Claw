"""Tests for the main application module."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app, create_app


class TestAppCreation:
    """Tests for application creation."""

    def test_create_app_returns_fastapi_instance(self) -> None:
        """Test that create_app returns a FastAPI instance."""
        from fastapi import FastAPI

        result = create_app()
        assert isinstance(result, FastAPI)

    def test_app_has_expected_routes(self) -> None:
        """Test that the app has the expected routes registered."""
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/health/ready" in routes
        assert "/api/v1/workflows" in routes
        assert "/api/v1/domains" in routes
        assert "/api/v1/agents" in routes
        assert "/api/v1/analytics/summary" in routes


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test the readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data
