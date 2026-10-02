"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from employer_branding.config import get_settings
from employer_branding.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint.

    Returns:
        HealthResponse with service status.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness probe for Kubernetes.

    Returns:
        Dictionary with readiness status.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe for Kubernetes.

    Returns:
        Dictionary with liveness status.
    """
    return {"status": "alive"}
