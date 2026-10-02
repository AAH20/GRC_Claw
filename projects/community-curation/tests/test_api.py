"""Tests for the API routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check returns 200 status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_returns_ok_status(self, client: TestClient) -> None:
        """Test that health check returns ok status."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_includes_version(self, client: TestClient) -> None:
        """Test that health check includes version."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "version" in data

    def test_health_check_includes_agents(self, client: TestClient) -> None:
        """Test that health check includes agents list."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 5


class TestAgentsEndpoint:
    """Tests for the agents endpoint."""

    def test_list_agents_returns_200(self, client: TestClient) -> None:
        """Test that agents endpoint returns 200."""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200

    def test_list_agents_returns_five_agents(self, client: TestClient) -> None:
        """Test that agents endpoint returns 5 agents."""
        response = client.get("/api/v1/agents")
        data = response.json()
        assert len(data) == 5

    def test_agents_have_required_fields(self, client: TestClient) -> None:
        """Test that each agent has required fields."""
        response = client.get("/api/v1/agents")
        data = response.json()
        for agent in data:
            assert "name" in agent
            assert "description" in agent
            assert "status" in agent
            assert "capabilities" in agent


class TestCurationEndpoint:
    """Tests for the curation endpoint."""

    def test_curate_returns_200(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that curate endpoint returns 200."""
        response = client.post("/api/v1/curate", json=sample_curation_request)
        assert response.status_code == 200

    def test_curate_returns_result_structure(
        self, client: TestClient, sample_curation_request: dict
    ) -> None:
        """Test that curate returns proper result structure."""
        response = client.post("/api/v1/curate", json=sample_curation_request)
        data = response.json()
        assert "request_id" in data
        assert "query" in data
        assert "ranked_content" in data
        assert "trends" in data
        assert "clusters" in data
        assert "quality_filtered" in data
        assert "explanation" in data
        assert "total_candidates" in data
        assert "processing_time_ms" in data

    def test_curate_validates_query_required(self, client: TestClient) -> None:
        """Test that curate validates query is required."""
        response = client.post("/api/v1/curate", json={"sources": ["reddit"]})
        assert response.status_code == 422

    def test_curate_validates_limit_range(self, client: TestClient) -> None:
        """Test that curate validates limit range."""
        request = {
            "query": "test",
            "limit": 200,  # Exceeds max of 100
        }
        response = client.post("/api/v1/curate", json=request)
        assert response.status_code == 422


class TestRankEndpoint:
    """Tests for the rank endpoint."""

    def test_rank_returns_200(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that rank endpoint returns 200."""
        response = client.post("/api/v1/rank", json=sample_curation_request)
        assert response.status_code == 200

    def test_rank_returns_list(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that rank endpoint returns a list."""
        response = client.post("/api/v1/rank", json=sample_curation_request)
        data = response.json()
        assert isinstance(data, list)


class TestTrendsEndpoint:
    """Tests for the trends endpoint."""

    def test_trends_returns_200(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that trends endpoint returns 200."""
        response = client.post("/api/v1/trends", json=sample_curation_request)
        assert response.status_code == 200

    def test_trends_returns_list(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that trends endpoint returns a list."""
        response = client.post("/api/v1/trends", json=sample_curation_request)
        data = response.json()
        assert isinstance(data, list)


class TestFilterEndpoint:
    """Tests for the filter endpoint."""

    def test_filter_returns_200(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that filter endpoint returns 200."""
        response = client.post("/api/v1/filter", json=sample_curation_request)
        assert response.status_code == 200

    def test_filter_returns_list(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that filter endpoint returns a list."""
        response = client.post("/api/v1/filter", json=sample_curation_request)
        data = response.json()
        assert isinstance(data, list)


class TestClusterEndpoint:
    """Tests for the cluster endpoint."""

    def test_cluster_returns_200(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that cluster endpoint returns 200."""
        response = client.post("/api/v1/cluster", json=sample_curation_request)
        assert response.status_code == 200

    def test_cluster_returns_list(self, client: TestClient, sample_curation_request: dict) -> None:
        """Test that cluster endpoint returns a list."""
        response = client.post("/api/v1/cluster", json=sample_curation_request)
        data = response.json()
        assert isinstance(data, list)


class TestMetricsEndpoint:
    """Tests for the metrics endpoint."""

    def test_metrics_returns_200(self, client: TestClient) -> None:
        """Test that metrics endpoint returns 200."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

    def test_metrics_returns_dict(self, client: TestClient) -> None:
        """Test that metrics endpoint returns a dictionary."""
        response = client.get("/api/v1/metrics")
        data = response.json()
        assert isinstance(data, dict)
        assert "app_name" in data
        assert "app_version" in data
