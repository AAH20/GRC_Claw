"""Policy management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from content_moderation.models.schemas import Policy

router = APIRouter()

# In-memory policy store (replace with database in production)
_policies: dict[UUID, Policy] = {}


@router.get("/policies", response_model=list[Policy])
async def list_policies() -> list[Policy]:
    """List all content moderation policies.

    Returns:
        List of all policies.
    """
    return list(_policies.values())


@router.post("/policies", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(policy: Policy) -> Policy:
    """Create a new content moderation policy.

    Args:
        policy: Policy to create.

    Returns:
        Created policy.
    """
    _policies[policy.id] = policy
    return policy


@router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(policy_id: UUID) -> Policy:
    """Get a specific policy by ID.

    Args:
        policy_id: Policy identifier.

    Returns:
        Requested policy.

    Raises:
        HTTPException: If policy not found.
    """
    policy = _policies.get(policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found",
        )
    return policy


@router.put("/policies/{policy_id}", response_model=Policy)
async def update_policy(policy_id: UUID, policy: Policy) -> Policy:
    """Update an existing policy.

    Args:
        policy_id: Policy identifier.
        policy: Updated policy data.

    Returns:
        Updated policy.

    Raises:
        HTTPException: If policy not found.
    """
    if policy_id not in _policies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found",
        )
    policy.id = policy_id
    _policies[policy_id] = policy
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: UUID) -> None:
    """Delete a policy.

    Args:
        policy_id: Policy identifier.

    Raises:
        HTTPException: If policy not found.
    """
    if policy_id not in _policies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found",
        )
    del _policies[policy_id]
