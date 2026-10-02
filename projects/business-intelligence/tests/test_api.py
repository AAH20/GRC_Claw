"""Tests for business intelligence API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from business_intelligence.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
