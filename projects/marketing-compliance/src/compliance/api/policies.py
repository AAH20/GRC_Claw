"""Policy management API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


class Severity(StrEnum):
    """Policy severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyCreate(BaseModel):
    """Payload for creating a compliance policy."""

    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=2048)
    severity: Severity = Severity.MEDIUM
    enabled: bool = True
    rules: list[str] = Field(default_factory=list)


class Policy(PolicyCreate):
    """A persisted compliance policy."""

    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# In-memory store. Replace with a persistent repository in production.
_POLICIES: dict[str, Policy] = {}


@router.get("", response_model=list[Policy])
async def list_policies(enabled: bool | None = None) -> list[Policy]:
    """List compliance policies.

    Args:
        enabled: Optional filter on the enabled flag.

    Returns:
        The list of matching policies.
    """
    policies = list(_POLICIES.values())
    if enabled is not None:
        policies = [p for p in policies if p.enabled is enabled]
    return policies


@router.post("", response_model=Policy, status_code=status.HTTP_201_CREATED)
async def create_policy(payload: PolicyCreate) -> Policy:
    """Create a new compliance policy.

    Args:
        payload: The policy definition.

    Returns:
        The created policy.

    Raises:
        HTTPException: 409 if a policy with the same name already exists.
    """
    if any(p.name == payload.name for p in _POLICIES.values()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"policy '{payload.name}' already exists",
        )
    policy_id = f"pol_{len(_POLICIES) + 1:04d}"
    policy = Policy(id=policy_id, **payload.model_dump())
    _POLICIES[policy_id] = policy
    return policy


@router.get("/{policy_id}", response_model=Policy)
async def get_policy(policy_id: str) -> Policy:
    """Fetch a single policy by id.

    Args:
        policy_id: The policy identifier.

    Returns:
        The matching policy.

    Raises:
        HTTPException: 404 if the policy does not exist.
    """
    policy = _POLICIES.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy not found")
    return policy


@router.put("/{policy_id}", response_model=Policy)
async def update_policy(policy_id: str, payload: PolicyCreate) -> Policy:
    """Replace an existing policy.

    Args:
        policy_id: The policy identifier.
        payload: The new policy definition.

    Returns:
        The updated policy.

    Raises:
        HTTPException: 404 if the policy does not exist.
    """
    if policy_id not in _POLICIES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy not found")
    updated = Policy(
        id=policy_id,
        updated_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    _POLICIES[policy_id] = updated
    return updated


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: str) -> None:
    """Delete a policy.

    Args:
        policy_id: The policy identifier.

    Raises:
        HTTPException: 404 if the policy does not exist.
    """
    if policy_id not in _POLICIES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy not found")
    del _POLICIES[policy_id]


def reset_store() -> None:
    """Clear the in-memory policy store (used by tests)."""
    _POLICIES.clear()


def seed_policies(entries: list[dict[str, Any]]) -> None:
    """Seed the in-memory store with policies.

    Args:
        entries: Raw policy definitions.
    """
    for entry in entries:
        policy_id = entry.get("id") or f"pol_{len(_POLICIES) + 1:04d}"
        _POLICIES[policy_id] = Policy(id=policy_id, **entry)
