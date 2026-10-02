"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from community_governance.api.dependencies import get_agents
from community_governance.config.settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    agents: dict[str, str] = Field(default_factory=dict, description="Agent health status")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    agents: dict = Depends(get_agents)  # noqa: B008,
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the service and its agents.
    """
    settings = get_settings()
    agent_status = {}
    for name, agent in agents.items():
        try:
            health = await agent.health_check()
            agent_status[name] = health.get("status", "unknown")
        except Exception:
            agent_status[name] = "unhealthy"

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        agents=agent_status,
    )
