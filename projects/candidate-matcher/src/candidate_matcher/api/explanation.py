"""Explanation endpoints for match results."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from candidate_matcher.agents.match_explainer import MatchExplainerAgent
from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent
from candidate_matcher.api.dependencies import (
    get_match_explainer,
    get_skills_gap_analyzer,
)
from candidate_matcher.models.schemas import (
    Candidate,
    JobPosting,
    MatchExplanation,
    MatchResult,
)

router = APIRouter(prefix="/api/v1", tags=["explanation"])


def _get_candidate(request: Request, candidate_id: UUID) -> Candidate:
    """Retrieve a candidate from app state store."""
    store: dict[UUID, Candidate] = request.app.state.candidate_store
    candidate = store.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    return candidate


def _get_job(request: Request, job_id: UUID) -> JobPosting:
    """Retrieve a job from app state store."""
    store: dict[UUID, JobPosting] = request.app.state.job_store
    job = store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job


def _get_match_result(request: Request, match_id: UUID) -> MatchResult:
    """Retrieve a match result from app state store."""
    store: dict[UUID, MatchResult] = request.app.state.match_store
    result = store.get(match_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result {match_id} not found",
        )
    return result


@router.post("/explain", response_model=MatchExplanation)
async def explain_match(
    request: Request,
    match_id: UUID,
    match_explainer: MatchExplainerAgent = Depends(get_match_explainer),  # noqa: B008
    skills_gap_analyzer: SkillsGapAnalyzerAgent = Depends(get_skills_gap_analyzer),  # noqa: B008
) -> MatchExplanation:
    """Generate an explanation for a match result.

    Args:
        request: FastAPI request object.
        match_id: Match result identifier.
        match_explainer: Match explainer agent.
        skills_gap_analyzer: Skills gap analyzer agent.

    Returns:
        Match explanation.
    """
    match_result = _get_match_result(request, match_id)
    candidate = _get_candidate(request, match_result.candidate_id)
    job = _get_job(request, match_result.job_id)

    # Re-compute skills gap for context
    skills_gap = await skills_gap_analyzer.execute(candidate=candidate, job=job)

    return await match_explainer.execute(
        candidate=candidate,
        job=job,
        match_result=match_result,
        skills_gap=skills_gap,
    )
