"""Tests for the health check endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the health endpoint returns 200 with correct structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check(client: TestClient) -> None:
    """Test the readiness endpoint returns 200."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_liveness_check(client: TestClient) -> None:
    """Test the liveness endpoint returns 200."""
    response = client.get("/api/v1/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True
