"""Tests for health check endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient) -> None:
    """Test the health check endpoint.

    Args:
        test_client: Test client fixture.
    """
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "checks" in data


def test_readiness_check(test_client: TestClient) -> None:
    """Test the readiness check endpoint.

    Args:
        test_client: Test client fixture.
    """
    response = test_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data
