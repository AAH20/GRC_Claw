"""Agent registry endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.agent import (
    AgentCreate,
    AgentFilter,
    AgentResponse,
    AgentUpdate,
    BindPolicyRequest,
    UpdateTrustScoreRequest,
)
from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.core.exceptions import ConflictException, NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/agents", tags=["Agents"])

_agents: dict[str, dict] = {}


@router.get("", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[AgentFilter, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[AgentResponse]:
    """List agents with filtering and pagination."""
    results = list(_agents.values())

    if filter.type:
        results = [a for a in results if a["type"] == filter.type.value]
    if filter.framework:
        results = [a for a in results if a["framework"] == filter.framework.value]
    if filter.lifecycle_stage:
        results = [a for a in results if a["lifecycle_stage"] == filter.lifecycle_stage.value]
    if filter.risk_tier:
        results = [a for a in results if a["risk_tier"] == filter.risk_tier.value]
    if filter.trust_score_min is not None:
        results = [a for a in results if a.get("trust_score", {}).get("value", 0) >= filter.trust_score_min]

    total = len(results)
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
        data=[AgentResponse(**a) for a in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("agents:write"))],
    body: AgentCreate,
) -> AgentResponse:
    """Register a new agent."""
    # Check for duplicate
    for agent in _agents.values():
        if agent["name"] == body.name:
            raise ConflictException(
                f"Agent with name '{body.name}' already registered.",
                code="AGENT_ALREADY_REGISTERED",
            )

    agent_id = f"agent-{len(_agents) + 1}"
    now = datetime.now(timezone.utc)

    agent = {
        "id": agent_id,
        "name": body.name,
        "type": body.type.value,
        "framework": body.framework.value,
        "owner": body.owner,
        "lifecycle_stage": "proposed",
        "risk_tier": body.risk_tier.value,
        "capabilities": [cap.model_dump() for cap in body.capabilities],
        "identity": None,
        "trust_score": None,
        "policy_bindings": [],
        "created_at": now,
        "updated_at": now,
    }

    _agents[agent_id] = agent
    return AgentResponse(**agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    agent_id: str,
) -> AgentResponse:
    """Get an agent by ID."""
    if agent_id not in _agents:
        raise NotFoundException("Agent", agent_id)
    return AgentResponse(**_agents[agent_id])


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("agents:write"))],
    agent_id: str,
    body: AgentUpdate,
) -> AgentResponse:
    """Update an agent."""
    if agent_id not in _agents:
        raise NotFoundException("Agent", agent_id)

    agent = _agents[agent_id]
    now = datetime.now(timezone.utc)

    if body.name:
        agent["name"] = body.name
    if body.lifecycle_stage:
        agent["lifecycle_stage"] = body.lifecycle_stage.value
    if body.risk_tier:
        agent["risk_tier"] = body.risk_tier.value
    if body.capabilities:
        agent["capabilities"] = [cap.model_dump() for cap in body.capabilities]

    agent["updated_at"] = now
    return AgentResponse(**agent)


@router.post("/{agent_id}/trust-score", response_model=AgentResponse)
async def update_trust_score(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("agents:write"))],
    agent_id: str,
    body: UpdateTrustScoreRequest,
) -> AgentResponse:
    """Update agent trust score."""
    if agent_id not in _agents:
        raise NotFoundException("Agent", agent_id)

    agent = _agents[agent_id]
    now = datetime.now(timezone.utc)

    agent["trust_score"] = {
        "value": body.value,
        "grade": body.grade,
        "last_evaluated": now,
    }
    agent["updated_at"] = now

    return AgentResponse(**agent)


@router.post("/{agent_id}/policy-bindings", response_model=AgentResponse)
async def bind_policies(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("agents:write"))],
    agent_id: str,
    body: BindPolicyRequest,
) -> AgentResponse:
    """Bind policies to an agent."""
    if agent_id not in _agents:
        raise NotFoundException("Agent", agent_id)

    agent = _agents[agent_id]
    now = datetime.now(timezone.utc)

    for policy_id in body.policy_ids:
        if policy_id not in agent["policy_bindings"]:
            agent["policy_bindings"].append(policy_id)

    agent["updated_at"] = now
    return AgentResponse(**agent)
