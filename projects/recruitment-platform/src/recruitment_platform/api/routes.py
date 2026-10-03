"""API route registration for the recruitment platform."""

from fastapi import APIRouter

from recruitment_platform.api.routers import (
    analytics,
    applications,
    assessments,
    candidates,
    employers,
    interviews,
    jobs,
    reports,
    skills,
    talent_pools,
)

api_router = APIRouter()

api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(talent_pools.router, prefix="/talent-pools", tags=["talent_pools"])
api_router.include_router(employers.router, prefix="/employers", tags=["employers"])
