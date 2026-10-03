"""
Health check endpoint tests for the recruitment-platform API.

Tests cover:
- GET /health  — basic health status
- GET /ready   — readiness probe
- GET /live    — liveness probe
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Return a TestClient bound to the FastAPI app."""
    from app.main import app  # adjust import to your actual app factory
    return TestClient(app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """Tests for the GET /health endpoint."""

    def test_health_check_returns_200(self, client):
        """GET /health must return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_json(self, client):
        """GET /health must return a JSON body."""
        response = client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

    def test_health_check_has_status_field(self, client):
        """GET /health response must include a 'status' field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_check_status_is_healthy(self, client):
        """GET /health 'status' value should be 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_response_is_dict(self, client):
        """GET /health response body must be a JSON object."""
        response = client.get("/health")
        assert isinstance(response.json(), dict)

    def test_health_check_no_auth_required(self, client):
        """GET /health must be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code != 401
        assert response.status_code != 403


# ---------------------------------------------------------------------------
# /ready
# ---------------------------------------------------------------------------

class TestReadinessCheck:
    """Tests for the GET /ready endpoint."""

    def test_readiness_check_returns_200(self, client):
        """GET /ready must return HTTP 200."""
        response = client.get("/ready")
        assert response.status_code == 200

    def test_readiness_check_returns_json(self, client):
        """GET /ready must return a JSON body."""
        response = client.get("/ready")
        assert response.headers["content-type"].startswith("application/json")

    def test_readiness_check_has_ready_field(self, client):
        """GET /ready response must include a 'ready' field."""
        response = client.get("/ready")
        data = response.json()
        assert "ready" in data

    def test_readiness_check_ready_is_true(self, client):
        """GET /ready 'ready' value should be True."""
        response = client.get("/ready")
        data = response.json()
        assert data["ready"] is True

    def test_readiness_check_response_is_dict(self, client):
        """GET /ready response body must be a JSON object."""
        response = client.get("/ready")
        assert isinstance(response.json(), dict)

    def test_readiness_check_no_auth_required(self, client):
        """GET /ready must be accessible without authentication."""
        response = client.get("/ready")
        assert response.status_code != 401
        assert response.status_code != 403


# ---------------------------------------------------------------------------
# /live
# ---------------------------------------------------------------------------

class TestLivenessCheck:
    """Tests for the GET /live endpoint."""

    def test_liveness_check_returns_200(self, client):
        """GET /live must return HTTP 200."""
        response = client.get("/live")
        assert response.status_code == 200

    def test_liveness_check_returns_json(self, client):
        """GET /live must return a JSON body."""
        response = client.get("/live")
        assert response.headers["content-type"].startswith("application/json")

    def test_liveness_check_has_alive_field(self, client):
        """GET /live response must include an 'alive' field."""
        response = client.get("/live")
        data = response.json()
        assert "alive" in data

    def test_liveness_check_alive_is_true(self, client):
        """GET /live 'alive' value should be True."""
        response = client.get("/live")
        data = response.json()
        assert data["alive"] is True

    def test_liveness_check_response_is_dict(self, client):
        """GET /live response body must be a JSON object."""
        response = client.get("/live")
        assert isinstance(response.json(), dict)

    def test_liveness_check_no_auth_required(self, client):
        """GET /live must be accessible without authentication."""
        response = client.get("/live")
        assert response.status_code != 401
        assert response.status_code != 403
