"""Tests for escalation workflow API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthAPI:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test readiness probe endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data


class TestEscalationsAPI:
    """Tests for escalation management endpoints."""

    def test_create_escalation(self, client: TestClient, sample_escalation_data: dict) -> None:
        """Test creating a new escalation."""
        response = client.post("/escalations", json=sample_escalation_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_escalation_data["title"]
        assert data["status"] == "pending"
        assert "id" in data

    def test_list_escalations(self, client: TestClient) -> None:
        """Test listing escalations."""
        response = client.get("/escalations")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_escalation_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent escalation."""
        response = client.get("/escalations/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_update_escalation(self, client: TestClient, sample_escalation_data: dict) -> None:
        """Test updating an escalation."""
        create_response = client.post("/escalations", json=sample_escalation_data)
        escalation_id = create_response.json()["id"]

        update_data = {"priority": "critical", "status": "in_progress"}
        response = client.patch(f"/escalations/{escalation_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "critical"
        assert data["status"] == "in_progress"

    def test_delete_escalation(self, client: TestClient, sample_escalation_data: dict) -> None:
        """Test deleting an escalation."""
        create_response = client.post("/escalations", json=sample_escalation_data)
        escalation_id = create_response.json()["id"]

        response = client.delete(f"/escalations/{escalation_id}")
        assert response.status_code == 204

        get_response = client.get(f"/escalations/{escalation_id}")
        assert get_response.status_code == 404

    def test_bulk_create_escalations(self, client: TestClient) -> None:
        """Test bulk creating escalations."""
        data = {
            "escalations": [
                {"title": "Bulk 1", "description": "Test 1", "requester": "user1"},
                {"title": "Bulk 2", "description": "Test 2", "requester": "user2"},
            ]
        }
        response = client.post("/escalations/bulk", json=data)
        assert response.status_code == 201
        assert len(response.json()) == 2


class TestPrioritiesAPI:
    """Tests for priority management endpoints."""

    def test_list_priorities(self, client: TestClient) -> None:
        """Test listing all priorities."""
        response = client.get("/priorities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4

    def test_get_priority(self, client: TestClient) -> None:
        """Test getting a specific priority."""
        response = client.get("/priorities/high")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "high"

    def test_get_priority_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent priority."""
        response = client.get("/priorities/invalid")
        assert response.status_code == 422


class TestSLAAPI:
    """Tests for SLA tracking endpoints."""

    def test_track_sla(self, client: TestClient) -> None:
        """Test creating SLA tracking."""
        response = client.post(
            "/sla/track?escalation_id=123e4567-e89b-12d3-a456-426614174000&priority=high"
        )
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "high"
        assert data["status"] == "active"

    def test_list_slas(self, client: TestClient) -> None:
        """Test listing SLAs."""
        response = client.get("/sla")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_sla_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent SLA."""
        response = client.get("/sla/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404


class TestResolutionsAPI:
    """Tests for resolution management endpoints."""

    def test_create_resolution(self, client: TestClient, sample_resolution_data: dict) -> None:
        """Test creating a resolution."""
        response = client.post("/resolutions", json=sample_resolution_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_resolution_data["title"]

    def test_list_resolutions(self, client: TestClient) -> None:
        """Test listing resolutions."""
        response = client.get("/resolutions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_resolution_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent resolution."""
        response = client.get("/resolutions/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_approve_resolution(self, client: TestClient, sample_resolution_data: dict) -> None:
        """Test approving a resolution."""
        create_response = client.post("/resolutions", json=sample_resolution_data)
        resolution_id = create_response.json()["id"]

        response = client.post(f"/resolutions/{resolution_id}/approve")
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
