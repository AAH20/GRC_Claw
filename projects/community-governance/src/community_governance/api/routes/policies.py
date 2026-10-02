"""Policy management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from community_governance.api.dependencies import get_policy_manager
from community_governance.agents import PolicyManagerAgent
from community_governance.config.logging_config import get_logger
from community_governance.models.policy import Policy, PolicyCreate, PolicyStatus, PolicyUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/policies", tags=["policies"])

# In-memory storage for demo purposes
_policies_store: dict[UUID, Policy] = {}


@router.post("", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    agent: PolicyManagerAgent = Depends(get_policy_manager),
) -> Policy:
    """Create a new governance policy.

    Args:
        policy_data: The policy creation data.
        agent: The policy manager agent.

    Returns:
        The newly created policy.
    """
    policy = await agent.execute({"operation": "create", "policy_data": policy_data.model_dump()})
    _policies_store[policy.id] = policy
    logger.info(f"Policy created: {policy.name}", policy_id=str(policy.id))
    return policy


@router.get("", response_model=list[Policy])
async def list_policies(
    status_filter: PolicyStatus | None = Query(default=None, alias="status", description="Filter by status"),
    scope: str | None = Query(default=None, description="Filter by scope"),
    agent: PolicyManagerAgent = Depends(get_policy_manager),
) -> list[Policy]:
    """List all governance policies.

    Args:
        status_filter: Optional status filter.
        scope: Optional scope filter.
        agent: The policy manager agent.

    Returns:
        List of policies.
    """
    policies = list(_policies_store.values())
    if status_filter:
        policies = [p for p in policies if p.status == status_filter]
    if scope:
        policies = [p for p in policies if p.scope.value == scope]
    return policies


@router.get("/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: UUID,
    agent: PolicyManagerAgent = Depends(get_policy_manager),
) -> Policy:
    """Get a specific policy by ID.

    Args:
        policy_id: The policy ID.
        agent: The policy manager agent.

    Returns:
        The requested policy.

    Raises:
        HTTPException: If the policy is not found.
    """
    policy = _policies_store.get(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found",
        )
    return policy


@router.put("/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: UUID,
    policy_data: PolicyUpdate,
    agent: PolicyManagerAgent = Depends(get_policy_manager),
) -> Policy:
    """Update an existing policy.

    Args:
        policy_id: The policy ID.
        policy_data: The policy update data.
        agent: The policy manager agent.

    Returns:
        The updated policy.

    Raises:
        HTTPException: If the policy is not found.
    """
    try:
        policy = await agent.execute(
            {
                "operation": "update",
                "policy_id": policy_id,
                "policy_data": policy_data.model_dump(exclude_unset=True),
            }
        )
        _policies_store[policy.id] = policy
        logger.info(f"Policy updated: {policy.name}", policy_id=str(policy.id))
        return policy
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update policy: {str(e)}",
        )


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    agent: PolicyManagerAgent = Depends(get_policy_manager),
) -> None:
    """Delete a policy.

    Args:
        policy_id: The policy ID.
        agent: The policy manager agent.

    Raises:
        HTTPException: If the policy is not found.
    """
    try:
        agent.remove_policy(policy_id)
        _policies_store.pop(policy_id, None)
        logger.info(f"Policy deleted: {policy_id}", policy_id=str(policy_id))
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise
