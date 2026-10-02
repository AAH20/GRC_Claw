"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter

from fraud_detection.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status.
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness probe endpoint.

    Returns:
        HealthResponse indicating service readiness.
    """
    return HealthResponse(status="ready")
