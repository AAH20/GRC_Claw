"""Compliance check endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.agents import ComplianceCheckerAgent
from onboarding_automator.config.settings import Settings, get_settings
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import (
    AgentResponse,
    ComplianceCheck,
    ComplianceCheckCreate,
    ComplianceCheckUpdate,
)

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


@router.post("", response_model=ComplianceCheck, status_code=status.HTTP_201_CREATED)
async def create_compliance_check(
    check_data: ComplianceCheckCreate,
    store: InMemoryStore = Depends(get_store),
) -> ComplianceCheck:
    """Create a new compliance check record.

    Args:
        check_data: The compliance check creation data.

    Returns:
        The newly created compliance check.
    """
    check = ComplianceCheck(
        plan_id=check_data.plan_id,
        name=check_data.name,
        description=check_data.description,
        category=check_data.category,
        severity=check_data.severity,
    )
    await store.save_compliance_check(check)

    # Add check to parent plan
    plan = await store.get_plan(check_data.plan_id)
    if plan:
        plan.compliance_checks.append(check.id)
        await store.save_plan(plan)

    return check


@router.get("", response_model=list[ComplianceCheck])
async def list_compliance_checks(
    store: InMemoryStore = Depends(get_store),
    plan_id: UUID | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ComplianceCheck]:
    """List compliance checks with optional filtering.

    Args:
        plan_id: Filter by parent plan ID.
        status_filter: Filter by check status.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of matching compliance checks.
    """
    checks = await store.list_compliance_checks(plan_id=plan_id)
    if status_filter:
        checks = [c for c in checks if c.status.value == status_filter]
    return checks[skip : skip + limit]


@router.get("/{check_id}", response_model=ComplianceCheck)
async def get_compliance_check(
    check_id: UUID,
    store: InMemoryStore = Depends(get_store),
) -> ComplianceCheck:
    """Get a specific compliance check by ID.

    Args:
        check_id: The check's unique identifier.

    Returns:
        The requested compliance check.

    Raises:
        HTTPException: If the check is not found.
    """
    check = await store.get_compliance_check(check_id)
    if check is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance check {check_id} not found",
        )
    return check


@router.patch("/{check_id}", response_model=ComplianceCheck)
async def update_compliance_check(
    check_id: UUID,
    update_data: ComplianceCheckUpdate,
    store: InMemoryStore = Depends(get_store),
) -> ComplianceCheck:
    """Update a compliance check.

    Args:
        check_id: The check's unique identifier.
        update_data: The fields to update.

    Returns:
        The updated compliance check.

    Raises:
        HTTPException: If the check is not found.
    """
    check = await store.get_compliance_check(check_id)
    if check is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance check {check_id} not found",
        )

    if update_data.status is not None:
        check.status = update_data.status
    if update_data.details is not None:
        check.details = update_data.details
    if update_data.remediation_steps is not None:
        check.remediation_steps = update_data.remediation_steps
    if update_data.severity is not None:
        check.severity = update_data.severity

    from datetime import datetime

    check.updated_at = datetime.utcnow()
    await store.save_compliance_check(check)
    return check


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compliance_check(
    check_id: UUID,
    store: InMemoryStore = Depends(get_store),
) -> None:
    """Delete a compliance check.

    Args:
        check_id: The check's unique identifier.

    Raises:
        HTTPException: If the check is not found.
    """
    deleted = await store.delete_compliance_check(check_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance check {check_id} not found",
        )


@router.post("/{plan_id}/run-all", response_model=AgentResponse)
async def run_all_compliance_checks(
    plan_id: UUID,
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> AgentResponse:
    """Run all applicable compliance checks for a plan.

    Args:
        plan_id: The plan's unique identifier.
        request: The incoming request.

    Returns:
        AgentResponse with all check results.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {plan_id} not found",
        )

    documents = await store.list_documents(plan_id=plan_id)
    agent = ComplianceCheckerAgent(request.app.state.settings)
    return await agent.run_all_checks(plan, documents)
