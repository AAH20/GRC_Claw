"""Trust score API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from content_marketplace.agents.trust_scorer import TrustScorerAgent
from content_marketplace.models.trust import TrustScore, TrustScoreCreate

logger = logging.getLogger(__name__)
router = APIRouter()


_trust_agent_instance: TrustScorerAgent | None = None


def get_trust_agent() -> TrustScorerAgent:
    """Dependency to get the trust scorer agent (singleton)."""
    global _trust_agent_instance
    if _trust_agent_instance is None:
        _trust_agent_instance = TrustScorerAgent()
    return _trust_agent_instance


@router.post("", response_model=TrustScore, status_code=status.HTTP_201_CREATED)
async def create_trust_score(
    data: TrustScoreCreate,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> TrustScore:
    """Create a new trust score for a user."""
    return await agent.create_trust_score(data)


@router.get("/{user_id}", response_model=TrustScore)
async def get_trust_score(
    user_id: str,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> TrustScore:
    """Get a user's trust score."""
    try:
        return await agent.get_trust_score(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trust score not found")


@router.post("/{user_id}/update", response_model=TrustScore)
async def update_trust_score(
    user_id: str,
    transaction_success: bool = False,
    dispute: bool = False,
    new_rating: float | None = None,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> TrustScore:
    """Update a user's trust score based on new activity."""
    try:
        return await agent.update_trust_score(
            user_id, transaction_success=transaction_success, dispute=dispute, new_rating=new_rating
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trust score not found")


@router.post("/{user_id}/verify", response_model=TrustScore)
async def verify_user(
    user_id: str,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> TrustScore:
    """Mark a user as verified."""
    try:
        return await agent.verify_user(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trust score not found")


@router.get("/{user_id}/behavior")
async def analyze_user_behavior(
    user_id: str,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> dict:
    """Analyze user behavior for trust assessment."""
    try:
        return await agent.analyze_user_behavior(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trust score not found")


@router.get("/leaderboard/top")
async def get_trust_leaderboard(
    limit: int = 10,
    agent: TrustScorerAgent = Depends(get_trust_agent),  # noqa: B008
) -> list[TrustScore]:
    """Get top users by trust score."""
    return await agent.get_leaderboard(limit=limit)
