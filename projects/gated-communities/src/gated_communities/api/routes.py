"""Main API router combining all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter
from tier_management.api.routes import (access_router, analytics_router,
                                        benefits_router, evaluation_router,
                                        health_router, tiers_router,
                                        upgrades_router)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["health"])
api_router.include_router(tiers_router, prefix="/tiers", tags=["tiers"])
api_router.include_router(
    evaluation_router, prefix="/evaluations", tags=["evaluations"]
)
api_router.include_router(upgrades_router, prefix="/upgrades", tags=["upgrades"])
api_router.include_router(access_router, prefix="/access", tags=["access"])
api_router.include_router(benefits_router, prefix="/benefits", tags=["benefits"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

router = APIRouter()
router.include_router(api_router)
