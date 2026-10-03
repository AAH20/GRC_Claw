"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ugc_marketplace import __version__
from ugc_marketplace.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status response.
    """
    return HealthResponse(status="healthy", version=__version__)


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check endpoint.

    Returns:
        Readiness status response.
    """
    return HealthResponse(status="ready", version=__version__)


@router.get("/live", response_model=HealthResponse)
async def liveness_check() -> HealthResponse:
    """Liveness check endpoint.

    Returns:
        Liveness status response.
    """
    return HealthResponse(status="alive", version=__version__)
