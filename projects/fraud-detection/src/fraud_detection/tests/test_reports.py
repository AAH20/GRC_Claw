"""Report endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_report_not_found(client: TestClient) -> None:
    """Test getting a non-existent report.

    Args:
        client: Test client fixture.
    """
    response = client.get(
        "/v1/reports/nonexistent",
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 404


def test_list_reports(client: TestClient) -> None:
    """Test listing reports.

    Args:
        client: Test client fixture.
    """
    response = client.get(
        "/v1/reports",
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
