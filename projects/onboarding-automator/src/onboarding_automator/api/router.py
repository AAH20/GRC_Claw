"""API router aggregating all endpoint modules."""

from fastapi import APIRouter

from onboarding_automator.api.routes import (
    compliance,
    documents,
    health,
    plans,
    progress,
    tasks,
    welcome,
)

__all__ = ["api_router"]

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(plans.router, prefix="/plans", tags=["Onboarding Plans"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(welcome.router, prefix="/welcome", tags=["Welcome"])
