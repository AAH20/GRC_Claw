"""Tests for the API endpoints."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from workflow_automation.agents.workflow_discovery import WorkflowType
from workflow_automation.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestMetricsEndpoint:
    """Tests for the metrics endpoint."""

    def test_metrics_endpoint(self, client: TestClient) -> None:
        """Test metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestWorkflowDiscoveryEndpoints:
    """Tests for workflow discovery endpoints."""

    def test_discover_workflows(self, client: TestClient) -> None:
        """Test workflow discovery endpoint."""
        response = client.post(
            "/api/v1/workflows/discover",
            json={
                "sources": ["n8n"],
                "workflow_types": ["lead_generation"],
                "max_results": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "discovery_id" in data
        assert "workflows" in data
        assert "total_found" in data
        assert "sources_queried" in data

    def test_discover_workflows_empty_sources(self, client: TestClient) -> None:
        """Test discovery with empty sources defaults to all."""
        response = client.post(
            "/api/v1/workflows/discover",
            json={"sources": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources_queried"]) == 3

    def test_list_workflows(self, client: TestClient) -> None:
        """Test listing workflows."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_workflows_with_filters(self, client: TestClient) -> None:
        """Test listing workflows with query filters."""
        response = client.get("/api/v1/workflows?source=n8n&status=active")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_workflow_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent workflow."""
        response = client.get("/api/v1/workflows/non-existent-id")
        assert response.status_code == 404

    def test_optimize_workflow_not_found(self, client: TestClient) -> None:
        """Test optimizing a non-existent workflow."""
        response = client.post(
            "/api/v1/workflows/non-existent-id/optimize",
            json={},
        )
        assert response.status_code == 404

    def test_refresh_workflow_not_found(self, client: TestClient) -> None:
        """Test refreshing a non-existent workflow."""
        response = client.post("/api/v1/workflows/non-existent-id/refresh")
        assert response.status_code == 404


class TestProcessEndpoints:
    """Tests for process automation endpoints."""

    def test_create_process(self, client: TestClient) -> None:
        """Test creating a process."""
        response = client.post(
            "/api/v1/processes",
            json={
                "name": "Test Process",
                "description": "A test process",
                "process_type": "data_sync",
                "steps": [
                    {
                        "name": "step1",
                        "action": "http_request",
                        "config": {"url": "https://example.com"},
                        "order": 0,
                    }
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Process"
        assert data["process_type"] == "data_sync"
        assert len(data["steps"]) == 1

    def test_list_processes(self, client: TestClient) -> None:
        """Test listing processes."""
        response = client.get("/api/v1/processes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_process_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent process."""
        response = client.get("/api/v1/processes/non-existent-id")
        assert response.status_code == 404

    def test_execute_process_not_found(self, client: TestClient) -> None:
        """Test executing a non-existent process."""
        response = client.post(
            "/api/v1/processes/non-existent-id/execute",
            json={},
        )
        assert response.status_code == 404

    def test_list_executions(self, client: TestClient) -> None:
        """Test listing executions for a process."""
        response = client.get("/api/v1/processes/non-existent-id/executions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_cancel_execution_not_found(self, client: TestClient) -> None:
        """Test cancelling a non-existent execution."""
        response = client.post("/api/v1/processes/executions/non-existent-id/cancel")
        assert response.status_code == 400


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json_body(self, client: TestClient) -> None:
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/api/v1/workflows/discover",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient) -> None:
        """Test validation of required fields."""
        response = client.post(
            "/api/v1/processes",
            json={"description": "missing name and type"},
        )
        assert response.status_code == 422
