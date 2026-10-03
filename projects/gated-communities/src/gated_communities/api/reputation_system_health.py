"""Health check API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from reputation_system.config.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str = "0.1.0"


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Basic health check endpoint.

    Args:
        settings: Application settings.

    Returns:
        Health status response.
    """
    return HealthResponse(status="healthy")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessResponse:
    """Readiness check endpoint for Kubernetes.

    Args:
        settings: Application settings.

    Returns:
        Readiness status with component checks.
    """
    checks = {
        "api": True,
        "agents": True,
    }
    return ReadinessResponse(ready=all(checks.values()), checks=checks)
