"""Trust Tier API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from reputation_system.agents.trust_tier import TrustTierAgent, TrustTierInput
from reputation_system.config.settings import Settings, get_settings
from reputation_system.models.schemas import TrustTier, TrustTierCreate, TrustTierUpdate

router = APIRouter(prefix="/trust-tiers", tags=["trust-tiers"])

# In-memory store for demo purposes
_tiers: dict[UUID, TrustTier] = {}


@router.post("", response_model=TrustTier, status_code=status.HTTP_201_CREATED)
async def create_trust_tier(
    data: TrustTierCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TrustTier:
    """Create a new trust tier.

    Args:
        data: Trust tier creation data.
        settings: Application settings.

    Returns:
        Created trust tier.
    """
    tier = TrustTier(**data.model_dump(exclude_none=True))
    _tiers[tier.id] = tier
    return tier


@router.get("/{tier_id}", response_model=TrustTier)
async def get_trust_tier(
    tier_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TrustTier:
    """Get a trust tier by ID.

    Args:
        tier_id: Trust tier identifier.
        settings: Application settings.

    Returns:
        Trust tier details.

    Raises:
        HTTPException: If tier not found.
    """
    if tier_id not in _tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trust tier {tier_id} not found",
        )
    return _tiers[tier_id]


@router.get("", response_model=list[TrustTier])
async def list_trust_tiers(
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[TrustTier]:
    """List all trust tiers with pagination.

    Args:
        settings: Application settings.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of trust tiers.
    """
    tiers = list(_tiers.values())
    return tiers[skip : skip + limit]


@router.put("/{tier_id}", response_model=TrustTier)
async def update_trust_tier(
    tier_id: UUID,
    data: TrustTierUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TrustTier:
    """Update a trust tier.

    Args:
        tier_id: Trust tier identifier.
        data: Update data.
        settings: Application settings.

    Returns:
        Updated trust tier.

    Raises:
        HTTPException: If tier not found.
    """
    if tier_id not in _tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trust tier {tier_id} not found",
        )

    tier = _tiers[tier_id]
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tier, field, value)
    return tier


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trust_tier(
    tier_id: UUID,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete a trust tier.

    Args:
        tier_id: Trust tier identifier.
        settings: Application settings.

    Raises:
        HTTPException: If tier not found.
    """
    if tier_id not in _tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trust tier {tier_id} not found",
        )
    del _tiers[tier_id]


@router.post("/evaluate/{member_id}")
async def evaluate_trust_tier(
    member_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    current_score: Annotated[int, Query(ge=0, le=1000)],
    current_tier: Annotated[str, Query()],
    account_age_days: Annotated[int, Query(ge=0)] = 0,
    violation_count: Annotated[int, Query(ge=0)] = 0,
    verification_status: Annotated[bool, Query()] = False,
) -> dict:
    """Evaluate trust tier for a member using the AI agent.

    Args:
        member_id: Member identifier.
        settings: Application settings.
        current_score: Current reputation score.
        current_tier: Current trust tier level.
        account_age_days: Account age in days.
        violation_count: Number of violations.
        verification_status: Identity verification status.

    Returns:
        Trust tier evaluation results.
    """
    from reputation_system.models.schemas import TrustTierLevel

    agent = TrustTierAgent(settings=settings)
    input_data = TrustTierInput(
        member_id=member_id,
        current_score=current_score,
        current_tier=TrustTierLevel(current_tier),
        account_age_days=account_age_days,
        violation_count=violation_count,
        verification_status=verification_status,
    )
    result = await agent.run(input_data)
    return result.model_dump()
