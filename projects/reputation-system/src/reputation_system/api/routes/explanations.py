"""Reputation Explanation API routes."""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from reputation_system.agents.reputation_explainer import (
    ReputationExplainerAgent,
    ExplanationInput,
)
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import ReputationExplanation, ReputationExplanationCreate

router = APIRouter(prefix="/explanations", tags=["explanations"])

# In-memory store for demo purposes
_explanations: Dict[UUID, ReputationExplanation] = {}


@router.post("", response_model=ReputationExplanation, status_code=status.HTTP_201_CREATED)
async def create_explanation(
    data: ReputationExplanationCreate,
    settings: Settings = Depends(get_settings),
) -> ReputationExplanation:
    """Create a new reputation explanation.

    Args:
        data: Explanation creation data.
        settings: Application settings.

    Returns:
        Created explanation.
    """
    explanation = ReputationExplanation(**data.model_dump())
    _explanations[explanation.id] = explanation
    return explanation


@router.get("/{explanation_id}", response_model=ReputationExplanation)
async def get_explanation(
    explanation_id: UUID,
    settings: Settings = Depends(get_settings),
) -> ReputationExplanation:
    """Get an explanation by ID.

    Args:
        explanation_id: Explanation identifier.
        settings: Application settings.

    Returns:
        Explanation details.

    Raises:
        HTTPException: If explanation not found.
    """
    if explanation_id not in _explanations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Explanation {explanation_id} not found",
        )
    return _explanations[explanation_id]


@router.get("/member/{member_id}", response_model=List[ReputationExplanation])
async def get_member_explanations(
    member_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    settings: Settings = Depends(get_settings),
) -> List[ReputationExplanation]:
    """Get explanations for a member.

    Args:
        member_id: Member identifier.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        settings: Application settings.

    Returns:
        List of explanations for the member.
    """
    explanations = [e for e in _explanations.values() if e.member_id == member_id]
    return explanations[skip : skip + limit]


@router.post("/generate/{member_id}")
async def generate_explanation(
    member_id: str,
    current_score: int = Query(..., ge=0, le=1000),
    trust_tier: str = Query(...),
    factors: List[Dict] = Query(default_factory=list),
    recent_actions: List[Dict] = Query(default_factory=list),
    badge_count: int = Query(0, ge=0),
    account_age_days: int = Query(0, ge=0),
    settings: Settings = Depends(get_settings),
) -> Dict:
    """Generate a reputation explanation using the AI agent.

    Args:
        member_id: Member identifier.
        current_score: Current reputation score.
        trust_tier: Current trust tier level.
        factors: Scoring factors.
        recent_actions: Recent actions.
        badge_count: Number of badges.
        account_age_days: Account age in days.
        settings: Application settings.

    Returns:
        Generated explanation with recommendations.
    """
    from reputation_system.models.schemas import TrustTierLevel

    agent = ReputationExplainerAgent(settings=settings)
    input_data = ExplanationInput(
        member_id=member_id,
        current_score=current_score,
        trust_tier=TrustTierLevel(trust_tier),
        factors=factors,
        recent_actions=recent_actions,
        badge_count=badge_count,
        account_age_days=account_age_days,
    )
    result = await agent.run(input_data)
    return result.model_dump()
