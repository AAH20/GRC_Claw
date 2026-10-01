"""Enforcement decision endpoints."""

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.api.v1.schemas.enforcement import (
    BatchDecideRequest,
    BatchDecideResponse,
    DecisionFilter,
    DecideRequest,
    EnforcementDecision,
)
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/enforcement", tags=["Enforcement"])

_decisions: dict[str, dict] = {}


@router.post("/decide", response_model=EnforcementDecision)
async def request_decision(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("enforcement:decide"))],
    body: DecideRequest,
) -> EnforcementDecision:
    """Request a single enforcement decision."""
    decision_id = f"dec-{len(_decisions) + 1:03d}"
    now = datetime.now(timezone.utc)

    # In production, this would evaluate against the policy engine (OPA/Cedar)
    # For demo, we return ALLOW
    verdict = "ALLOW"
    evidence_hash = hashlib.sha256(
        f"{body.agent_id}:{body.action}:{body.resource}".encode()
    ).hexdigest()

    decision = {
        "decision_id": decision_id,
        "verdict": verdict,
        "policy_id": body.policy_ids[0] if body.policy_ids else "pol-001",
        "policy_version": "1.0.0",
        "agent_id": body.agent_id,
        "action": body.action,
        "resource": body.resource,
        "context": body.context or {},
        "evidence_hash": f"sha256:{evidence_hash}",
        "timestamp": now,
        "ttl": 300,
        "signature": f"ecdsa-p256:{hashlib.sha256(decision_id.encode()).hexdigest()[:32]}",
        "matched_rules": ["allow_read_public"],
        "evaluation_time_ms": 2.3,
        "reason": None,
    }

    _decisions[decision_id] = decision
    return EnforcementDecision(**decision)


@router.post("/decide-batch", response_model=BatchDecideResponse)
async def batch_decide(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("enforcement:decide"))],
    body: BatchDecideRequest,
) -> BatchDecideResponse:
    """Request batch enforcement decisions."""
    results = []
    allowed_count = 0
    denied_count = 0
    total_time = 0.0

    for decide_req in body.decisions:
        decision_id = f"dec-{len(_decisions) + 1:03d}"
        now = datetime.now(timezone.utc)

        verdict = "ALLOW"  # Simplified for demo
        eval_time = 2.0

        decision = {
            "decision_id": decision_id,
            "verdict": verdict,
            "policy_id": decide_req.policy_ids[0] if decide_req.policy_ids else "pol-001",
            "policy_version": "1.0.0",
            "agent_id": decide_req.agent_id,
            "action": decide_req.action,
            "resource": decide_req.resource,
            "context": decide_req.context or {},
            "evidence_hash": f"sha256:{hashlib.sha256(decision_id.encode()).hexdigest()}",
            "timestamp": now,
            "ttl": 300,
            "signature": f"ecdsa-p256:{hashlib.sha256(decision_id.encode()).hexdigest()[:32]}",
            "matched_rules": ["allow_read_public"],
            "evaluation_time_ms": eval_time,
            "reason": None,
        }

        _decisions[decision_id] = decision

        results.append({
            "decision_id": decision_id,
            "verdict": verdict,
            "policy_id": decision["policy_id"],
            "evaluation_time_ms": eval_time,
            "reason": None,
        })

        if verdict == "ALLOW":
            allowed_count += 1
        else:
            denied_count += 1
        total_time += eval_time

    avg_time = total_time / len(body.decisions) if body.decisions else 0.0

    return BatchDecideResponse(
        results=results,
        summary={
            "total": len(body.decisions),
            "allowed": allowed_count,
            "denied": denied_count,
            "avg_evaluation_time_ms": avg_time,
        },
    )


@router.get("/decisions/{decision_id}", response_model=EnforcementDecision)
async def get_decision(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    decision_id: str,
) -> EnforcementDecision:
    """Get an enforcement decision by ID."""
    if decision_id not in _decisions:
        raise NotFoundException("Decision", decision_id)
    return EnforcementDecision(**_decisions[decision_id])


@router.get("/decisions", response_model=PaginatedResponse[EnforcementDecision])
async def list_decisions(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    filter: Annotated[DecisionFilter, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[EnforcementDecision]:
    """List enforcement decisions with filtering."""
    results = list(_decisions.values())

    if filter.agent_id:
        results = [d for d in results if d["agent_id"] == filter.agent_id]
    if filter.policy_id:
        results = [d for d in results if d["policy_id"] == filter.policy_id]
    if filter.verdict:
        results = [d for d in results if d["verdict"] == filter.verdict.value]

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
        data=[EnforcementDecision(**d) for d in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )
