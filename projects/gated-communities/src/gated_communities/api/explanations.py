"""Reputation Explanation API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from reputation_system.agents.reputation_explainer import (
    ExplanationInput, ReputationExplainerAgent)
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import (ReputationExplanation,
                                              ReputationExplanationCreate)

router = APIRouter(prefix="/explanations", tags=["explanations"])

# In-memory store for demo purposes
_explanations: dict[UUID, ReputationExplanation] = {}


@router.post(
    "", response_model=ReputationExplanation, status_code=status.HTTP_201_CREATED
)
async def create_explanation(
    data: ReputationExplanationCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReputationExplanation:
    """Create a new reputation explanation.

    Args:
        data: Explanation creation data.
        settings: Application settings.

    Returns:
        Created explanation.
    """
    explanation = ReputationExplanation(**data.model_dump(exclude_none=True))
    _explanations[explanation.id] = explanation
    return explanation


@router.get("/{explanation_id}", response_model=ReputationExplanation)
async def get_explanation(
    explanation_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
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


@router.get("/member/{member_id}", response_model=list[ReputationExplanation])
async def get_member_explanations(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[ReputationExplanation]:
    """Get explanations for a member.

    Args:
        member_id: Member identifier.
        settings: Application settings.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of explanations for the member.
    """
    explanations = [e for e in _explanations.values() if e.member_id == member_id]
    return explanations[skip : skip + limit]


@router.post("/generate/{member_id}")
async def generate_explanation(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    current_score: Annotated[int, Query(ge=0, le=1000)],
    trust_tier: Annotated[str, Query()],
    factors: Annotated[str, Query()] = "",
    recent_actions: Annotated[str, Query()] = "",
    badge_count: Annotated[int, Query(ge=0)] = 0,
    account_age_days: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    """Generate a reputation explanation using the AI agent.

    Args:
        member_id: Member identifier.
        settings: Application settings.
        current_score: Current reputation score.
        trust_tier: Current trust tier level.
        factors: Scoring factors.
        recent_actions: Recent actions.
        badge_count: Number of badges.
        account_age_days: Account age in days.

    Returns:
        Generated explanation with recommendations.
    """
    from reputation_system.models.schemas import TrustTierLevel

    agent = ReputationExplainerAgent(settings=settings)
    factors_list = [
        {"name": f, "value": 0, "impact": 0.0} for f in factors.split(",") if f
    ]
    actions_list = [
        {"action": a, "score_change": 0} for a in recent_actions.split(",") if a
    ]
    input_data = ExplanationInput(
        member_id=member_id,
        current_score=current_score,
        trust_tier=TrustTierLevel(trust_tier),
        factors=factors_list,
        recent_actions=actions_list,
        badge_count=badge_count,
        account_age_days=account_age_days,
    )
    result = await agent.run(input_data)
    return result.model_dump()
