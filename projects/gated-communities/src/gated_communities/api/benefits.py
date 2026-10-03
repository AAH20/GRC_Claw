"""Benefit management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from tier_management.agents.benefit_manager import BenefitManagerAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import Benefit

if TYPE_CHECKING:
    from uuid import UUID

benefits_router = APIRouter()

# In-memory store
_benefits_store: dict[UUID, Benefit] = {}
_agent_instance: BenefitManagerAgent | None = None


async def _get_agent(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> BenefitManagerAgent:  # noqa: B008
    """Get or create the benefit manager agent singleton.

    Args:
        settings: Application settings.

    Returns:
        The benefit manager agent instance.
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BenefitManagerAgent()
        await agent_initialize()
    return _agent_instance


async def agent_initialize() -> None:
    """Initialize the benefit manager agent."""
    if _agent_instance is not None:
        await _agent_instance.initialize()


@benefits_router.post("", response_model=Benefit, status_code=status.HTTP_201_CREATED)
async def create_benefit(
    benefit_data: dict[str, Any],
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
    agent: BenefitManagerAgent = Depends(_get_agent),  # noqa: B008
) -> Benefit:
    """Create a new benefit.

    Args:
        benefit_data: Benefit creation data.
        settings: Application settings.
        agent: The benefit manager agent.

    Returns:
        The created benefit.
    """
    try:
        result = await agent.execute(
            {
                "operation": "create",
                "benefit_data": benefit_data,
            }
        )
        _benefits_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@benefits_router.get("/{benefit_id}", response_model=Benefit)
async def get_benefit(
    benefit_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
) -> Benefit:
    """Get a specific benefit by ID.

    Args:
        benefit_id: The benefit identifier.
        settings: Application settings.

    Returns:
        The requested benefit.

    Raises:
        HTTPException: If benefit not found.
    """
    benefit = _benefits_store.get(benefit_id)
    if not benefit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benefit '{benefit_id}' not found",
        )
    return benefit


@benefits_router.get("", response_model=list[Benefit])
async def list_benefits(
    tier_id: UUID | None = None,
    active_only: bool = True,
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
) -> list[Benefit]:
    """List benefits with optional filtering.

    Args:
        tier_id: Filter by tier.
        active_only: Only return active benefits.
        settings: Application settings.

    Returns:
        List of matching benefits.
    """
    benefits = list(_benefits_store.values())
    if tier_id:
        benefits = [b for b in benefits if tier_id in b.tier_ids]
    if active_only:
        benefits = [b for b in benefits if b.active]
    return benefits


@benefits_router.put("/{benefit_id}", response_model=Benefit)
async def update_benefit(
    benefit_id: UUID,
    benefit_data: dict[str, Any],
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
    agent: BenefitManagerAgent = Depends(_get_agent),  # noqa: B008
) -> Benefit:
    """Update an existing benefit.

    Args:
        benefit_id: The benefit identifier.
        benefit_data: Updated benefit data.
        settings: Application settings.
        agent: The benefit manager agent.

    Returns:
        The updated benefit.

    Raises:
        HTTPException: If benefit not found.
    """
    try:
        result = await agent.execute(
            {
                "operation": "update",
                "benefit_id": str(benefit_id),
                "benefit_data": benefit_data,
            }
        )
        _benefits_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@benefits_router.post("/{benefit_id}/deactivate", response_model=Benefit)
async def deactivate_benefit(
    benefit_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
    agent: BenefitManagerAgent = Depends(_get_agent),  # noqa: B008
) -> Benefit:
    """Deactivate a benefit.

    Args:
        benefit_id: The benefit identifier.
        settings: Application settings.
        agent: The benefit manager agent.

    Returns:
        The deactivated benefit.

    Raises:
        HTTPException: If benefit not found.
    """
    try:
        result = await agent.execute(
            {
                "operation": "deactivate",
                "benefit_id": str(benefit_id),
            }
        )
        _benefits_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@benefits_router.post("/{benefit_id}/assign", response_model=Benefit)
async def assign_benefit_to_tiers(
    benefit_id: UUID,
    tier_ids: list[UUID],
    settings: Settings = Depends(get_settings),  # noqa: B008  # noqa: B008
    agent: BenefitManagerAgent = Depends(_get_agent),  # noqa: B008
) -> Benefit:
    """Assign a benefit to additional tiers.

    Args:
        benefit_id: The benefit identifier.
        tier_ids: List of tier IDs to assign.
        settings: Application settings.
        agent: The benefit manager agent.

    Returns:
        The updated benefit.

    Raises:
        HTTPException: If benefit not found.
    """
    try:
        result = await agent.execute(
            {
                "operation": "assign",
                "benefit_id": str(benefit_id),
                "tier_ids": [str(t) for t in tier_ids],
            }
        )
        _benefits_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
