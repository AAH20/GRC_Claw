"""Tier evaluation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from tier_management.agents.tier_evaluator import TierEvaluatorAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import TierEvaluation

if TYPE_CHECKING:
    from uuid import UUID

evaluation_router = APIRouter()

# In-memory store
_evaluations_store: dict[UUID, TierEvaluation] = {}


@evaluation_router.post(
    "", response_model=TierEvaluation, status_code=status.HTTP_201_CREATED
)
async def create_evaluation(
    evaluation_data: dict[str, Any],
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TierEvaluation:
    """Create a new tier evaluation for a member.

    Args:
        evaluation_data: Evaluation request data.
        settings: Application settings.

    Returns:
        The created evaluation result.
    """
    agent = TierEvaluatorAgent()
    await agent.initialize()

    try:
        result = await agent.execute(evaluation_data)
        _evaluations_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@evaluation_router.get("/{evaluation_id}", response_model=TierEvaluation)
async def get_evaluation(
    evaluation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TierEvaluation:
    """Get a specific evaluation by ID.

    Args:
        evaluation_id: The evaluation identifier.
        settings: Application settings.

    Returns:
        The requested evaluation.

    Raises:
        HTTPException: If evaluation not found.
    """
    evaluation = _evaluations_store.get(evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
        )
    return evaluation


@evaluation_router.get("/member/{member_id}", response_model=list[TierEvaluation])
async def get_member_evaluations(
    member_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> list[TierEvaluation]:
    """Get all evaluations for a specific member.

    Args:
        member_id: The member identifier.
        settings: Application settings.

    Returns:
        List of evaluations for the member.
    """
    return [e for e in _evaluations_store.values() if e.member_id == member_id]


@evaluation_router.post("/{evaluation_id}/reevaluate", response_model=TierEvaluation)
async def reevaluate_member(
    evaluation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TierEvaluation:
    """Re-evaluate a member with updated metrics.

    Args:
        evaluation_id: The original evaluation identifier.
        settings: Application settings.

    Returns:
        The new evaluation result.

    Raises:
        HTTPException: If original evaluation not found.
    """
    original = _evaluations_store.get(evaluation_id)
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found",
        )

    agent = TierEvaluatorAgent()
    await agent.initialize()

    input_data = {
        "member_id": str(original.member_id),
        "current_tier_id": str(original.current_tier_id),
        "target_tier_id": str(original.target_tier_id),
    }

    result = await agent.execute(input_data)
    _evaluations_store[result.id] = result
    return result
