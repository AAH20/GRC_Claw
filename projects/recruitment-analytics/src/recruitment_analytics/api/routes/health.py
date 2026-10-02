"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status and version.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        checks={
            "api": "up",
            "version": settings.app_version,
        },
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> HealthResponse:
    """Readiness probe for Kubernetes.

    Returns:
        HealthResponse indicating service is ready to accept traffic.
    """
    return HealthResponse(
        status="ready",
        version=settings.app_version,
        checks={
            "api": "ready",
        },
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check(
    settings: Settings = Depends(get_settings)  # noqa: B008
) -> HealthResponse:
    """Liveness probe for Kubernetes.

    Returns:
        HealthResponse indicating service is alive.
    """
    return HealthResponse(
        status="alive",
        version=settings.app_version,
        checks={
            "api": "alive",
        },
    )
