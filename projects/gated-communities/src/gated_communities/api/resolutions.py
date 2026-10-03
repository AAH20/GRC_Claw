"""Resolution management API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from escalation_workflow.agents.resolution_optimizer import (
    ResolutionOptimizerAgent, ResolutionOptimizerInput)
from escalation_workflow.config import Settings, get_settings
from escalation_workflow.models.resolution import (Resolution,
                                                   ResolutionCreate,
                                                   ResolutionStatus)
from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/resolutions", tags=["resolutions"])

_resolutions: dict[UUID, Resolution] = {}


@router.post("", response_model=Resolution, status_code=status.HTTP_201_CREATED)
async def create_resolution(data: ResolutionCreate) -> Resolution:
    """Create a new resolution.

    Args:
        data: Resolution creation data.

    Returns:
        Resolution: The created resolution.
    """
    resolution = Resolution(**data.model_dump())
    _resolutions[resolution.id] = resolution

    from escalation_workflow.api.escalations import _escalations

    if data.escalation_id in _escalations:
        _escalations[data.escalation_id].resolution_id = resolution.id

    return resolution


@router.get("", response_model=list[Resolution])
async def list_resolutions(
    status_filter: ResolutionStatus | None = None,
) -> list[Resolution]:
    """List resolutions with optional filtering.

    Args:
        status_filter: Filter by resolution status.

    Returns:
        list[Resolution]: List of resolutions.
    """
    items = list(_resolutions.values())
    if status_filter:
        items = [r for r in items if r.status == status_filter]
    return items


@router.get("/{resolution_id}", response_model=Resolution)
async def get_resolution(resolution_id: UUID) -> Resolution:
    """Get a specific resolution.

    Args:
        resolution_id: The resolution identifier.

    Returns:
        Resolution: The requested resolution.

    Raises:
        HTTPException: If resolution not found.
    """
    if resolution_id not in _resolutions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resolution {resolution_id} not found",
        )
    return _resolutions[resolution_id]


@router.post("/{resolution_id}/optimize", response_model=ResolutionCreate)
async def optimize_resolution(
    resolution_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ResolutionCreate:
    """Optimize a resolution using the resolution optimizer agent.

    Args:
        resolution_id: The resolution identifier.
        settings: Application settings.

    Returns:
        ResolutionCreate: Optimized resolution proposal.

    Raises:
        HTTPException: If resolution not found.
    """
    if resolution_id not in _resolutions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resolution {resolution_id} not found",
        )

    resolution = _resolutions[resolution_id]
    agent = ResolutionOptimizerAgent()

    from escalation_workflow.api.escalations import _escalations

    escalation = _escalations.get(resolution.escalation_id)

    if not escalation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {resolution.escalation_id} not found",
        )

    return await agent.run(
        ResolutionOptimizerInput(
            escalation=escalation,
            previous_resolutions=[],
        )
    )


@router.post("/{resolution_id}/approve", response_model=Resolution)
async def approve_resolution(resolution_id: UUID) -> Resolution:
    """Approve a resolution.

    Args:
        resolution_id: The resolution identifier.

    Returns:
        Resolution: The approved resolution.

    Raises:
        HTTPException: If resolution not found.
    """
    if resolution_id not in _resolutions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resolution {resolution_id} not found",
        )

    resolution = _resolutions[resolution_id]
    resolution.status = ResolutionStatus.APPROVED
    _resolutions[resolution_id] = resolution
    return resolution


@router.post("/{resolution_id}/verify", response_model=Resolution)
async def verify_resolution(
    resolution_id: UUID,
    verified_by: str = "system",
) -> Resolution:
    """Verify a resolution.

    Args:
        resolution_id: The resolution identifier.
        verified_by: Who verified the resolution.

    Returns:
        Resolution: The verified resolution.

    Raises:
        HTTPException: If resolution not found.
    """
    if resolution_id not in _resolutions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resolution {resolution_id} not found",
        )

    from datetime import datetime

    resolution = _resolutions[resolution_id]
    resolution.status = ResolutionStatus.VERIFIED
    resolution.verified_by = verified_by
    resolution.verified_at = datetime.utcnow()
    _resolutions[resolution_id] = resolution
    return resolution
