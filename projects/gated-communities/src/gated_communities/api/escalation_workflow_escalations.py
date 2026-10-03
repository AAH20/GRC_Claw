"""Escalation management API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from escalation_workflow.agents.auto_resolver import AutoResolverAgent, AutoResolverInput
from escalation_workflow.agents.escalation_analyzer import (
    EscalationAnalyzerAgent,
    EscalationAnalyzerInput,
)
from escalation_workflow.agents.priority_router import PriorityRouterAgent, PriorityRouterInput
from escalation_workflow.agents.resolution_optimizer import ResolutionOptimizerAgent
from escalation_workflow.agents.sla_tracker import SLATrackerAgent
from escalation_workflow.config import Settings, get_settings
from escalation_workflow.models.analysis import EscalationAnalysis
from escalation_workflow.models.escalation import (
    Escalation,
    EscalationCreate,
    EscalationStatus,
    EscalationUpdate,
)
from escalation_workflow.models.priority import PriorityAssessment
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

if TYPE_CHECKING:
    from uuid import UUID

    from escalation_workflow.models.resolution import Resolution
    from escalation_workflow.models.sla import SLA

router = APIRouter(prefix="/escalations", tags=["escalations"])

# In-memory store for demo purposes - replace with database in production
_escalations: dict[UUID, Escalation] = {}
_resolutions: dict[UUID, Resolution] = {}
_slas: dict[UUID, SLA] = {}
_analyses: dict[UUID, EscalationAnalysis] = {}


class EscalationListResponse(BaseModel):
    """Response model for escalation list."""

    items: list[Escalation]
    total: int
    page: int
    page_size: int


class BulkEscalationCreateRequest(BaseModel):
    """Request model for bulk escalation creation."""

    escalations: list[EscalationCreate]


class EscalationActionResponse(BaseModel):
    """Response model for escalation actions."""

    success: bool
    message: str
    data: dict[str, Any] | None = None


def _get_priority_router(settings: Settings) -> PriorityRouterAgent:
    """Get or create priority router agent.

    Args:
        settings: Application settings.

    Returns:
        PriorityRouterAgent: The priority router agent.
    """
    return PriorityRouterAgent()


def _get_sla_tracker(settings: Settings) -> SLATrackerAgent:
    """Get or create SLA tracker agent.

    Args:
        settings: Application settings.

    Returns:
        SLATrackerAgent: The SLA tracker agent.
    """
    return SLATrackerAgent()


def _get_resolution_optimizer(settings: Settings) -> ResolutionOptimizerAgent:
    """Get or create resolution optimizer agent.

    Args:
        settings: Application settings.

    Returns:
        ResolutionOptimizerAgent: The resolution optimizer agent.
    """
    return ResolutionOptimizerAgent()


def _get_escalation_analyzer(settings: Settings) -> EscalationAnalyzerAgent:
    """Get or create escalation analyzer agent.

    Args:
        settings: Application settings.

    Returns:
        EscalationAnalyzerAgent: The escalation analyzer agent.
    """
    return EscalationAnalyzerAgent()


def _get_auto_resolver(settings: Settings) -> AutoResolverAgent:
    """Get or create auto resolver agent.

    Args:
        settings: Application settings.

    Returns:
        AutoResolverAgent: The auto resolver agent.
    """
    return AutoResolverAgent()


@router.post("", response_model=Escalation, status_code=status.HTTP_201_CREATED)
async def create_escalation(
    data: EscalationCreate,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> Escalation:
    """Create a new escalation.

    Args:
        data: Escalation creation data.
        settings: Application settings.

    Returns:
        Escalation: The created escalation.
    """
    escalation = Escalation(**data.model_dump())
    _escalations[escalation.id] = escalation
    return escalation


@router.get("", response_model=EscalationListResponse)
async def list_escalations(
    status_filter: EscalationStatus | None = Query(
        default=None, alias="status"
    ),  # noqa: B008
    priority: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EscalationListResponse:
    """List escalations with optional filtering.

    Args:
        status_filter: Filter by status.
        priority: Filter by priority.
        category: Filter by category.
        page: Page number.
        page_size: Items per page.

    Returns:
        EscalationListResponse: Paginated list of escalations.
    """
    items = list(_escalations.values())

    if status_filter:
        items = [e for e in items if e.status == status_filter]
    if priority:
        items = [e for e in items if e.priority == priority]
    if category:
        items = [e for e in items if e.category == category]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return EscalationListResponse(
        items=items[start:end],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{escalation_id}", response_model=Escalation)
async def get_escalation(escalation_id: UUID) -> Escalation:
    """Get a specific escalation by ID.

    Args:
        escalation_id: The escalation identifier.

    Returns:
        Escalation: The requested escalation.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )
    return _escalations[escalation_id]


@router.patch("/{escalation_id}", response_model=Escalation)
async def update_escalation(
    escalation_id: UUID,
    data: EscalationUpdate,
) -> Escalation:
    """Update an existing escalation.

    Args:
        escalation_id: The escalation identifier.
        data: Update data.

    Returns:
        Escalation: The updated escalation.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation = _escalations[escalation_id]
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(escalation, field, value)

    from datetime import datetime

    escalation.updated_at = datetime.utcnow()
    _escalations[escalation_id] = escalation
    return escalation


@router.delete("/{escalation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_escalation(escalation_id: UUID) -> None:
    """Delete an escalation.

    Args:
        escalation_id: The escalation identifier.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )
    del _escalations[escalation_id]


@router.post("/{escalation_id}/route", response_model=PriorityAssessment)
async def route_escalation(
    escalation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> PriorityAssessment:
    """Route an escalation using the priority router agent.

    Args:
        escalation_id: The escalation identifier.
        settings: Application settings.

    Returns:
        PriorityAssessment: The routing assessment.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation = _escalations[escalation_id]
    agent = _get_priority_router(settings)
    result = await agent.run(PriorityRouterInput(escalation=escalation))

    escalation.priority = result.assessed_priority.value
    escalation.status = EscalationStatus.ROUTED
    _escalations[escalation_id] = escalation

    return result


@router.post("/{escalation_id}/analyze", response_model=EscalationAnalysis)
async def analyze_escalation(
    escalation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> EscalationAnalysis:
    """Analyze an escalation using the analyzer agent.

    Args:
        escalation_id: The escalation identifier.
        settings: Application settings.

    Returns:
        EscalationAnalysis: The analysis result.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation = _escalations[escalation_id]
    agent = _get_escalation_analyzer(settings)
    result = await agent.run(
        EscalationAnalyzerInput(
            escalations=[escalation],
            analysis_type="single",
        )
    )
    _analyses[result.id] = result
    return result


@router.post("/{escalation_id}/auto-resolve", response_model=EscalationActionResponse)
async def auto_resolve_escalation(
    escalation_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> EscalationActionResponse:
    """Attempt to auto-resolve an escalation.

    Args:
        escalation_id: The escalation identifier.
        settings: Application settings.

    Returns:
        EscalationActionResponse: Result of auto-resolution attempt.

    Raises:
        HTTPException: If escalation not found.
    """
    if escalation_id not in _escalations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    escalation = _escalations[escalation_id]
    agent = _get_auto_resolver(settings)
    resolution = await agent.run(AutoResolverInput(escalation=escalation))

    if resolution:
        _resolutions[resolution.id] = resolution
        escalation.status = EscalationStatus.RESOLVED
        escalation.resolution_id = resolution.id
        _escalations[escalation_id] = escalation
        return EscalationActionResponse(
            success=True,
            message="Escalation auto-resolved successfully",
            data={"resolution_id": str(resolution.id)},
        )

    return EscalationActionResponse(
        success=False,
        message="Auto-resolution not possible for this escalation",
    )


@router.post(
    "/bulk", response_model=list[Escalation], status_code=status.HTTP_201_CREATED
)
async def bulk_create_escalations(
    data: BulkEscalationCreateRequest,
) -> list[Escalation]:
    """Create multiple escalations in bulk.

    Args:
        data: Bulk creation data.

    Returns:
        list[Escalation]: Created escalations.
    """
    created: list[Escalation] = []
    for item in data.escalations:
        escalation = Escalation(**item.model_dump())
        _escalations[escalation.id] = escalation
        created.append(escalation)
    return created
