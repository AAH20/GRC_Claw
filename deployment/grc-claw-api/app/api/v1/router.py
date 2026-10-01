"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.routes import agents, assessments, audit, compliance, composed, enforcement, evidence, graphql, health, policies, webhooks

api_router = APIRouter(prefix="/v1.0")

api_router.include_router(policies.router)
api_router.include_router(evidence.router)
api_router.include_router(enforcement.router)
api_router.include_router(assessments.router)
api_router.include_router(compliance.router)
api_router.include_router(agents.router)
api_router.include_router(audit.router)
api_router.include_router(webhooks.router)
api_router.include_router(composed.router)
api_router.include_router(health.router)
api_router.include_router(graphql.router)
