"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status of the application.
    """
    return {"status": "healthy", "service": "recruitment-platform"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness check endpoint.

    Returns:
        Readiness status of the application.
    """
    return {"status": "ready"}
