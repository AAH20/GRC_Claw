"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter
from member_verification.config.settings import Settings, get_settings
from member_verification.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = None,
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the service.
    """
    settings = settings or get_settings()
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
    settings: Settings = None,
) -> HealthResponse:
    """Readiness probe endpoint for Kubernetes.

    Returns:
        Readiness status of the service.
    """
    settings = settings or get_settings()
    return HealthResponse(
        status="ready",
        version=settings.app_version,
        checks={
            "api": True,
            "agents": True,
        },
    )
