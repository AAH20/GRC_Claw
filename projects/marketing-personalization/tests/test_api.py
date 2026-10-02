"""Tests for personalization API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from personalization.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCampaignEndpoints:
    def test_create_campaign(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/campaigns",
            json={"name": "Test Campaign", "campaign_type": "email"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["campaign_id"] is not None

    def test_list_campaigns(self, client: TestClient) -> None:
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_campaign_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/campaigns/nonexistent")
        assert response.status_code == 404


class TestSegmentEndpoints:
    def test_create_segment(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/segments",
            json={"name": "Test Segment", "segment_type": "dynamic"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Segment"

    def test_list_segments(self, client: TestClient) -> None:
        response = client.get("/api/v1/segments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
