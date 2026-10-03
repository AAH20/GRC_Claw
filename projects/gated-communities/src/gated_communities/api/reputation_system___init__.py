"""API router aggregation."""

from fastapi import APIRouter

from reputation_system.api.routes import (
    badges,
    explanations,
    health,
    history,
    reputation,
    trust_tiers,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(reputation.router)
api_router.include_router(badges.router)
api_router.include_router(trust_tiers.router)
api_router.include_router(history.router)
api_router.include_router(explanations.router)
