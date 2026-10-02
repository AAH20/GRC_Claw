"""API route handlers for escalation workflow."""

from escalation_workflow.api.escalations import router as escalations_router
from escalation_workflow.api.health import router as health_router
from escalation_workflow.api.priorities import router as priorities_router
from escalation_workflow.api.resolutions import router as resolutions_router
from escalation_workflow.api.sla import router as sla_router

__all__ = [
    "escalations_router",
    "health_router",
    "priorities_router",
    "resolutions_router",
    "sla_router",
]
