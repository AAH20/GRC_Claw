"""Health check endpoints."""

from fastapi import APIRouter

from licensing_engine import __version__
from licensing_engine.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Check if the service is healthy.

    Returns:
        HealthResponse with service status and version.
    """
    return HealthResponse(status="healthy", version=__version__)


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness_check() -> HealthResponse:
    """Check if the service is ready to accept traffic.

    Returns:
        HealthResponse with service status and version.
    """
    return HealthResponse(status="ready", version=__version__)


@router.get("/live", response_model=HealthResponse, summary="Liveness check")
async def liveness_check() -> HealthResponse:
    """Check if the service is alive.

    Returns:
        HealthResponse with service status and version.
    """
    return HealthResponse(status="alive", version=__version__)
