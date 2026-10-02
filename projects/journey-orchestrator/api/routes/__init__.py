"""API route handlers for the Journey Orchestrator."""

from fastapi import APIRouter

from api.routes import journeys, personalization, timing, experiments

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(journeys.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(personalization.router, tags=["personalization"])
api_router.include_router(timing.router, tags=["timing"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
