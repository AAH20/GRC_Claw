"""SLA tracking API endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from escalation_workflow.agents.sla_tracker import SLATrackerAgent, SLATrackerInput
from escalation_workflow.config import Settings, get_settings
from escalation_workflow.models.sla import SLA, SLABreach, SLAStatus
from fastapi import APIRouter, Depends, HTTPException, Query, status

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/sla", tags=["sla"])

_slas: dict[UUID, SLA] = {}


@router.post("/track", response_model=SLA, status_code=status.HTTP_201_CREATED)
async def track_sla(
    escalation_id: UUID,
    priority: str = "medium",
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SLA:
    """Start tracking SLA for an escalation.

    Args:
        escalation_id: The escalation identifier.
        priority: The priority level.
        settings: Application settings.

    Returns:
        SLA: The created SLA tracking record.
    """
    now = datetime.utcnow()

    priority_sla_map = {
        "critical": settings.critical_sla_minutes,
        "high": settings.high_sla_minutes,
        "medium": settings.medium_sla_minutes,
        "low": settings.low_sla_minutes,
    }

    sla_minutes = priority_sla_map.get(priority, settings.default_sla_minutes)

    sla = SLA(
        escalation_id=escalation_id,
        priority=priority,
        response_time_minutes=sla_minutes,
        resolution_time_minutes=sla_minutes * 4,
        response_deadline=now + timedelta(minutes=sla_minutes),
        resolution_deadline=now + timedelta(minutes=sla_minutes * 4),
        remaining_minutes=sla_minutes * 4,
    )

    _slas[sla.id] = sla
    return sla


@router.get("", response_model=list[SLA])
async def list_slas(
    status_filter: SLAStatus | None = Query(default=None, alias="status"),  # noqa: B008
) -> list[SLA]:
    """List SLA tracking records.

    Args:
        status_filter: Filter by SLA status.

    Returns:
        list[SLA]: List of SLA records.
    """
    items = list(_slas.values())
    if status_filter:
        items = [s for s in items if s.status == status_filter]
    return items


@router.get("/{sla_id}", response_model=SLA)
async def get_sla(sla_id: UUID) -> SLA:
    """Get a specific SLA record.

    Args:
        sla_id: The SLA identifier.

    Returns:
        SLA: The SLA record.

    Raises:
        HTTPException: If SLA not found.
    """
    if sla_id not in _slas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SLA {sla_id} not found",
        )
    return _slas[sla_id]


@router.post("/{sla_id}/check", response_model=SLA)
async def check_sla_status(
    sla_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SLA:
    """Check and update SLA status.

    Args:
        sla_id: The SLA identifier.
        settings: Application settings.

    Returns:
        SLA: Updated SLA record.

    Raises:
        HTTPException: If SLA not found.
    """
    if sla_id not in _slas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SLA {sla_id} not found",
        )

    sla = _slas[sla_id]
    agent = SLATrackerAgent()

    result = await agent.run(
        SLATrackerInput(
            escalation_id=str(sla.escalation_id),
            priority=sla.priority,
            started_at=sla.started_at,
            response_deadline=sla.response_deadline,
            resolution_deadline=sla.resolution_deadline,
        )
    )

    sla.status = result.status
    sla.remaining_minutes = result.remaining_minutes
    sla.elapsed_minutes = result.elapsed_minutes
    _slas[sla_id] = sla

    return sla


@router.post("/{sla_id}/breach", response_model=SLABreach)
async def record_breach(sla_id: UUID) -> SLABreach:
    """Record an SLA breach.

    Args:
        sla_id: The SLA identifier.

    Returns:
        SLABreach: The recorded breach.

    Raises:
        HTTPException: If SLA not found.
    """
    if sla_id not in _slas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SLA {sla_id} not found",
        )

    sla = _slas[sla_id]
    agent = SLATrackerAgent()
    breach = agent.calculate_breach(sla)

    sla.breaches.append(breach)
    sla.breach_count += 1
    sla.status = SLAStatus.BREACHED
    _slas[sla_id] = sla

    return breach


@router.get("/escalation/{escalation_id}", response_model=list[SLA])
async def get_slas_for_escalation(escalation_id: UUID) -> list[SLA]:
    """Get all SLA records for an escalation.

    Args:
        escalation_id: The escalation identifier.

    Returns:
        list[SLA]: SLA records for the escalation.
    """
    return [s for s in _slas.values() if s.escalation_id == escalation_id]
