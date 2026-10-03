"""Policy API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from compliance_monitor.api.dependencies import get_policy_tracker
from compliance_monitor.api.store import store
from compliance_monitor.models.schemas import Policy, PolicyCreate
from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from uuid import UUID

    from compliance_monitor.agents import PolicyTrackerAgent

router = APIRouter()


@router.get("", response_model=list[Policy])
async def list_policies() -> list[Policy]:
    """List all compliance policies.

    Returns:
        List of all policies.
    """
    return store.list_policies()


@router.post("", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreate,
    agent: PolicyTrackerAgent = Depends(get_policy_tracker),  # noqa: B008,
) -> Policy:
    """Create a new compliance policy.

    Args:
        data: Policy creation data.
        agent: Policy tracker agent.

    Returns:
        Created policy.
    """
    policy = await agent.run(data)
    return store.create_policy(policy)


@router.get("/{policy_id}", response_model=Policy)
async def get_policy(policy_id: UUID) -> Policy:
    """Get a policy by ID.

    Args:
        policy_id: Policy identifier.

    Returns:
        Policy details.

    Raises:
        HTTPException: If policy not found.
    """
    policy = store.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: UUID) -> None:
    """Delete a policy.

    Args:
        policy_id: Policy identifier.

    Raises:
        HTTPException: If policy not found.
    """
    if not store.delete_policy(policy_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
