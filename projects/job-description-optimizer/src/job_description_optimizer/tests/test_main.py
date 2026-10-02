"""Tests for the main application module."""

from fastapi.testclient import TestClient

from job_description_optimizer.config import Settings
from job_description_optimizer.main import create_app


class TestAppFactory:
    """Tests for the application factory."""

    def test_create_app_returns_fastapi(self, settings: Settings) -> None:
        """Test that create_app returns a FastAPI instance."""
        from fastapi import FastAPI

        app = create_app(settings=settings)
        assert isinstance(app, FastAPI)

    def test_create_app_with_default_settings(self) -> None:
        """Test that create_app works with default settings."""
        from fastapi import FastAPI

        app = create_app()
        assert isinstance(app, FastAPI)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check returns 200 status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_format(self, client: TestClient) -> None:
        """Test that health check returns correct response format."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self, client: TestClient) -> None:
        """Test that root endpoint returns 200 status."""
        response = client.get("/api/v1/")
        assert response.status_code == 200

    def test_root_returns_service_info(self, client: TestClient) -> None:
        """Test that root endpoint returns service information."""
        response = client.get("/api/v1/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_endpoint(self, client: TestClient) -> None:
        """Test that unknown endpoints return 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_invalid_agent_name_returns_404(self, client: TestClient) -> None:
        """Test that invalid agent name returns 404."""
        response = client.get("/api/v1/agents/nonexistent")
        assert response.status_code == 404
