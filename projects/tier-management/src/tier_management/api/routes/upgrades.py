"""Upgrade request endpoints."""

from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tier_management.agents.upgrade_recommender import UpgradeRecommenderAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import UpgradeRequest

upgrades_router = APIRouter()

# In-memory store
_upgrades_store: dict[UUID, UpgradeRequest] = {}


@upgrades_router.post("", response_model=UpgradeRequest, status_code=status.HTTP_201_CREATED)
async def create_upgrade_request(
    request_data: dict[str, Any],
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UpgradeRequest:
    """Create a new upgrade request.

    Args:
        request_data: Upgrade request data.
        settings: Application settings.

    Returns:
        The created upgrade request.
    """
    agent = UpgradeRecommenderAgent()
    await agent.initialize()

    try:
        result = await agent.execute(request_data)
        _upgrades_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@upgrades_router.get("/{request_id}", response_model=UpgradeRequest)
async def get_upgrade_request(
    request_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UpgradeRequest:
    """Get a specific upgrade request by ID.

    Args:
        request_id: The request identifier.
        settings: Application settings.

    Returns:
        The requested upgrade request.

    Raises:
        HTTPException: If request not found.
    """
    request = _upgrades_store.get(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upgrade request '{request_id}' not found",
        )
    return request


@upgrades_router.get("/member/{member_id}", response_model=list[UpgradeRequest])
async def get_member_upgrades(
    member_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> list[UpgradeRequest]:
    """Get all upgrade requests for a member.

    Args:
        member_id: The member identifier.
        settings: Application settings.

    Returns:
        List of upgrade requests for the member.
    """
    return [
        r for r in _upgrades_store.values()
        if r.member_id == member_id
    ]


@upgrades_router.post("/{request_id}/approve", response_model=UpgradeRequest)
async def approve_upgrade(
    request_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UpgradeRequest:
    """Approve an upgrade request.

    Args:
        request_id: The request identifier.
        settings: Application settings.

    Returns:
        The approved upgrade request.

    Raises:
        HTTPException: If request not found.
    """
    request = _upgrades_store.get(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upgrade request '{request_id}' not found",
        )

    from datetime import datetime

    request.status = "approved"
    request.processed_at = datetime.now(UTC)
    request.processed_by = "admin"
    _upgrades_store[request_id] = request
    return request


@upgrades_router.post("/{request_id}/deny", response_model=UpgradeRequest)
async def deny_upgrade(
    request_id: UUID,
    reason: str = "Does not meet requirements",
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UpgradeRequest:
    """Deny an upgrade request.

    Args:
        request_id: The request identifier.
        reason: Denial reason.
        settings: Application settings.

    Returns:
        The denied upgrade request.

    Raises:
        HTTPException: If request not found.
    """
    request = _upgrades_store.get(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upgrade request '{request_id}' not found",
        )

    from datetime import datetime

    request.status = "denied"
    request.processed_at = datetime.now(UTC)
    request.processed_by = "admin"
    request.denial_reason = reason
    _upgrades_store[request_id] = request
    return request
