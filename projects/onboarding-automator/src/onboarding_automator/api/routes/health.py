"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from onboarding_automator.config.settings import Settings, get_settings
from onboarding_automator.models import HealthResponse

__all__ = ["router"]

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Check the health of the service.

    Returns:
        HealthResponse with current service status.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
    )


@router.get("/ready")
async def readiness_check(request: Request) -> JSONResponse:
    """Check if the service is ready to accept traffic.

    Returns:
        JSONResponse indicating readiness status.
    """
    # In production, check database connectivity, etc.
    return JSONResponse(content={"ready": True}, status_code=200)


@router.get("/live")
async def liveness_check() -> JSONResponse:
    """Check if the service is alive.

    Returns:
        JSONResponse indicating liveness status.
    """
    return JSONResponse(content={"alive": True}, status_code=200)
