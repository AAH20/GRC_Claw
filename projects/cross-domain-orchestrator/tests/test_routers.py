"""Tests for API routers."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.domain import DomainRequest
from app.models.workflow import Workflow, WorkflowStep


class TestHealthRouter:
    """Tests for health endpoints."""

    def test_health_endpoint(self, client: TestClient) -> None:
        """Test the health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_endpoint(self, client: TestClient) -> None:
        """Test the readiness endpoint returns 200."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True


class TestWorkflowRouter:
    """Tests for workflow endpoints."""

    def test_create_workflow(self, client: TestClient) -> None:
        """Test creating a workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test description",
            "steps": [
                {
                    "name": "Step 1",
                    "domain": "security",
                    "action": "scan",
                    "order": 0,
                },
            ],
        }
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["id"] is not None

    def test_list_workflows(self, client: TestClient) -> None:
        """Test listing workflows."""
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_workflow(self, client: TestClient) -> None:
        """Test getting a specific workflow."""
        # Create a workflow first
        workflow_data = {
            "name": "Get Test Workflow",
            "steps": [],
        }
        create_response = client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code == 200
        assert response.json()["id"] == workflow_id

    def test_get_nonexistent_workflow(self, client: TestClient) -> None:
        """Test getting a workflow that doesn't exist."""
        response = client.get("/api/v1/workflows/nonexistent-id")
        assert response.status_code == 404

    def test_delete_workflow(self, client: TestClient) -> None:
        """Test deleting a workflow."""
        workflow_data = {"name": "Delete Test", "steps": []}
        create_response = client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code == 204

    def test_execute_workflow(self, client: TestClient) -> None:
        """Test executing a workflow."""
        workflow_data = {
            "name": "Execute Test",
            "steps": [
                {
                    "name": "Step 1",
                    "domain": "security",
                    "action": "scan",
                    "order": 0,
                },
            ],
        }
        create_response = client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        response = client.post(f"/api/v1/workflows/{workflow_id}/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["success"] is True

    def test_add_step_to_workflow(self, client: TestClient) -> None:
        """Test adding a step to a workflow."""
        workflow_data = {"name": "Add Step Test", "steps": []}
        create_response = client.post("/api/v1/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        step_data = {
            "name": "New Step",
            "domain": "compliance",
            "action": "audit",
            "order": 0,
        }
        response = client.post(
            f"/api/v1/workflows/{workflow_id}/steps",
            json=step_data,
        )
        assert response.status_code == 200
        assert len(response.json()["steps"]) == 1


class TestDomainRouter:
    """Tests for domain endpoints."""

    def test_route_domain_request(self, client: TestClient) -> None:
        """Test routing a domain request."""
        request_data = {
            "domain": "security",
            "action": "threat_detection",
            "payload": {"target": "network"},
        }
        response = client.post("/api/v1/domains/route", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["domain"] == "security"

    def test_route_invalid_domain(self, client: TestClient) -> None:
        """Test routing to an invalid domain."""
        request_data = {
            "domain": "nonexistent",
            "action": "test",
        }
        response = client.post("/api/v1/domains/route", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_list_domains(self, client: TestClient) -> None:
        """Test listing domains."""
        response = client.get("/api/v1/domains")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_get_domain(self, client: TestClient) -> None:
        """Test getting a specific domain."""
        response = client.get("/api/v1/domains/security")
        assert response.status_code == 200
        assert response.json()["name"] == "security"

    def test_get_nonexistent_domain(self, client: TestClient) -> None:
        """Test getting a domain that doesn't exist."""
        response = client.get("/api/v1/domains/nonexistent")
        assert response.status_code == 404

    def test_register_domain(self, client: TestClient) -> None:
        """Test registering a new domain."""
        domain_data = {
            "name": "test_domain",
            "type": "custom",
            "description": "Test domain",
            "capabilities": ["test"],
        }
        response = client.post("/api/v1/domains", json=domain_data)
        assert response.status_code == 201
        assert response.json()["name"] == "test_domain"

    def test_unregister_domain(self, client: TestClient) -> None:
        """Test unregistering a domain."""
        # First register a domain
        domain_data = {
            "name": "temp_domain",
            "type": "custom",
            "description": "Temporary",
        }
        client.post("/api/v1/domains", json=domain_data)

        response = client.delete("/api/v1/domains/temp_domain")
        assert response.status_code == 204


class TestAgentsRouter:
    """Tests for agent endpoints."""

    def test_list_agents(self, client: TestClient) -> None:
        """Test listing agents."""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_get_agent_status(self, client: TestClient) -> None:
        """Test getting agent status."""
        response = client.get("/api/v1/agents/domain_router/status")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "domain_router"
        assert data["status"] == "active"

    def test_get_nonexistent_agent_status(self, client: TestClient) -> None:
        """Test getting status for a non-existent agent."""
        response = client.get("/api/v1/agents/nonexistent/status")
        assert response.status_code == 404

    def test_reset_agent(self, client: TestClient) -> None:
        """Test resetting an agent."""
        response = client.post("/api/v1/agents/analytics_collector/reset")
        assert response.status_code == 200
        assert response.json()["reset"] is True


class TestAnalyticsRouter:
    """Tests for analytics endpoints."""

    def test_collect_event(self, client: TestClient) -> None:
        """Test collecting an analytics event."""
        event_data = {
            "event_type": "test_event",
            "domain": "security",
            "agent": "test_agent",
            "data": {"key": "value"},
        }
        response = client.post("/api/v1/analytics/collect", json=event_data)
        assert response.status_code == 200
        assert response.json()["event_type"] == "test_event"

    def test_get_analytics_summary(self, client: TestClient) -> None:
        """Test getting analytics summary."""
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "domain_metrics" in data

    def test_get_cross_domain_analytics(self, client: TestClient) -> None:
        """Test getting cross-domain analytics."""
        response = client.get("/api/v1/analytics/cross-domain")
        assert response.status_code == 200
        assert "total_events" in response.json()

    def test_record_event(self, client: TestClient) -> None:
        """Test recording an event via query params."""
        response = client.post(
            "/api/v1/analytics/record",
            params={
                "event_type": "test",
                "domain": "security",
                "agent": "test_agent",
            },
        )
        assert response.status_code == 200
        assert response.json()["event_type"] == "test"

    def test_get_domain_analytics(self, client: TestClient) -> None:
        """Test getting domain-specific analytics."""
        response = client.get("/api/v1/analytics/domains/security")
        assert response.status_code == 200
        assert response.json()["domain"] == "security"

    def test_get_agent_analytics(self, client: TestClient) -> None:
        """Test getting agent-specific analytics."""
        response = client.get("/api/v1/agents/domain_router/status")
        assert response.status_code == 200

    def test_clear_analytics(self, client: TestClient) -> None:
        """Test clearing analytics data."""
        response = client.delete("/api/v1/analytics/events")
        assert response.status_code == 204
