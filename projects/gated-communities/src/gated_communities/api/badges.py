"""Badge API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from reputation_system.agents.badge_manager import BadgeEvaluationInput, BadgeManagerAgent
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import Badge, BadgeCreate, BadgeUpdate

router = APIRouter(prefix="/badges", tags=["badges"])

# In-memory store for demo purposes
_badges: dict[UUID, Badge] = {}
_member_badges: dict[str, list[str]] = {}


@router.post("", response_model=Badge, status_code=status.HTTP_201_CREATED)
async def create_badge(
    data: BadgeCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Badge:
    """Create a new badge.

    Args:
        data: Badge creation data.
        settings: Application settings.

    Returns:
        Created badge.
    """
    badge = Badge(**data.model_dump(exclude_none=True))
    _badges[badge.id] = badge
    return badge


@router.get("/{badge_id}", response_model=Badge)
async def get_badge(
    badge_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Badge:
    """Get a badge by ID.

    Args:
        badge_id: Badge identifier.
        settings: Application settings.

    Returns:
        Badge details.

    Raises:
        HTTPException: If badge not found.
    """
    if badge_id not in _badges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge {badge_id} not found",
        )
    return _badges[badge_id]


@router.get("", response_model=list[Badge])
async def list_badges(
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    category: Annotated[str | None, Query()] = None,
) -> list[Badge]:
    """List all badges with pagination and filtering.

    Args:
        settings: Application settings.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        category: Filter by category.

    Returns:
        List of badges.
    """
    badges = list(_badges.values())
    if category:
        badges = [b for b in badges if b.category.value == category]
    return badges[skip : skip + limit]


@router.put("/{badge_id}", response_model=Badge)
async def update_badge(
    badge_id: UUID,
    data: BadgeUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Badge:
    """Update a badge.

    Args:
        badge_id: Badge identifier.
        data: Update data.
        settings: Application settings.

    Returns:
        Updated badge.

    Raises:
        HTTPException: If badge not found.
    """
    if badge_id not in _badges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge {badge_id} not found",
        )

    badge = _badges[badge_id]
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(badge, field, value)
    return badge


@router.delete("/{badge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_badge(
    badge_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete a badge.

    Args:
        badge_id: Badge identifier.
        settings: Application settings.

    Raises:
        HTTPException: If badge not found.
    """
    if badge_id not in _badges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge {badge_id} not found",
        )
    del _badges[badge_id]


@router.post("/evaluate/{member_id}")
async def evaluate_member_badges(
    member_id: str,
    badge_criteria: dict,
    member_stats: dict,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Evaluate badge eligibility for a member using the AI agent.

    Args:
        member_id: Member identifier.
        badge_criteria: Badge criteria to evaluate.
        member_stats: Member statistics.
        settings: Application settings.

    Returns:
        Badge evaluation results.
    """
    agent = BadgeManagerAgent(settings=settings)
    current_badges = _member_badges.get(member_id, [])
    input_data = BadgeEvaluationInput(
        member_id=member_id,
        badge_criteria=badge_criteria,
        member_stats=member_stats,
        current_badges=current_badges,
    )
    result = await agent.run(input_data)
    return result.model_dump()
