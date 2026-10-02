"""API router aggregating all endpoint modules."""

from fastapi import APIRouter

from licensing_engine.api.routes import (
    compliance,
    contracts,
    health,
    licenses,
    negotiations,
    royalties,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["Licenses"])
api_router.include_router(
    negotiations.router, prefix="/negotiations", tags=["Negotiations"]
)
api_router.include_router(
    compliance.router, prefix="/compliance", tags=["Compliance"]
)
api_router.include_router(royalties.router, prefix="/royalties", tags=["Royalties"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
