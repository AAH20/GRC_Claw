"""Access control endpoints."""

from __future__ import annotations

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tier_management.agents.access_controller import AccessControllerAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import AccessCheckRequest, AccessCheckResponse, AccessPolicy

access_router = APIRouter()

# In-memory store
_policies_store: dict[UUID, AccessPolicy] = {}
_agent_instance: AccessControllerAgent | None = None


async def _get_agent(settings: Settings = Depends(get_settings)) -> AccessControllerAgent:  # noqa: B008
    """Get or create the access controller agent singleton.

    Args:
        settings: Application settings.

    Returns:
        The access controller agent instance.
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AccessControllerAgent()
        await _agent_instance.initialize()
        # Load existing policies
        for policy in _policies_store.values():
            _agent_instance.add_policy(policy)
    return _agent_instance


@access_router.post("/check", response_model=AccessCheckResponse)
async def check_access(
    request: AccessCheckRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
    agent: AccessControllerAgent = Depends(_get_agent),  # noqa: B008
) -> AccessCheckResponse:
    """Check if a member has access to a resource.

    Args:
        request: The access check request.
        settings: Application settings.
        agent: The access controller agent.

    Returns:
        Access check response with decision.
    """
    return await agent.execute(request)


@access_router.post("/policies", response_model=AccessPolicy, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: dict,
    settings: Settings = Depends(get_settings),  # noqa: B008
    agent: AccessControllerAgent = Depends(_get_agent),  # noqa: B008
) -> AccessPolicy:
    """Create a new access policy.

    Args:
        policy_data: Policy creation data.
        settings: Application settings.
        agent: The access controller agent.

    Returns:
        The created policy.
    """
    from datetime import datetime
    from uuid import uuid4

    policy = AccessPolicy(
        id=uuid4(),
        name=policy_data.get("name", "Unnamed Policy"),
        tier_id=UUID(str(policy_data.get("tier_id"))),
        resource=policy_data.get("resource", ""),
        action=policy_data.get("action", "read"),
        effect=policy_data.get("effect", "granted"),
        conditions=policy_data.get("conditions", {}),
        priority=int(policy_data.get("priority", 0)),
        enabled=bool(policy_data.get("enabled", True)),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    _policies_store[policy.id] = policy
    agent.add_policy(policy)
    return policy


@access_router.get("/policies/{policy_id}", response_model=AccessPolicy)
async def get_policy(
    policy_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AccessPolicy:
    """Get a specific access policy.

    Args:
        policy_id: The policy identifier.
        settings: Application settings.

    Returns:
        The requested policy.

    Raises:
        HTTPException: If policy not found.
    """
    policy = _policies_store.get(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_id}' not found",
        )
    return policy


@access_router.get("/policies", response_model=list[AccessPolicy])
async def list_policies(
    tier_id: UUID | None = None,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> list[AccessPolicy]:
    """List access policies with optional filtering.

    Args:
        tier_id: Filter by tier.
        settings: Application settings.

    Returns:
        List of matching policies.
    """
    policies = list(_policies_store.values())
    if tier_id:
        policies = [p for p in policies if p.tier_id == tier_id]
    return policies


@access_router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
    agent: AccessControllerAgent = Depends(_get_agent),  # noqa: B008
) -> None:
    """Delete an access policy.

    Args:
        policy_id: The policy identifier.
        settings: Application settings.
        agent: The access controller agent.

    Raises:
        HTTPException: If policy not found.
    """
    if policy_id not in _policies_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_id}' not found",
        )
    del _policies_store[policy_id]
    agent.remove_policy(policy_id)
