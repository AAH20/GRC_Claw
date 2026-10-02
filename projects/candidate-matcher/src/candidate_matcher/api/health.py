"""Health check endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from candidate_matcher.config.settings import Settings, get_settings
from candidate_matcher.models.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint.

    Args:
        request: FastAPI request object.
        settings: Application settings.

    Returns:
        Health status response.
    """
    checks = {
        "llm_client": hasattr(request.app.state, "llm_client"),
        "embedding_client": hasattr(request.app.state, "embedding_client"),
        "vector_store": hasattr(request.app.state, "vector_store"),
    }
    return HealthResponse(
        status="healthy" if all(checks.values()) else "degraded",
        version=settings.app_version,
        checks=checks,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    request: Request,
) -> ReadinessResponse:
    """Readiness probe endpoint.

    Args:
        request: FastAPI request object.

    Returns:
        Readiness status response.
    """
    checks = {
        "llm_client": hasattr(request.app.state, "llm_client"),
        "embedding_client": hasattr(request.app.state, "embedding_client"),
        "vector_store": hasattr(request.app.state, "vector_store"),
        "agents_initialized": all(
            hasattr(request.app.state, attr)
            for attr in [
                "semantic_matcher",
                "skills_gap_analyzer",
                "bias_aware_ranker",
                "culture_fit_assessor",
                "match_explainer",
            ]
        ),
    }
    ready = all(checks.values())
    return ReadinessResponse(
        ready=ready,
        checks=checks,
    )
