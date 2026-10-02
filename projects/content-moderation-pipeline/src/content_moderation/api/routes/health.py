"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status response.
    """
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/metrics")
async def metrics() -> dict[str, str]:
    """Prometheus metrics endpoint.

    Returns:
        Metrics in Prometheus format.
    """
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return {
        "content": generate_latest().decode("utf-8"),
        "content_type": CONTENT_TYPE_LATEST,
    }
