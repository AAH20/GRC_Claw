"""Tier management endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import Tier, TierLevel, TierStatus

tiers_router = APIRouter()

# In-memory store for demo purposes
_tiers_store: dict[UUID, Tier] = {}


@tiers_router.get("", response_model=list[Tier])
async def list_tiers(
    level: TierLevel | None = None,
    status: TierStatus = TierStatus.ACTIVE,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
) -> list[Tier]:
    """List all tiers with optional filtering.

    Args:
        level: Filter by tier level.
        status: Filter by tier status.
        skip: Number of records to skip.
        limit: Maximum records to return.
        settings: Application settings.

    Returns:
        List of matching tiers.
    """
    tiers = list(_tiers_store.values())
    if level:
        tiers = [t for t in tiers if t.level == level]
    tiers = [t for t in tiers if t.status == status]
    return tiers[skip : skip + limit]


@tiers_router.post("", response_model=Tier, status_code=status.HTTP_201_CREATED)
async def create_tier(
    tier_data: dict[str, Any],
    settings: Settings = Depends(get_settings),
) -> Tier:
    """Create a new tier.

    Args:
        tier_data: Tier creation data.
        settings: Application settings.

    Returns:
        The created tier.
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    tier = Tier(
        id=uuid4(),
        name=tier_data.get("name", "New Tier"),
        level=TierLevel(tier_data.get("level", "bronze")),
        status=TierStatus(tier_data.get("status", "active")),
        description=tier_data.get("description"),
        requirements=tier_data.get("requirements", {}),
        benefits=tier_data.get("benefits", []),
        max_members=tier_data.get("max_members"),
        monthly_fee=float(tier_data.get("monthly_fee", 0.0)),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata=tier_data.get("metadata", {}),
    )
    _tiers_store[tier.id] = tier
    return tier


@tiers_router.get("/{tier_id}", response_model=Tier)
async def get_tier(
    tier_id: UUID,
    settings: Settings = Depends(get_settings),
) -> Tier:
    """Get a specific tier by ID.

    Args:
        tier_id: The tier identifier.
        settings: Application settings.

    Returns:
        The requested tier.

    Raises:
        HTTPException: If tier not found.
    """
    tier = _tiers_store.get(tier_id)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier '{tier_id}' not found",
        )
    return tier


@tiers_router.put("/{tier_id}", response_model=Tier)
async def update_tier(
    tier_id: UUID,
    tier_data: dict[str, Any],
    settings: Settings = Depends(get_settings),
) -> Tier:
    """Update an existing tier.

    Args:
        tier_id: The tier identifier.
        tier_data: Updated tier data.
        settings: Application settings.

    Returns:
        The updated tier.

    Raises:
        HTTPException: If tier not found.
    """
    tier = _tiers_store.get(tier_id)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier '{tier_id}' not found",
        )

    for key, value in tier_data.items():
        if hasattr(tier, key) and key != "id":
            setattr(tier, key, value)

    from datetime import datetime, timezone

    tier.updated_at = datetime.now(timezone.utc)
    _tiers_store[tier_id] = tier
    return tier


@tiers_router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(
    tier_id: UUID,
    settings: Settings = Depends(get_settings),
) -> None:
    """Delete a tier.

    Args:
        tier_id: The tier identifier.
        settings: Application settings.

    Raises:
        HTTPException: If tier not found.
    """
    if tier_id not in _tiers_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier '{tier_id}' not found",
        )
    del _tiers_store[tier_id]
