"""API router aggregating all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from recruitment_analytics.api.routes import (
    cost,
    diversity,
    funnel,
    health,
    prediction,
    source,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(funnel.router, prefix="/funnel", tags=["funnel"])
api_router.include_router(source.router, prefix="/source", tags=["source"])
api_router.include_router(prediction.router, prefix="/prediction", tags=["prediction"])
api_router.include_router(diversity.router, prefix="/diversity", tags=["diversity"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
