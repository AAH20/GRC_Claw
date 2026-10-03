"""Reputation Score API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from reputation_system.agents.reputation_scorer import ReputationScorerAgent, ScoringInput
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import (
    ReputationScore,
    ReputationScoreCreate,
    ReputationScoreUpdate,
)

router = APIRouter(prefix="/reputation", tags=["reputation"])

# In-memory store for demo purposes
_scores: dict[str, ReputationScore] = {}


@router.post(
    "/scores", response_model=ReputationScore, status_code=status.HTTP_201_CREATED
)
async def create_reputation_score(
    data: ReputationScoreCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationScore:
    """Create a new reputation score for a member.

    Args:
        data: Reputation score creation data.
        settings: Application settings.

    Returns:
        Created reputation score.

    Raises:
        HTTPException: If member already has a score.
    """
    if data.member_id in _scores:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Reputation score already exists for member {data.member_id}",
        )

    score = ReputationScore(
        member_id=data.member_id,
        score=data.initial_score,
        metadata=data.metadata or {},
    )
    _scores[data.member_id] = score
    return score


@router.get("/scores/{member_id}", response_model=ReputationScore)
async def get_reputation_score(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationScore:
    """Get reputation score for a member.

    Args:
        member_id: Member identifier.
        settings: Application settings.

    Returns:
        Member's reputation score.

    Raises:
        HTTPException: If member not found.
    """
    if member_id not in _scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reputation score not found for member {member_id}",
        )
    return _scores[member_id]


@router.put("/scores/{member_id}", response_model=ReputationScore)
async def update_reputation_score(
    member_id: str,
    data: ReputationScoreUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationScore:
    """Update reputation score for a member.

    Args:
        member_id: Member identifier.
        data: Update data.
        settings: Application settings.

    Returns:
        Updated reputation score.

    Raises:
        HTTPException: If member not found.
    """
    if member_id not in _scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reputation score not found for member {member_id}",
        )

    score = _scores[member_id]
    if data.score is not None:
        score.score = data.score
    if data.trust_tier is not None:
        score.trust_tier = data.trust_tier
    if data.metadata is not None:
        score.metadata.update(data.metadata)
    return score


@router.delete("/scores/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reputation_score(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete reputation score for a member.

    Args:
        member_id: Member identifier.
        settings: Application settings.

    Raises:
        HTTPException: If member not found.
    """
    if member_id not in _scores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reputation score not found for member {member_id}",
        )
    del _scores[member_id]


@router.get("/scores", response_model=list[ReputationScore])
async def list_reputation_scores(
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ReputationScore]:
    """List all reputation scores with pagination.

    Args:
        settings: Application settings.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of reputation scores.
    """
    scores = list(_scores.values())
    return scores[skip : skip + limit]


@router.post("/scores/{member_id}/calculate", response_model=dict[str, Any])
async def calculate_reputation_score(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    contributions: Annotated[int, Query(ge=0)] = 0,
    positive_feedback: Annotated[int, Query(ge=0)] = 0,
    negative_feedback: Annotated[int, Query(ge=0)] = 0,
    account_age_days: Annotated[int, Query(ge=0)] = 0,
    badge_count: Annotated[int, Query(ge=0)] = 0,
    recent_activity_score: Annotated[float, Query(ge=0.0, le=1.0)] = 0.0,
    quality_score: Annotated[float, Query(ge=0.0, le=1.0)] = 0.0,
) -> dict[str, Any]:
    """Calculate reputation score using the AI agent.

    Args:
        member_id: Member identifier.
        settings: Application settings.
        contributions: Total contributions.
        positive_feedback: Positive feedback count.
        negative_feedback: Negative feedback count.
        account_age_days: Account age in days.
        badge_count: Number of badges earned.
        recent_activity_score: Recent activity score (0-1).
        quality_score: Quality score (0-1).

    Returns:
        Calculated score with factors and confidence.
    """
    agent = ReputationScorerAgent(settings=settings)
    input_data = ScoringInput(
        member_id=member_id,
        contributions=contributions,
        positive_feedback=positive_feedback,
        negative_feedback=negative_feedback,
        account_age_days=account_age_days,
        badge_count=badge_count,
        recent_activity_score=recent_activity_score,
        quality_score=quality_score,
    )
    result = await agent.run(input_data)
    return result.model_dump()
