"""Health check endpoints."""

from __future__ import annotations

from escalation_workflow.config import Settings, get_settings
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response schema."""

    ready: bool
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> HealthResponse:
    """Basic health check endpoint.

    Args:
        settings: Application settings.

    Returns:
        HealthResponse: Current health status.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ReadinessResponse:
    """Readiness probe for Kubernetes.

    Args:
        settings: Application settings.

    Returns:
        ReadinessResponse: Readiness status with component checks.
    """
    checks = {
        "config_loaded": True,
        "agents_initialized": True,
    }
    return ReadinessResponse(
        ready=all(checks.values()),
        checks=checks,
    )
