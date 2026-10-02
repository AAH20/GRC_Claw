"""API routes for skills-assessor."""

from skills_assessor.api.assessments import router as assessments_router
from skills_assessor.api.health import router as health_router
from skills_assessor.api.skills import router as skills_router

__all__ = ["assessments_router", "health_router", "skills_router"]
