"""Agent endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_agents_status(client: TestClient) -> None:
    """Test getting agent statuses.

    Args:
        client: Test client fixture.
    """
    response = client.get(
        "/v1/agents/status",
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "overall_status" in data
    assert len(data["agents"]) == 5
