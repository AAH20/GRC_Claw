"""Escalation API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import Field

from moderation_queue.api.dependencies import get_logger
from moderation_queue.models import Escalation, PriorityLevel

router = APIRouter(prefix="/escalations", tags=["escalations"])

# In-memory store for demo purposes
_escalations_db: dict[UUID, Escalation] = {}


class CreateEscalationRequest(BaseModel):
    """Request model for creating an escalation."""

    item_id: UUID = Field(..., description="Item to escalate")
    reason: str = Field(..., description="Escalation reason")
    to_queue_id: UUID | None = Field(default=None, description="Destination queue")
    assigned_to: str | None = Field(default=None, description="Assigned reviewer")
    priority: PriorityLevel = Field(default=PriorityLevel.HIGH, description="Escalation priority")


class EscalationListResponse(BaseModel):
    """Response model for escalation list."""

    escalations: list[Escalation] = Field(..., description="List of escalations")
    total: int = Field(..., description="Total number of escalations")


@router.post(
    "",
    response_model=Escalation,
    status_code=status.HTTP_201_CREATED,
    summary="Create an escalation",
    description="Create a new escalation for a moderation item",
)
async def create_escalation(
    request: CreateEscalationRequest,
    logger=Depends(get_logger),
) -> Escalation:
    """Create a new escalation.

    Args:
        request: Escalation creation request.
        logger: Request logger.

    Returns:
        Escalation: Created escalation.
    """
    escalation = Escalation(
        item_id=request.item_id,
        reason=request.reason,
        to_queue_id=request.to_queue_id,
        assigned_to=request.assigned_to,
        priority=request.priority,
    )
    _escalations_db[escalation.id] = escalation
    logger.info("Created escalation", escalation_id=str(escalation.id))
    return escalation


@router.get(
    "",
    response_model=EscalationListResponse,
    summary="List escalations",
    description="Get a list of escalations",
)
async def list_escalations(
    status_filter: str | None = Query(default=None, description="Filter by status"),
    priority: PriorityLevel | None = Query(default=None, description="Filter by priority"),
    logger=Depends(get_logger),
) -> EscalationListResponse:
    """List escalations with optional filters.

    Args:
        status_filter: Filter by status.
        priority: Filter by priority.
        logger: Request logger.

    Returns:
        EscalationListResponse: List of escalations.
    """
    escalations = list(_escalations_db.values())

    if status_filter:
        escalations = [e for e in escalations if e.status == status_filter]
    if priority:
        escalations = [e for e in escalations if e.priority == priority]

    return EscalationListResponse(escalations=escalations, total=len(escalations))


@router.get(
    "/{escalation_id}",
    response_model=Escalation,
    summary="Get an escalation",
    description="Get a specific escalation by ID",
)
async def get_escalation(
    escalation_id: UUID,
    logger=Depends(get_logger),
) -> Escalation:
    """Get an escalation by ID.

    Args:
        escalation_id: Escalation identifier.
        logger: Request logger.

    Returns:
        Escalation: The requested escalation.

    Raises:
        HTTPException: If escalation not found.
    """
    escalation = _escalations_db.get(escalation_id)
    if not escalation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )
    return escalation


@router.patch(
    "/{escalation_id}/resolve",
    response_model=Escalation,
    summary="Resolve an escalation",
    description="Mark an escalation as resolved",
)
async def resolve_escalation(
    escalation_id: UUID,
    logger=Depends(get_logger),
) -> Escalation:
    """Resolve an escalation.

    Args:
        escalation_id: Escalation identifier.
        logger: Request logger.

    Returns:
        Escalation: Updated escalation.

    Raises:
        HTTPException: If escalation not found.
    """
    from datetime import datetime

    escalation = _escalations_db.get(escalation_id)
    if not escalation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation.status = "resolved"
    escalation.resolved_at = datetime.utcnow()
    _escalations_db[escalation_id] = escalation
    logger.info("Resolved escalation", escalation_id=str(escalation_id))
    return escalation
