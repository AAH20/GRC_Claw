"""Tests for report endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_report(client: TestClient) -> None:
    """Test creating a new report.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/reports",
        json={
            "title": "Test Report",
            "description": "Test description",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Report"
    assert data["status"] == "pending"
    assert "report_id" in data


def test_list_reports(client: TestClient) -> None:
    """Test listing reports.

    Args:
        client: Test client fixture.
    """
    # Create a report first
    client.post(
        "/api/v1/reports",
        json={"title": "Test Report", "description": "Test"},
    )
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_report(client: TestClient) -> None:
    """Test getting a specific report.

    Args:
        client: Test client fixture.
    """
    # Create a report first
    create_response = client.post(
        "/api/v1/reports",
        json={"title": "Test Report", "description": "Test"},
    )
    report_id = create_response.json()["report_id"]

    response = client.get(f"/api/v1/reports/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == report_id


def test_get_report_not_found(client: TestClient) -> None:
    """Test getting a non-existent report returns 404.

    Args:
        client: Test client fixture.
    """
    response = client.get("/api/v1/reports/nonexistent")
    assert response.status_code == 404


def test_delete_report(client: TestClient) -> None:
    """Test deleting a report.

    Args:
        client: Test client fixture.
    """
    # Create a report first
    create_response = client.post(
        "/api/v1/reports",
        json={"title": "Test Report", "description": "Test"},
    )
    report_id = create_response.json()["report_id"]

    response = client.delete(f"/api/v1/reports/{report_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/reports/{report_id}")
    assert get_response.status_code == 404
