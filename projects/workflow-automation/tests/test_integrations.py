"""Tests for integration clients (n8n, Zapier, Make)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from workflow_automation.integrations.make import MakeBlueprint, MakeClient
from workflow_automation.integrations.n8n import N8nClient, N8nCredentials
from workflow_automation.integrations.zapier import ZapierClient


class TestN8nClient:
    """Tests for the n8n integration client."""

    @pytest.fixture
    def n8n_credentials(self) -> N8nCredentials:
        """Create test n8n credentials."""
        return N8nCredentials(
            api_key="test-api-key",
            base_url="http://localhost:5678",
        )

    @pytest.fixture
    def n8n_client(self, n8n_credentials: N8nCredentials) -> N8nClient:
        """Create a test n8n client."""
        return N8nClient(credentials=n8n_credentials)

    @respx.mock
    async def test_health_check_success(self, n8n_client: N8nClient) -> None:
        """Test successful health check."""
        respx.get("http://localhost:5678/healthz").mock(
            return_value=httpx.Response(200)
        )
        result = await n8n_client.health_check()
        assert result is True

    @respx.mock
    async def test_health_check_failure(self, n8n_client: N8nClient) -> None:
        """Test failed health check."""
        respx.get("http://localhost:5678/healthz").mock(
            return_value=httpx.Response(500)
        )
        result = await n8n_client.health_check()
        assert result is False

    @respx.mock
    async def test_list_workflows(self, n8n_client: N8nClient) -> None:
        """Test listing workflows."""
        respx.get("http://localhost:5678/api/v1/workflows").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "1",
                            "name": "Test Workflow",
                            "active": True,
                            "nodes": [],
                            "connections": {},
                        }
                    ]
                },
            )
        )
        workflows = await n8n_client.list_workflows()
        assert len(workflows) == 1
        assert workflows[0].name == "Test Workflow"
        assert workflows[0].active is True

    @respx.mock
    async def test_get_workflow(self, n8n_client: N8nClient) -> None:
        """Test getting a specific workflow."""
        respx.get("http://localhost:5678/api/v1/workflows/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "1",
                    "name": "Test Workflow",
                    "active": True,
                    "nodes": [],
                    "connections": {},
                },
            )
        )
        workflow = await n8n_client.get_workflow("1")
        assert workflow.id == "1"
        assert workflow.name == "Test Workflow"

    @respx.mock
    async def test_create_workflow(self, n8n_client: N8nClient) -> None:
        """Test creating a workflow."""
        respx.post("http://localhost:5678/api/v1/workflows").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "2",
                    "name": "New Workflow",
                    "active": False,
                    "nodes": [],
                    "connections": {},
                },
            )
        )
        workflow = await n8n_client.create_workflow("New Workflow", [], {})
        assert workflow.id == "2"
        assert workflow.name == "New Workflow"

    @respx.mock
    async def test_update_workflow(self, n8n_client: N8nClient) -> None:
        """Test updating a workflow."""
        respx.patch("http://localhost:5678/api/v1/workflows/1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "1",
                    "name": "Updated Workflow",
                    "active": True,
                    "nodes": [],
                    "connections": {},
                },
            )
        )
        workflow = await n8n_client.update_workflow("1", name="Updated Workflow")
        assert workflow.name == "Updated Workflow"

    @respx.mock
    async def test_delete_workflow(self, n8n_client: N8nClient) -> None:
        """Test deleting a workflow."""
        respx.delete("http://localhost:5678/api/v1/workflows/1").mock(
            return_value=httpx.Response(200)
        )
        result = await n8n_client.delete_workflow("1")
        assert result is True

    @respx.mock
    async def test_activate_workflow(self, n8n_client: N8nClient) -> None:
        """Test activating a workflow."""
        respx.post("http://localhost:5678/api/v1/workflows/1/activate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "1",
                    "name": "Test Workflow",
                    "active": True,
                    "nodes": [],
                    "connections": {},
                },
            )
        )
        workflow = await n8n_client.activate_workflow("1")
        assert workflow.active is True

    @respx.mock
    async def test_deactivate_workflow(self, n8n_client: N8nClient) -> None:
        """Test deactivating a workflow."""
        respx.post("http://localhost:5678/api/v1/workflows/1/deactivate").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "1",
                    "name": "Test Workflow",
                    "active": False,
                    "nodes": [],
                    "connections": {},
                },
            )
        )
        workflow = await n8n_client.deactivate_workflow("1")
        assert workflow.active is False

    @respx.mock
    async def test_list_executions(self, n8n_client: N8nClient) -> None:
        """Test listing executions."""
        respx.get("http://localhost:5678/api/v1/executions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "exec-1",
                            "finished": True,
                            "mode": "manual",
                            "workflow_id": "1",
                            "status": "success",
                        }
                    ]
                },
            )
        )
        executions = await n8n_client.list_executions()
        assert len(executions) == 1
        assert executions[0].id == "exec-1"

    @respx.mock
    async def test_execute_workflow(self, n8n_client: N8nClient) -> None:
        """Test triggering a workflow execution."""
        respx.post("http://localhost:5678/api/v1/workflows/1/run").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "exec-2",
                    "finished": False,
                    "mode": "manual",
                    "workflow_id": "1",
                    "status": "running",
                },
            )
        )
        execution = await n8n_client.execute_workflow("1", {"key": "value"})
        assert execution.id == "exec-2"
        assert execution.status == "running"


class TestZapierClient:
    """Tests for the Zapier integration client."""

    @pytest.fixture
    def zapier_client(self) -> ZapierClient:
        """Create a test Zapier client."""
        return ZapierClient(
            webhook_url="https://hooks.zapier.com/hooks/catch/123/abc",
            api_key="test-api-key",
        )

    @respx.mock
    async def test_health_check_success(self, zapier_client: ZapierClient) -> None:
        """Test successful health check."""
        respx.get("https://hooks.zapier.com/hooks/catch/123/abc").mock(
            return_value=httpx.Response(200)
        )
        result = await zapier_client.health_check()
        assert result is True

    async def test_health_check_not_configured(self) -> None:
        """Test health check when webhook URL is not set."""
        client = ZapierClient(webhook_url="")
        result = await client.health_check()
        assert result is False

    @respx.mock
    async def test_trigger_webhook(self, zapier_client: ZapierClient) -> None:
        """Test triggering a webhook."""
        respx.post("https://hooks.zapier.com/hooks/catch/123/abc").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        result = await zapier_client.trigger_webhook("test_event", {"key": "value"})
        assert result["success"] is True
        assert result["event"] == "test_event"

    async def test_trigger_webhook_not_configured(self) -> None:
        """Test triggering webhook when URL is not set."""
        client = ZapierClient(webhook_url="")
        with pytest.raises(ValueError, match="webhook URL not configured"):
            await client.trigger_webhook("test_event")

    @respx.mock
    async def test_trigger_catch_hook(self, zapier_client: ZapierClient) -> None:
        """Test triggering a catch hook."""
        respx.post("https://hooks.zapier.com/hooks/catch/123/abc").mock(
            return_value=httpx.Response(200, json={"status": "success"})
        )
        result = await zapier_client.trigger_catch_hook({"key": "value"})
        assert result["success"] is True

    @respx.mock
    async def test_list_zaps(self, zapier_client: ZapierClient) -> None:
        """Test listing Zaps."""
        respx.get("https://api.zapier.com/api/v1/zaps").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "zap-1",
                            "title": "Test Zap",
                            "status": "on",
                        }
                    ]
                },
            )
        )
        zaps = await zapier_client.list_zaps()
        assert len(zaps) == 1
        assert zaps[0].title == "Test Zap"

    async def test_list_zaps_not_configured(self) -> None:
        """Test listing Zaps when API key is not set."""
        client = ZapierClient(api_key="")
        with pytest.raises(ValueError, match="API key not configured"):
            await client.list_zaps()

    @respx.mock
    async def test_toggle_zap(self, zapier_client: ZapierClient) -> None:
        """Test toggling a Zap."""
        respx.patch("https://api.zapier.com/api/v1/zaps/zap-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "zap-1",
                    "title": "Test Zap",
                    "status": "off",
                },
            )
        )
        zap = await zapier_client.toggle_zap("zap-1", turn_on=False)
        assert zap.status == "off"


class TestMakeClient:
    """Tests for the Make integration client."""

    @pytest.fixture
    def make_client(self) -> MakeClient:
        """Create a test Make client."""
        return MakeClient(
            api_key="test-api-key",
            base_url="https://www.make.com",
            team_id="team-123",
        )

    @respx.mock
    async def test_health_check_success(self, make_client: MakeClient) -> None:
        """Test successful health check."""
        respx.get("https://www.make.com/api/v2/teams").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await make_client.health_check()
        assert result is True

    @respx.mock
    async def test_health_check_failure(self, make_client: MakeClient) -> None:
        """Test failed health check."""
        respx.get("https://www.make.com/api/v2/teams").mock(
            return_value=httpx.Response(401)
        )
        result = await make_client.health_check()
        assert result is False

    @respx.mock
    async def test_list_scenarios(self, make_client: MakeClient) -> None:
        """Test listing scenarios."""
        respx.get("https://www.make.com/api/v2/scenarios").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "sc-1",
                        "name": "Test Scenario",
                        "team_id": "team-123",
                        "is_active": True,
                    }
                ],
            )
        )
        scenarios = await make_client.list_scenarios()
        assert len(scenarios) == 1
        assert scenarios[0].name == "Test Scenario"

    @respx.mock
    async def test_get_scenario(self, make_client: MakeClient) -> None:
        """Test getting a specific scenario."""
        respx.get("https://www.make.com/api/v2/scenarios/sc-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sc-1",
                    "name": "Test Scenario",
                    "team_id": "team-123",
                    "is_active": True,
                },
            )
        )
        scenario = await make_client.get_scenario("sc-1")
        assert scenario.id == "sc-1"

    @respx.mock
    async def test_create_scenario(self, make_client: MakeClient) -> None:
        """Test creating a scenario."""
        respx.post("https://www.make.com/api/v2/scenarios").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sc-2",
                    "name": "New Scenario",
                    "team_id": "team-123",
                    "is_active": False,
                },
            )
        )
        blueprint = MakeBlueprint(name="New Scenario", flow=[])
        scenario = await make_client.create_scenario("New Scenario", blueprint)
        assert scenario.id == "sc-2"

    @respx.mock
    async def test_delete_scenario(self, make_client: MakeClient) -> None:
        """Test deleting a scenario."""
        respx.delete("https://www.make.com/api/v2/scenarios/sc-1").mock(
            return_value=httpx.Response(200)
        )
        result = await make_client.delete_scenario("sc-1")
        assert result is True

    @respx.mock
    async def test_activate_scenario(self, make_client: MakeClient) -> None:
        """Test activating a scenario."""
        respx.post("https://www.make.com/api/v2/scenarios/sc-1/start").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sc-1",
                    "name": "Test Scenario",
                    "team_id": "team-123",
                    "is_active": True,
                },
            )
        )
        scenario = await make_client.activate_scenario("sc-1")
        assert scenario.is_active is True

    @respx.mock
    async def test_deactivate_scenario(self, make_client: MakeClient) -> None:
        """Test deactivating a scenario."""
        respx.post("https://www.make.com/api/v2/scenarios/sc-1/stop").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sc-1",
                    "name": "Test Scenario",
                    "team_id": "team-123",
                    "is_active": False,
                },
            )
        )
        scenario = await make_client.deactivate_scenario("sc-1")
        assert scenario.is_active is False

    @respx.mock
    async def test_run_scenario(self, make_client: MakeClient) -> None:
        """Test triggering a scenario execution."""
        respx.post("https://www.make.com/api/v2/scenarios/sc-1/run").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "exec-1",
                    "scenario_id": "sc-1",
                    "status": "running",
                },
            )
        )
        execution = await make_client.run_scenario("sc-1", {"key": "value"})
        assert execution.id == "exec-1"
        assert execution.status == "running"

    @respx.mock
    async def test_get_blueprint(self, make_client: MakeClient) -> None:
        """Test getting a scenario blueprint."""
        respx.get("https://www.make.com/api/v2/scenarios/sc-1/blueprint").mock(
            return_value=httpx.Response(
                200,
                json={
                    "name": "Test Scenario",
                    "flow": [{"id": 1, "module": "gateway:CustomWebHook"}],
                },
            )
        )
        blueprint = await make_client.get_blueprint("sc-1")
        assert blueprint.name == "Test Scenario"
        assert len(blueprint.flow) == 1
