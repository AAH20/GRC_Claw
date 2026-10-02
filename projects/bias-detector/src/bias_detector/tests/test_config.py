"""Tests for config endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_config(client: TestClient) -> None:
    """Test config endpoint returns configuration.

    Args:
        client: Test client fixture.
    """
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "app_version" in data
    assert "app_env" in data
