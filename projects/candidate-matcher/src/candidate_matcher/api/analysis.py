"""Analysis endpoints for skills gap, bias, and culture fit."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent
from candidate_matcher.api.dependencies import (
    get_bias_aware_ranker,
    get_culture_fit_assessor,
    get_skills_gap_analyzer,
)
from candidate_matcher.models.schemas import (
    BiasReport,
    Candidate,
    CultureFitResult,
    JobPosting,
    SkillsGap,
)

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


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


@router.post("/skills-gap", response_model=SkillsGap)
async def analyze_skills_gap(
    request: Request,
    candidate_id: UUID,
    job_id: UUID,
    skills_gap_analyzer: SkillsGapAnalyzerAgent = Depends(get_skills_gap_analyzer),
) -> SkillsGap:
    """Analyze skills gap between a candidate and job.

    Args:
        request: FastAPI request object.
        candidate_id: Candidate identifier.
        job_id: Job identifier.
        skills_gap_analyzer: Skills gap analyzer agent.

    Returns:
        Skills gap analysis result.
    """
    candidate = _get_candidate(request, candidate_id)
    job = _get_job(request, job_id)
    return await skills_gap_analyzer.execute(candidate=candidate, job=job)


@router.post("/bias", response_model=BiasReport)
async def analyze_bias(
    request: Request,
    candidate_id: UUID,
    job_id: UUID,
    bias_aware_ranker: BiasAwareRankerAgent = Depends(get_bias_aware_ranker),
) -> BiasReport:
    """Run bias analysis for a candidate-job pair.

    Args:
        request: FastAPI request object.
        candidate_id: Candidate identifier.
        job_id: Job identifier.
        bias_aware_ranker: Bias-aware ranker agent.

    Returns:
        Bias analysis report.
    """
    candidate = _get_candidate(request, candidate_id)
    job = _get_job(request, job_id)
    result = await bias_aware_ranker.execute(
        candidate=candidate,
        job=job,
        base_scores={"semantic": 0.5, "skills": 0.5, "experience": 0.5, "culture": 0.5},
    )
    return result["bias_report"]


@router.post("/culture-fit", response_model=CultureFitResult)
async def assess_culture_fit(
    request: Request,
    candidate_id: UUID,
    job_id: UUID,
    culture_fit_assessor: CultureFitAssessorAgent = Depends(get_culture_fit_assessor),
) -> CultureFitResult:
    """Assess culture fit between a candidate and job.

    Args:
        request: FastAPI request object.
        candidate_id: Candidate identifier.
        job_id: Job identifier.
        culture_fit_assessor: Culture fit assessor agent.

    Returns:
        Culture fit assessment result.
    """
    candidate = _get_candidate(request, candidate_id)
    job = _get_job(request, job_id)
    result = await culture_fit_assessor.execute(candidate=candidate, job=job)
    return CultureFitResult(
        fit_score=result["fit_score"],
        aligned_values=result["aligned_values"],
        potential_conflicts=result["potential_conflicts"],
        work_style_compatibility=result["work_style_compatibility"],
        summary=result["summary"],
    )
