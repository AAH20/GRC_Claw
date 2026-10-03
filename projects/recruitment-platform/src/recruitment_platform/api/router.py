"""API router aggregating all endpoint modules."""

from __future__ import annotations

from fastapi import APIRouter

from recruitment_platform.api.routes import (
    bias_detector,
    candidate_matcher,
    employer_branding,
    health,
    interview_scheduler,
    job_description_optimizer,
    onboarding_automator,
    recruitment_analytics,
    resume_parser,
    skills_assessor,
    talent_pool_manager,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(resume_parser.router, prefix="/resume-parser", tags=["resume-parser"])
api_router.include_router(candidate_matcher.router, prefix="/candidate-matcher", tags=["candidate-matcher"])
api_router.include_router(interview_scheduler.router, prefix="/interview-scheduler", tags=["interview-scheduler"])
api_router.include_router(skills_assessor.router, prefix="/skills-assessor", tags=["skills-assessor"])
api_router.include_router(bias_detector.router, prefix="/bias-detector", tags=["bias-detector"])
api_router.include_router(talent_pool_manager.router, prefix="/talent-pool", tags=["talent-pool"])
api_router.include_router(recruitment_analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(onboarding_automator.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(job_description_optimizer.router, prefix="/job-description", tags=["job-description"])
api_router.include_router(employer_branding.router, prefix="/employer-branding", tags=["employer-branding"])
