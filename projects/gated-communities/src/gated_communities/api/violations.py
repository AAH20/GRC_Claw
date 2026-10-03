"""Violation API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from compliance_monitor.api.dependencies import get_violation_detector
from compliance_monitor.api.store import store
from compliance_monitor.models.schemas import Violation, ViolationCreate
from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from uuid import UUID

    from compliance_monitor.agents import ViolationDetectorAgent

router = APIRouter()


@router.get("", response_model=list[Violation])
async def list_violations() -> list[Violation]:
    """List all compliance violations.

    Returns:
        List of all violations.
    """
    return store.list_violations()


@router.post("", response_model=Violation, status_code=status.HTTP_201_CREATED)
async def report_violation(
    data: ViolationCreate,
    agent: ViolationDetectorAgent = Depends(get_violation_detector),  # noqa: B008,
) -> Violation:
    """Report a new compliance violation.

    Args:
        data: Violation creation data.
        agent: Violation detector agent.

    Returns:
        Created violation.
    """
    violation = await agent.run(data)
    return store.create_violation(violation)


@router.get("/{violation_id}", response_model=Violation)
async def get_violation(violation_id: UUID) -> Violation:
    """Get a violation by ID.

    Args:
        violation_id: Violation identifier.

    Returns:
        Violation details.

    Raises:
        HTTPException: If violation not found.
    """
    violation = store.get_violation(violation_id)
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found"
        )
    return violation
