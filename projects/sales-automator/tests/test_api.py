"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sales_automator.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestProspectsEndpoint:
    """Tests for the prospects endpoints."""

    def test_create_prospect(self, client: TestClient) -> None:
        payload = {
            "name": "Jane Doe",
            "company": "Acme Corp",
            "title": "VP Sales",
            "email": "jane@acme.com",
        }
        response = client.post("/api/v1/prospects", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["company"] == "Acme Corp"
        assert "id" in data

    def test_list_prospects(self, client: TestClient) -> None:
        response = client.get("/api/v1/prospects")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_prospect(self, client: TestClient) -> None:
        payload = {"name": "Test", "company": "TestCo"}
        create_resp = client.post("/api/v1/prospects", json=payload)
        prospect_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/prospects/{prospect_id}")
        assert response.status_code == 200
        assert response.json()["id"] == prospect_id

    def test_get_prospect_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/prospects/nonexistent")
        assert response.status_code == 404

    def test_score_prospect(self, client: TestClient) -> None:
        payload = {"name": "Test", "company": "TestCo"}
        create_resp = client.post("/api/v1/prospects", json=payload)
        prospect_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/prospects/{prospect_id}/score")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data


class TestSequencesEndpoint:
    """Tests for the sequences endpoints."""

    def test_create_sequence(self, client: TestClient) -> None:
        payload = {
            "name": "Test Sequence",
            "prospect_id": "p1",
            "steps": 3,
        }
        response = client.post("/api/v1/sequences", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Sequence"
        assert len(data["steps"]) == 3

    def test_list_sequences(self, client: TestClient) -> None:
        response = client.get("/api/v1/sequences")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_sequence_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/sequences/nonexistent")
        assert response.status_code == 404

    def test_enroll_prospect(self, client: TestClient) -> None:
        payload = {"name": "Test", "prospect_id": "p1", "steps": 2}
        create_resp = client.post("/api/v1/sequences", json=payload)
        sequence_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/sequences/{sequence_id}/enroll",
            json={"prospect_id": "p2"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "enrolled"
