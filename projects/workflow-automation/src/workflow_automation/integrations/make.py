"""Make (Integromat) integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from workflow_automation.config import get_settings

logger = structlog.get_logger(__name__)


class MakeScenario(BaseModel):
    """Represents a Make scenario."""

    id: str
    name: str
    team_id: str = ""
    is_active: bool = False
    created_at: str = ""
    updated_at: str = ""


class MakeExecution(BaseModel):
    """Represents a Make execution."""

    id: str
    scenario_id: str = ""
    status: str = "running"
    started_at: str = ""
    finished_at: str | None = None


class MakeBlueprint(BaseModel):
    """Represents a Make scenario blueprint."""

    name: str
    flow: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MakeClient:
    """Client for interacting with the Make API.

    Provides methods to manage scenarios, executions, and blueprints
    on the Make platform.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        team_id: str | None = None,
    ) -> None:
        """Initialize the Make client.

        Args:
            api_key: Make API key. If None, loads from settings.
            base_url: Make API base URL. If None, loads from settings.
            team_id: Make team ID. If None, loads from settings.
        """
        settings = get_settings()
        self._api_key = api_key or settings.make_api_key
        self._base_url = base_url or settings.make_base_url
        self._team_id = team_id or settings.make_team_id
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the Make API is accessible.

        Returns:
            True if the API is reachable and credentials are valid.
        """
        try:
            response = await self._client.get("/api/v2/teams")
            return response.status_code == 200
        except Exception as e:
            logger.error("Make health check failed", error=str(e))
            return False

    async def list_scenarios(self) -> list[MakeScenario]:
        """List all scenarios for the configured team.

        Returns:
            List of scenarios.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(
            "/api/v2/scenarios",
            params={"teamId": self._team_id},
        )
        response.raise_for_status()
        data = response.json()
        return [MakeScenario(**scenario) for scenario in data]

    async def get_scenario(self, scenario_id: str) -> MakeScenario:
        """Get a specific scenario by ID.

        Args:
            scenario_id: The scenario identifier.

        Returns:
            The scenario details.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(f"/api/v2/scenarios/{scenario_id}")
        response.raise_for_status()
        return MakeScenario(**response.json())

    async def create_scenario(
        self, name: str, blueprint: MakeBlueprint
    ) -> MakeScenario:
        """Create a new scenario.

        Args:
            name: Scenario name.
            blueprint: Scenario blueprint.

        Returns:
            The created scenario.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload = {
            "name": name,
            "teamId": self._team_id,
            "blueprint": blueprint.model_dump(),
        }
        response = await self._client.post("/api/v2/scenarios", json=payload)
        response.raise_for_status()
        return MakeScenario(**response.json())

    async def update_scenario(
        self, scenario_id: str, name: str | None = None, blueprint: MakeBlueprint | None = None
    ) -> MakeScenario:
        """Update an existing scenario.

        Args:
            scenario_id: The scenario identifier.
            name: New scenario name.
            blueprint: Updated blueprint.

        Returns:
            The updated scenario.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if blueprint is not None:
            payload["blueprint"] = blueprint.model_dump()

        response = await self._client.patch(
            f"/api/v2/scenarios/{scenario_id}", json=payload
        )
        response.raise_for_status()
        return MakeScenario(**response.json())

    async def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario.

        Args:
            scenario_id: The scenario identifier.

        Returns:
            True if deleted successfully.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.delete(f"/api/v2/scenarios/{scenario_id}")
        response.raise_for_status()
        return True

    async def activate_scenario(self, scenario_id: str) -> MakeScenario:
        """Activate a scenario.

        Args:
            scenario_id: The scenario identifier.

        Returns:
            The updated scenario.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v2/scenarios/{scenario_id}/start"
        )
        response.raise_for_status()
        return MakeScenario(**response.json())

    async def deactivate_scenario(self, scenario_id: str) -> MakeScenario:
        """Deactivate a scenario.

        Args:
            scenario_id: The scenario identifier.

        Returns:
            The updated scenario.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v2/scenarios/{scenario_id}/stop"
        )
        response.raise_for_status()
        return MakeScenario(**response.json())

    async def list_executions(
        self, scenario_id: str | None = None, limit: int = 100
    ) -> list[MakeExecution]:
        """List scenario executions.

        Args:
            scenario_id: Filter by scenario ID.
            limit: Maximum number of executions to return.

        Returns:
            List of executions.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        params: dict[str, Any] = {"limit": limit}
        if scenario_id:
            params["scenarioId"] = scenario_id

        response = await self._client.get("/api/v2/executions", params=params)
        response.raise_for_status()
        data = response.json()
        return [MakeExecution(**execution) for execution in data]

    async def get_execution(self, execution_id: str) -> MakeExecution:
        """Get a specific execution by ID.

        Args:
            execution_id: The execution identifier.

        Returns:
            The execution details.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(f"/api/v2/executions/{execution_id}")
        response.raise_for_status()
        return MakeExecution(**response.json())

    async def run_scenario(
        self, scenario_id: str, data: dict[str, Any] | None = None
    ) -> MakeExecution:
        """Trigger a scenario execution.

        Args:
            scenario_id: The scenario identifier.
            data: Optional data to pass to the scenario.

        Returns:
            The execution record.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.post(
            f"/api/v2/scenarios/{scenario_id}/run",
            json=data or {},
        )
        response.raise_for_status()
        return MakeExecution(**response.json())

    async def get_blueprint(self, scenario_id: str) -> MakeBlueprint:
        """Get the blueprint of a scenario.

        Args:
            scenario_id: The scenario identifier.

        Returns:
            The scenario blueprint.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        response = await self._client.get(
            f"/api/v2/scenarios/{scenario_id}/blueprint"
        )
        response.raise_for_status()
        return MakeBlueprint(**response.json())
