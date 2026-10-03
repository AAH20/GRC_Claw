"""Tests for audit API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_list_audits_empty(client: TestClient) -> None:
    """Test listing audits when none exist."""
    response = client.get("/api/v1/audits")
    assert response.status_code == 200
    assert response.json() == []


def test_generate_audit(client: TestClient) -> None:
    """Test generating an audit report."""
    audit_data = {
        "title": "Q4 2024 Compliance Audit",
        "description": "Quarterly compliance audit",
        "period_start": datetime.now(tz=UTC).isoformat(),
        "period_end": (datetime.now(tz=UTC) + timedelta(days=90)).isoformat(),
    }
    response = client.post("/api/v1/audits", json=audit_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == audit_data["title"]
    assert "id" in data


def test_get_audit(client: TestClient) -> None:
    """Test getting an audit report by ID."""
    audit_data = {
        "title": "Test Audit",
        "period_start": datetime.now(tz=UTC).isoformat(),
        "period_end": (datetime.now(tz=UTC) + timedelta(days=30)).isoformat(),
    }
    create_response = client.post("/api/v1/audits", json=audit_data)
    audit_id = create_response.json()["id"]

    response = client.get(f"/api/v1/audits/{audit_id}")
    assert response.status_code == 200
    assert response.json()["id"] == audit_id


def test_get_audit_not_found(client: TestClient) -> None:
    """Test getting a non-existent audit report."""
    response = client.get("/api/v1/audits/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
