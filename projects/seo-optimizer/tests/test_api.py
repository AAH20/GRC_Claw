"""Tests for SEO Optimizer API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from seo_optimizer.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_format(self, client: TestClient) -> None:
        """Test that health check returns correct format."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestKeywordEndpoints:
    """Test cases for keyword research endpoints."""

    def test_research_keywords_returns_202(self, client: TestClient) -> None:
        """Test that keyword research endpoint returns 202."""
        response = client.post(
            "/api/v1/keywords/research",
            json={
                "domain": "example.com",
                "seed_keywords": ["seo"],
                "max_results": 10,
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_research_keywords_validation(self, client: TestClient) -> None:
        """Test that keyword research validates input."""
        response = client.post(
            "/api/v1/keywords/research",
            json={"domain": ""},
        )
        assert response.status_code == 422

    def test_get_research_results_not_found(self, client: TestClient) -> None:
        """Test that getting non-existent task returns 404."""
        response = client.get("/api/v1/keywords/non-existent-id")
        assert response.status_code == 404


class TestContentEndpoints:
    """Test cases for content optimization endpoints."""

    def test_optimize_content_returns_202(self, client: TestClient) -> None:
        """Test that content optimization endpoint returns 202."""
        response = client.post(
            "/api/v1/content/optimize",
            json={
                "content": "This is test content for SEO optimization.",
                "target_keywords": ["seo"],
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_optimize_content_validation(self, client: TestClient) -> None:
        """Test that content optimization validates input."""
        response = client.post(
            "/api/v1/content/optimize",
            json={"content": "", "target_keywords": []},
        )
        assert response.status_code == 422

    def test_get_optimization_results_not_found(self, client: TestClient) -> None:
        """Test that getting non-existent task returns 404."""
        response = client.get("/api/v1/content/non-existent-id")
        assert response.status_code == 404


class TestMetricsEndpoint:
    """Test cases for Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
