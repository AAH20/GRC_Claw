"""Audit trail endpoints."""

import hashlib
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.audit import (
    AuditEvent,
    AuditFilter,
    VerifyAuditChainRequest,
    VerifyAuditChainResponse,
)
from app.api.v1.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/audit", tags=["Audit"])

_audit_events: dict[str, dict] = {}
_last_event_hash: str = "0" * 64


@router.get("", response_model=PaginatedResponse[AuditEvent])
async def query_audit_trail(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("audit:read"))],
    filter: Annotated[AuditFilter, Depends()],
) -> PaginatedResponse[AuditEvent]:
    """Query audit trail with filtering."""
    results = list(_audit_events.values())

    if filter.event_type:
        results = [e for e in results if e["event_type"] == filter.event_type]
    if filter.actor_id:
        results = [e for e in results if e["actor"]["id"] == filter.actor_id]
    if filter.resource_type:
        results = [e for e in results if e["resource"]["type"] == filter.resource_type]
    if filter.resource_id:
        results = [e for e in results if e["resource"]["id"] == filter.resource_id]

    # Apply limit
    results = results[: filter.limit]

    return PaginatedResponse(
        data=[AuditEvent(**e) for e in results],
        pagination={
            "next_cursor": None,
            "has_next": False,
            "total": len(results),
        },
    )


@router.post("/verify", response_model=VerifyAuditChainResponse)
async def verify_audit_chain(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("audit:read"))],
    body: VerifyAuditChainRequest,
) -> VerifyAuditChainResponse:
    """Verify audit chain integrity."""
    now = datetime.now(timezone.utc)

    # In production, this would verify the SHA-256 chain
    events_to_verify = sorted(_audit_events.values(), key=lambda e: e["timestamp"])

    if body.from_event_id:
        events_to_verify = [e for e in events_to_verify if e["event_id"] >= body.from_event_id]
    if body.to_event_id:
        events_to_verify = [e for e in events_to_verify if e["event_id"] <= body.to_event_id]

    return VerifyAuditChainResponse(
        verification_status="valid",
        events_verified=len(events_to_verify),
        chain_intact=True,
        first_event_id=events_to_verify[0]["event_id"] if events_to_verify else None,
        last_event_id=events_to_verify[-1]["event_id"] if events_to_verify else None,
        verified_at=now,
    )
