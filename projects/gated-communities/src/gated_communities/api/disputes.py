"""Dispute management routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from community_governance.api.dependencies import get_dispute_resolver
from community_governance.config.logging_config import get_logger
from community_governance.models.dispute import (Dispute, DisputeCreate,
                                                 DisputeResolution,
                                                 DisputeStatus, DisputeUpdate)
from fastapi import APIRouter, Depends, HTTPException, Query, status

if TYPE_CHECKING:
    from uuid import UUID

    from community_governance.agents import DisputeResolverAgent

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])

# In-memory storage for demo purposes
_disputes_store: dict[UUID, Dispute] = {}


@router.post("", response_model=Dispute, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_data: DisputeCreate,
    agent: DisputeResolverAgent = Depends(get_dispute_resolver),  # noqa: B008
) -> Dispute:
    """Create a new dispute.

    Args:
        dispute_data: The dispute creation data.
        agent: The dispute resolver agent.

    Returns:
        The newly created dispute.
    """
    dispute = Dispute(
        title=dispute_data.title,
        description=dispute_data.description,
        priority=dispute_data.priority,
        category=dispute_data.category,
        initiator_id=dispute_data.initiator_id,
        respondent_id=dispute_data.respondent_id,
        related_action_id=dispute_data.related_action_id,
        metadata=dispute_data.metadata,
    )
    _disputes_store[dispute.id] = dispute
    agent.add_dispute(dispute)
    logger.info(f"Dispute created: {dispute.title}", dispute_id=str(dispute.id))
    return dispute


@router.get("", response_model=list[Dispute])
async def list_disputes(
    status_filter: DisputeStatus | None = Query(  # noqa: B008
        default=None, alias="status", description="Filter by status"
    ),
    priority: str | None = Query(default=None, description="Filter by priority"),
    agent: DisputeResolverAgent = Depends(get_dispute_resolver),  # noqa: B008
) -> list[Dispute]:
    """List all disputes.

    Args:
        status_filter: Optional status filter.
        priority: Optional priority filter.
        agent: The dispute resolver agent.

    Returns:
        List of disputes.
    """
    disputes = list(_disputes_store.values())
    if status_filter:
        disputes = [d for d in disputes if d.status == status_filter]
    if priority:
        disputes = [d for d in disputes if d.priority.value == priority]
    return disputes


@router.get("/{dispute_id}", response_model=Dispute)
async def get_dispute(
    dispute_id: UUID,
    agent: DisputeResolverAgent = Depends(get_dispute_resolver),  # noqa: B008
) -> Dispute:
    """Get a specific dispute by ID.

    Args:
        dispute_id: The dispute ID.
        agent: The dispute resolver agent.

    Returns:
        The requested dispute.

    Raises:
        HTTPException: If the dispute is not found.
    """
    dispute = _disputes_store.get(dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with ID '{dispute_id}' not found",
        )
    return dispute


@router.put("/{dispute_id}", response_model=Dispute)
async def update_dispute(
    dispute_id: UUID,
    dispute_data: DisputeUpdate,
    agent: DisputeResolverAgent = Depends(get_dispute_resolver),  # noqa: B008
) -> Dispute:
    """Update an existing dispute.

    Args:
        dispute_id: The dispute ID.
        dispute_data: The dispute update data.
        agent: The dispute resolver agent.

    Returns:
        The updated dispute.

    Raises:
        HTTPException: If the dispute is not found.
    """
    dispute = _disputes_store.get(dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with ID '{dispute_id}' not found",
        )

    update_dict = dispute_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(dispute, field, value)

    from datetime import datetime

    dispute.updated_at = datetime.utcnow()
    logger.info(f"Dispute updated: {dispute.title}", dispute_id=str(dispute.id))
    return dispute


@router.post("/{dispute_id}/resolve", response_model=DisputeResolution)
async def resolve_dispute(
    dispute_id: UUID,
    context: dict | None = None,
    agent: DisputeResolverAgent = Depends(get_dispute_resolver),  # noqa: B008
) -> DisputeResolution:
    """Resolve a dispute.

    Args:
        dispute_id: The dispute ID.
        context: Optional additional context for resolution.
        agent: The dispute resolver agent.

    Returns:
        The dispute resolution.

    Raises:
        HTTPException: If the dispute is not found or resolution fails.
    """
    try:
        resolution = await agent.execute(
            {"dispute_id": dispute_id, "context": context or {}}
        )
        logger.info(f"Dispute resolved: {dispute_id}", dispute_id=str(dispute_id))
        return resolution
    except Exception as e:
        logger.error(f"Failed to resolve dispute {dispute_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resolve dispute: {str(e)}",
        ) from e
