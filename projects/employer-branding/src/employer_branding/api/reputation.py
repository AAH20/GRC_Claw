"""Reputation management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from employer_branding.agents.reputation_manager import ReputationManagerAgent
from employer_branding.models import ReputationAnalysisRequest, ReputationScore

router = APIRouter(prefix="/api/v1/reputation", tags=["reputation"])

# In-memory store
_reputation_store: dict[UUID, ReputationScore] = {}


def get_reputation_agent() -> ReputationManagerAgent:
    """Dependency to get reputation manager agent."""
    return ReputationManagerAgent()


@router.post("/analyze", response_model=ReputationScore, status_code=status.HTTP_201_CREATED)
async def analyze_reputation(
    request: ReputationAnalysisRequest,
    agent: ReputationManagerAgent = Depends(get_reputation_agent),
) -> ReputationScore:
    """Analyze employer reputation.

    Args:
        request: Reputation analysis request.
        agent: Reputation manager agent.

    Returns:
        ReputationScore with detailed analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        score = await agent.run(request)
        _reputation_store[score.id] = score
        return score
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation analysis failed: {exc}",
        ) from exc


@router.get("/{score_id}", response_model=ReputationScore)
async def get_reputation_score(score_id: UUID) -> ReputationScore:
    """Get a reputation score by ID.

    Args:
        score_id: Score UUID.

    Returns:
        ReputationScore if found.

    Raises:
        HTTPException: If score not found.
    """
    if score_id not in _reputation_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reputation score {score_id} not found",
        )
    return _reputation_store[score_id]


@router.get("/company/{company_name}", response_model=list[ReputationScore])
async def get_company_reputation(company_name: str) -> list[ReputationScore]:
    """Get reputation scores for a company.

    Args:
        company_name: Company name.

    Returns:
        List of ReputationScore objects.
    """
    return [
        s for s in _reputation_store.values()
        if s.company_name.lower() == company_name.lower()
    ]


@router.post("/compare", response_model=list[ReputationScore], status_code=status.HTTP_201_CREATED)
async def compare_reputations(
    companies: list[str],
    agent: ReputationManagerAgent = Depends(get_reputation_agent),
) -> list[ReputationScore]:
    """Compare reputation across multiple companies.

    Args:
        companies: List of company names.
        agent: Reputation manager agent.

    Returns:
        List of ReputationScore objects for comparison.

    Raises:
        HTTPException: If comparison fails.
    """
    try:
        results = []
        for company_name in companies:
            request = ReputationAnalysisRequest(
                company_name=company_name,
                sources=[],
                period_days=90,
                include_recommendations=True,
            )
            score = await agent.run(request)
            _reputation_store[score.id] = score
            results.append(score)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation comparison failed: {exc}",
        ) from exc
