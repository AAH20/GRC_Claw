"""Priority management API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from escalation_workflow.agents.priority_router import (PriorityRouterAgent,
                                                        PriorityRouterInput)
from escalation_workflow.config import Settings, get_settings
from escalation_workflow.models.priority import (Priority, PriorityAssessment,
                                                 PriorityLevel)
from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/priorities", tags=["priorities"])

_priorities: dict[PriorityLevel, Priority] = {
    PriorityLevel.CRITICAL: Priority(
        level=PriorityLevel.CRITICAL,
        name="Critical",
        description="Critical escalations requiring immediate attention",
        sla_minutes=15,
        escalation_threshold=1,
        notification_channels=["slack", "pagerduty", "email"],
    ),
    PriorityLevel.HIGH: Priority(
        level=PriorityLevel.HIGH,
        name="High",
        description="High priority escalations with urgent response needed",
        sla_minutes=30,
        escalation_threshold=2,
        notification_channels=["slack", "email"],
    ),
    PriorityLevel.MEDIUM: Priority(
        level=PriorityLevel.MEDIUM,
        name="Medium",
        description="Medium priority escalations with standard response time",
        sla_minutes=120,
        escalation_threshold=3,
        notification_channels=["email"],
    ),
    PriorityLevel.LOW: Priority(
        level=PriorityLevel.LOW,
        name="Low",
        description="Low priority escalations with flexible response time",
        sla_minutes=480,
        escalation_threshold=5,
        notification_channels=["email"],
    ),
}


@router.get("", response_model=list[Priority])
async def list_priorities() -> list[Priority]:
    """List all priority configurations.

    Returns:
        list[Priority]: All priority levels with their configurations.
    """
    return list(_priorities.values())


@router.get("/{level}", response_model=Priority)
async def get_priority(level: PriorityLevel) -> Priority:
    """Get a specific priority configuration.

    Args:
        level: The priority level.

    Returns:
        Priority: The priority configuration.

    Raises:
        HTTPException: If priority level not found.
    """
    if level not in _priorities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Priority level {level} not found",
        )
    return _priorities[level]


@router.post("/assess", response_model=PriorityAssessment)
async def assess_priority(
    escalation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> PriorityAssessment:
    """Assess priority for an escalation.

    Args:
        escalation_id: The escalation identifier.
        settings: Application settings.

    Returns:
        PriorityAssessment: The priority assessment result.

    Raises:
        HTTPException: If escalation not found.
    """
    from escalation_workflow.api.escalations import _escalations

    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation = _escalations[escalation_id]
    agent = PriorityRouterAgent()
    return await agent.run(PriorityRouterInput(escalation=escalation))
