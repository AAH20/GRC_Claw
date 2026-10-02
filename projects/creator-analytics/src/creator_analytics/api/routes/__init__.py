"""API routes for creator analytics."""

from fastapi import APIRouter

from creator_analytics.api.routes import audience, content, engagement, growth, health, revenue

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(audience.router, prefix="/audience", tags=["audience"])
router.include_router(content.router, prefix="/content", tags=["content"])
router.include_router(revenue.router, prefix="/revenue", tags=["revenue"])
router.include_router(growth.router, prefix="/growth", tags=["growth"])
router.include_router(engagement.router, prefix="/engagement", tags=["engagement"])
