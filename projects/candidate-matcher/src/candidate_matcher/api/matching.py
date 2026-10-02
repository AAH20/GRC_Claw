"""Matching endpoints for candidate-job matching."""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
from candidate_matcher.agents.match_explainer import MatchExplainerAgent
from candidate_matcher.agents.semantic_matcher import SemanticMatcherAgent
from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent
from candidate_matcher.api.dependencies import (
    get_bias_aware_ranker,
    get_culture_fit_assessor,
    get_match_explainer,
    get_semantic_matcher,
    get_skills_gap_analyzer,
)
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.models.schemas import (
    BatchMatchRequest,
    BatchMatchResponse,
    Candidate,
    JobPosting,
    MatchRequest,
    MatchResult,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["matching"])


def _get_candidate(request: Request, candidate_id: UUID) -> Candidate:
    """Retrieve a candidate from app state store.

    Args:
        request: FastAPI request object.
        candidate_id: Candidate identifier.

    Returns:
        The candidate profile.

    Raises:
        HTTPException: If candidate not found.
    """
    store: dict[UUID, Candidate] = request.app.state.candidate_store
    candidate = store.get(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    return candidate


def _get_job(request: Request, job_id: UUID) -> JobPosting:
    """Retrieve a job from app state store.

    Args:
        request: FastAPI request object.
        job_id: Job identifier.

    Returns:
        The job posting.

    Raises:
        HTTPException: If job not found.
    """
    store: dict[UUID, JobPosting] = request.app.state.job_store
    job = store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job


@router.post("/match", response_model=list[MatchResult])
async def match_candidates(
    request: Request,
    match_request: MatchRequest,
    semantic_matcher: SemanticMatcherAgent = Depends(get_semantic_matcher),  # noqa: B008
    skills_gap_analyzer: SkillsGapAnalyzerAgent = Depends(get_skills_gap_analyzer),  # noqa: B008
    bias_aware_ranker: BiasAwareRankerAgent = Depends(get_bias_aware_ranker),  # noqa: B008
    culture_fit_assessor: CultureFitAssessorAgent = Depends(get_culture_fit_assessor),  # noqa: B008
    match_explainer: MatchExplainerAgent = Depends(get_match_explainer),  # noqa: B008
) -> list[MatchResult]:
    """Match candidates to a job posting.

    Args:
        request: FastAPI request object.
        match_request: Match request parameters.
        semantic_matcher: Semantic matcher agent.
        skills_gap_analyzer: Skills gap analyzer agent.
        bias_aware_ranker: Bias-aware ranker agent.
        culture_fit_assessor: Culture fit assessor agent.
        match_explainer: Match explainer agent.

    Returns:
        List of match results sorted by score.
    """
    start_time = time.time()
    job = _get_job(request, match_request.job_id)

    # Get candidates to match
    candidate_store: dict[UUID, Candidate] = request.app.state.candidate_store
    if match_request.candidate_ids:
        candidates = []
        for cid in match_request.candidate_ids:
            try:
                candidates.append(_get_candidate(request, cid))
            except HTTPException:
                continue
    else:
        candidates = list(candidate_store.values())

    results: list[MatchResult] = []

    for candidate in candidates:
        # Run all agents
        semantic_result = await semantic_matcher.execute(candidate=candidate, job=job)
        skills_gap = await skills_gap_analyzer.execute(candidate=candidate, job=job)
        culture_result = await culture_fit_assessor.execute(candidate=candidate, job=job)

        base_scores = {
            "semantic": semantic_result["combined_score"],
            "skills": 1.0 - skills_gap.gap_score,
            "experience": min(candidate.experience_years / 10.0, 1.0),
            "culture": culture_result["fit_score"],
        }

        # Apply bias-aware ranking
        rank_result = await bias_aware_ranker.execute(
            candidate=candidate,
            job=job,
            base_scores=base_scores,
        )

        # Generate explanation if requested
        explanation = None
        if match_request.include_explanation:
            match_result_temp = MatchResult(
                job_id=job.id,
                candidate_id=candidate.id,
                overall_score=rank_result["adjusted_score"],
                semantic_score=base_scores["semantic"],
                skills_score=base_scores["skills"],
                experience_score=base_scores["experience"],
                culture_score=base_scores["culture"],
                bias_adjusted=rank_result["mitigation_applied"],
                bias_penalty=rank_result["original_score"] - rank_result["adjusted_score"],
            )
            explanation_result = await match_explainer.execute(
                candidate=candidate,
                job=job,
                match_result=match_result_temp,
                skills_gap=skills_gap,
            )
            explanation = explanation_result.summary

        results.append(MatchResult(
            job_id=job.id,
            candidate_id=candidate.id,
            overall_score=rank_result["adjusted_score"],
            semantic_score=base_scores["semantic"],
            skills_score=base_scores["skills"],
            experience_score=base_scores["experience"],
            culture_score=base_scores["culture"],
            bias_adjusted=rank_result["mitigation_applied"],
            bias_penalty=rank_result["original_score"] - rank_result["adjusted_score"],
            explanation=explanation,
        ))

    # Sort by score and assign ranks
    results.sort(key=lambda r: r.overall_score, reverse=True)
    for i, result in enumerate(results):
        result.rank = i + 1

    # Apply top_k and min_similarity filters
    if match_request.min_similarity > 0:
        results = [r for r in results if r.overall_score >= match_request.min_similarity]
    results = results[: match_request.top_k]

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "match_candidates_completed",
        job_id=str(job.id),
        candidates_processed=len(candidates),
        results_returned=len(results),
        duration_ms=round(duration_ms, 2),
    )

    return results


@router.post("/match/batch", response_model=BatchMatchResponse)
async def batch_match_candidates(
    request: Request,
    batch_request: BatchMatchRequest,
    semantic_matcher: SemanticMatcherAgent = Depends(get_semantic_matcher),  # noqa: B008
    skills_gap_analyzer: SkillsGapAnalyzerAgent = Depends(get_skills_gap_analyzer),  # noqa: B008
    bias_aware_ranker: BiasAwareRankerAgent = Depends(get_bias_aware_ranker),  # noqa: B008
    culture_fit_assessor: CultureFitAssessorAgent = Depends(get_culture_fit_assessor),  # noqa: B008
) -> BatchMatchResponse:
    """Batch match multiple candidates to a job.

    Args:
        request: FastAPI request object.
        batch_request: Batch match request parameters.
        semantic_matcher: Semantic matcher agent.
        skills_gap_analyzer: Skills gap analyzer agent.
        bias_aware_ranker: Bias-aware ranker agent.
        culture_fit_assessor: Culture fit assessor agent.

    Returns:
        Batch match response with all results.
    """
    start_time = time.time()
    job = _get_job(request, batch_request.job_id)

    results: list[MatchResult] = []

    for cid in batch_request.candidate_ids:
        try:
            candidate = _get_candidate(request, cid)
        except HTTPException:
            continue

        semantic_result = await semantic_matcher.execute(candidate=candidate, job=job)
        skills_gap = await skills_gap_analyzer.execute(candidate=candidate, job=job)
        culture_result = await culture_fit_assessor.execute(candidate=candidate, job=job)

        base_scores = {
            "semantic": semantic_result["combined_score"],
            "skills": 1.0 - skills_gap.gap_score,
            "experience": min(candidate.experience_years / 10.0, 1.0),
            "culture": culture_result["fit_score"],
        }

        rank_result = await bias_aware_ranker.execute(
            candidate=candidate,
            job=job,
            base_scores=base_scores,
        )

        results.append(MatchResult(
            job_id=job.id,
            candidate_id=candidate.id,
            overall_score=rank_result["adjusted_score"],
            semantic_score=base_scores["semantic"],
            skills_score=base_scores["skills"],
            experience_score=base_scores["experience"],
            culture_score=base_scores["culture"],
            bias_adjusted=rank_result["mitigation_applied"],
            bias_penalty=rank_result["original_score"] - rank_result["adjusted_score"],
        ))

    results.sort(key=lambda r: r.overall_score, reverse=True)
    for i, result in enumerate(results):
        result.rank = i + 1

    duration_ms = (time.time() - start_time) * 1000

    return BatchMatchResponse(
        job_id=job.id,
        results=results,
        total_candidates=len(results),
        processing_time_ms=round(duration_ms, 2),
    )


@router.get("/match/{match_id}", response_model=MatchResult)
async def get_match_result(
    request: Request,
    match_id: UUID,
) -> MatchResult:
    """Get a match result by ID.

    Args:
        request: FastAPI request object.
        match_id: Match result identifier.

    Returns:
        The match result.

    Raises:
        HTTPException: If match result not found.
    """
    store: dict[UUID, MatchResult] = request.app.state.match_store
    result = store.get(match_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result {match_id} not found",
        )
    return result
