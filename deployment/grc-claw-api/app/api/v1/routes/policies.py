"""Policy management endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.api.v1.schemas.policy import (
    CompilePolicyResponse,
    DryRunRequest,
    DryRunResponse,
    PolicyCreate,
    PolicyDependencyResponse,
    PolicyFilter,
    PolicyResponse,
    PolicyUpdate,
    PolicyVersion,
)
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/policies", tags=["Policies"])

# In-memory store for demo (replace with database in production)
_policies: dict[str, dict] = {}


@router.get("", response_model=PaginatedResponse[PolicyResponse])
async def list_policies(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[PolicyFilter, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[PolicyResponse]:
    """List policies with filtering and pagination."""
    results = list(_policies.values())

    # Apply filters
    if filter.status:
        results = [p for p in results if p["status"] == filter.status.value]
    if filter.category:
        results = [p for p in results if p["category"] == filter.category.value]
    if filter.framework:
        results = [p for p in results if filter.framework in p.get("framework_tags", [])]
    if filter.agent_id:
        results = [p for p in results if filter.agent_id in p.get("agent_bindings", [])]

    total = len(results)

    # Apply pagination
    start = 0
    if pagination.cursor:
        try:
            start = int(pagination.cursor)
        except ValueError:
            start = 0

    end = start + pagination.limit
    page = results[start:end]

    next_cursor = str(end) if end < total else None

    return PaginatedResponse(
        data=[PolicyResponse(**p) for p in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("policies:write"))],
    body: PolicyCreate,
) -> PolicyResponse:
    """Create a new policy."""
    policy_id = f"pol-{len(_policies) + 1:03d}"
    now = datetime.now(timezone.utc)

    policy = {
        "id": policy_id,
        "policy_key": body.policy_key,
        "name": body.name,
        "description": body.description,
        "category": body.category.value,
        "status": "draft",
        "version": "1.0.0",
        "framework_tags": body.framework_tags,
        "effective_date": None,
        "expiry_date": None,
        "owner_id": auth.subject,
        "agent_bindings": [],
        "cedar_policy": body.cedar_policy,
        "rego_policy": None,
        "metadata": body.metadata or {},
        "created_at": now,
        "updated_at": now,
        "created_by": auth.subject,
        "updated_by": auth.subject,
    }

    _policies[policy_id] = policy
    return PolicyResponse(**policy)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    policy_id: str,
) -> PolicyResponse:
    """Get a policy by ID."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)
    return PolicyResponse(**_policies[policy_id])


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("policies:write"))],
    policy_id: str,
    body: PolicyUpdate,
) -> PolicyResponse:
    """Update a policy (creates new version)."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    policy = _policies[policy_id]
    now = datetime.now(timezone.utc)

    if body.name:
        policy["name"] = body.name
    if body.description:
        policy["description"] = body.description
    if body.cedar_policy:
        policy["cedar_policy"] = body.cedar_policy
    if body.metadata:
        policy["metadata"] = body.metadata

    # Increment version
    version_parts = policy["version"].split(".")
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    policy["version"] = ".".join(version_parts)
    policy["updated_at"] = now
    policy["updated_by"] = auth.subject

    return PolicyResponse(**policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("policies:write"))],
    policy_id: str,
    force: bool = False,
) -> None:
    """Delete a policy."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    policy = _policies[policy_id]
    if policy["status"] == "active" and not force:
        from app.core.exceptions import ConflictException
        raise ConflictException(
            "Cannot delete active policy. Use force=true to override.",
            code="POLICY_ACTIVE",
        )

    policy["status"] = "archived"
    policy["updated_at"] = datetime.now(timezone.utc)
    policy["updated_by"] = auth.subject


@router.post("/{policy_id}/compile", response_model=CompilePolicyResponse)
async def compile_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("policies:write"))],
    policy_id: str,
) -> CompilePolicyResponse:
    """Compile Cedar policy to Rego."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    policy = _policies[policy_id]
    now = datetime.now(timezone.utc)

    # In production, this would invoke the Cedar-to-Rego compiler
    rego_policy = f"""package grc.agent.{policy_id}

import future.keywords.if
import future.keywords.in

default allow := false

allow if {{
    # Compiled from Cedar policy
    # Source: {policy.get("cedar_policy", "")[:100]}
}}
"""
    policy["rego_policy"] = rego_policy
    policy["updated_at"] = now

    return CompilePolicyResponse(
        policy_id=policy_id,
        compilation_status="success",
        rego_policy=rego_policy,
        warnings=[],
        errors=[],
        compiled_at=now,
    )


@router.post("/{policy_id}/dry-run", response_model=DryRunResponse)
async def dry_run_policy(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    policy_id: str,
    body: DryRunRequest,
) -> DryRunResponse:
    """Dry-run policy against test inputs."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    results = []
    allowed_count = 0
    denied_count = 0
    total_time = 0.0

    for i, test_input in enumerate(body.test_inputs):
        # In production, this would evaluate against the compiled Rego policy
        decision = "ALLOW"  # Simplified for demo
        eval_time = 2.0

        results.append({
            "input_index": i,
            "decision": decision,
            "matched_rules": ["allow_read_public"],
            "evaluation_time_ms": eval_time,
            "reason": None,
        })

        if decision == "ALLOW":
            allowed_count += 1
        else:
            denied_count += 1
        total_time += eval_time

    avg_time = total_time / len(body.test_inputs) if body.test_inputs else 0.0

    return DryRunResponse(
        policy_id=policy_id,
        dry_run_results=results,
        summary={
            "total": len(body.test_inputs),
            "allowed": allowed_count,
            "denied": denied_count,
            "avg_evaluation_time_ms": avg_time,
        },
    )


@router.get("/{policy_id}/versions", response_model=list[PolicyVersion])
async def get_policy_versions(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    policy_id: str,
) -> list[PolicyVersion]:
    """Get policy version history."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    policy = _policies[policy_id]
    # In production, this would query the version history table
    return [
        PolicyVersion(
            version=policy["version"],
            status=policy["status"],
            change_summary="Current version",
            created_at=policy["updated_at"],
            created_by=policy["updated_by"],
        ),
        PolicyVersion(
            version="1.0.0",
            status="superseded",
            change_summary="Initial policy creation",
            created_at=policy["created_at"],
            created_by=policy["created_by"],
        ),
    ]


@router.get("/{policy_id}/dependencies", response_model=PolicyDependencyResponse)
async def get_policy_dependencies(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    policy_id: str,
) -> PolicyDependencyResponse:
    """Get policy dependency graph."""
    if policy_id not in _policies:
        raise NotFoundException("Policy", policy_id)

    return PolicyDependencyResponse(
        policy_id=policy_id,
        dependencies=[],
        dependents=[],
    )
