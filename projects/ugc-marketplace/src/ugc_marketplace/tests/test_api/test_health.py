"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ugc_marketplace.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client.

    Returns:
        FastAPI test client.
    """
    app = create_app()
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_check(client: TestClient) -> None:
    """Test readiness check endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200


def test_liveness_check(client: TestClient) -> None:
    """Test liveness check endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
