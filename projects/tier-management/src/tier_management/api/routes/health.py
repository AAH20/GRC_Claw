"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import HealthResponse

health_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status and version.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        checks={
            "api": True,
            "agents": True,
        },
    )


@health_router.get("/ready")
async def readiness_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> JSONResponse:
    """Readiness probe for Kubernetes.

    Returns:
        JSONResponse indicating service readiness.
    """
    return JSONResponse(
        content={"ready": True, "version": settings.app_version},
        status_code=200,
    )


@health_router.get("/live")
async def liveness_check() -> JSONResponse:
    """Liveness probe for Kubernetes.

    Returns:
        JSONResponse indicating service is alive.
    """
    return JSONResponse(content={"alive": True}, status_code=200)
