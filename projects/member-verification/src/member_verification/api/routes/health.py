"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from member_verification.config.settings import Settings, get_settings
from member_verification.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the service.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        checks={
            "api": True,
            "agents": True,
        },
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Readiness probe endpoint for Kubernetes.

    Returns:
        Readiness status of the service.
    """
    return HealthResponse(
        status="ready",
        version=settings.app_version,
        checks={
            "api": True,
            "agents": True,
        },
    )
