"""n8n integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from workflow_automation.config import get_settings

logger = structlog.get_logger(__name__)


class N8nWorkflow(BaseModel):
    """Represents an n8n workflow."""

    id: str
    name: str
    active: bool = False
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    connections: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class N8nExecution(BaseModel):
    """Represents an n8n execution."""

    id: str
    finished: bool = False
    mode: str = "manual"
    started_at: str = ""
    stopped_at: str | None = None
    workflow_id: str = ""
    status: str = "running"


class N8nCredentials(BaseModel):
    """n8n API credentials."""

    api_key: str
    base_url: str = "http://localhost:5678"


class N8nClient:
    """Client for interacting with the n8n API.

    Provides methods to manage workflows, executions, and credentials
    on an n8n instance.
    """

    def __init__(self, credentials: N8nCredentials | None = None) -> None:
        """Initialize the n8n client.

        Args:
            credentials: n8n API credentials. If None, loads from settings.
        """
        if credentials is None:
            settings = get_settings()
            credentials = N8nCredentials(
                api_key=settings.n8n_api_key,
                base_url=settings.n8n_base_url,
            )

        self._credentials = credentials
        self._client = httpx.AsyncClient(
            base_url=credentials.base_url,
            headers={"X-N8N-API-KEY": credentials.api_key},
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the n8n instance is healthy.

        Returns:
            True if the instance is reachable and healthy.
        """
        try:
            response = await self._client.get("/healthz")
            return response.status_code == 200
        except Exception as e:
            logger.error("n8n health check failed", error=str(e))
            return False

    async def list_workflows(self) -> list[N8nWorkflow]:
        """List all workflows from the n8n instance.

        Returns:
            List of workflows.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get("/api/v1/workflows")
        response.raise_for_status()
        data = response.json().get("data", [])
        return [N8nWorkflow(**wf) for wf in data]

    async def get_workflow(self, workflow_id: str) -> N8nWorkflow:
        """Get a specific workflow by ID.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The workflow details.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(f"/api/v1/workflows/{workflow_id}")
        response.raise_for_status()
        return N8nWorkflow(**response.json())

    async def create_workflow(
        self, name: str, nodes: list[dict[str, Any]], connections: dict[str, Any]
    ) -> N8nWorkflow:
        """Create a new workflow.

        Args:
            name: Workflow name.
            nodes: Workflow nodes.
            connections: Node connections.

        Returns:
            The created workflow.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload = {"name": name, "nodes": nodes, "connections": connections}
        response = await self._client.post("/api/v1/workflows", json=payload)
        response.raise_for_status()
        return N8nWorkflow(**response.json())

    async def update_workflow(
        self,
        workflow_id: str,
        name: str | None = None,
        nodes: list[dict[str, Any]] | None = None,
        connections: dict[str, Any] | None = None,
        active: bool | None = None,
    ) -> N8nWorkflow:
        """Update an existing workflow.

        Args:
            workflow_id: The workflow identifier.
            name: New workflow name.
            nodes: Updated nodes.
            connections: Updated connections.
            active: Active status.

        Returns:
            The updated workflow.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if nodes is not None:
            payload["nodes"] = nodes
        if connections is not None:
            payload["connections"] = connections
        if active is not None:
            payload["active"] = active

        response = await self._client.patch(
            f"/api/v1/workflows/{workflow_id}", json=payload
        )
        response.raise_for_status()
        return N8nWorkflow(**response.json())

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            True if deleted successfully.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.delete(f"/api/v1/workflows/{workflow_id}")
        response.raise_for_status()
        return True

    async def activate_workflow(self, workflow_id: str) -> N8nWorkflow:
        """Activate a workflow.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The updated workflow.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/activate"
        )
        response.raise_for_status()
        return N8nWorkflow(**response.json())

    async def deactivate_workflow(self, workflow_id: str) -> N8nWorkflow:
        """Deactivate a workflow.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The updated workflow.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/deactivate"
        )
        response.raise_for_status()
        return N8nWorkflow(**response.json())

    async def list_executions(
        self, workflow_id: str | None = None, limit: int = 100
    ) -> list[N8nExecution]:
        """List workflow executions.

        Args:
            workflow_id: Filter by workflow ID.
            limit: Maximum number of executions to return.

        Returns:
            List of executions.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        params: dict[str, Any] = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id

        response = await self._client.get("/api/v1/executions", params=params)
        response.raise_for_status()
        data = response.json().get("data", [])
        return [N8nExecution(**ex) for ex in data]

    async def get_execution(self, execution_id: str) -> N8nExecution:
        """Get a specific execution by ID.

        Args:
            execution_id: The execution identifier.

        Returns:
            The execution details.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(f"/api/v1/executions/{execution_id}")
        response.raise_for_status()
        return N8nExecution(**response.json())

    async def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution.

        Args:
            execution_id: The execution identifier.

        Returns:
            True if deleted successfully.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.delete(f"/api/v1/executions/{execution_id}")
        response.raise_for_status()
        return True

    async def execute_workflow(
        self, workflow_id: str, data: dict[str, Any] | None = None
    ) -> N8nExecution:
        """Trigger a workflow execution.

        Args:
            workflow_id: The workflow identifier.
            data: Optional data to pass to the workflow.

        Returns:
            The execution record.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/run",
            json={"workflowData": data or {}},
        )
        response.raise_for_status()
        return N8nExecution(**response.json())
