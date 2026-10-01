"""Audit trail-related schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Actor(BaseModel):
    """Audit event actor."""

    type: str
    id: str
    name: str | None = None


class AuditResource(BaseModel):
    """Audit event resource."""

    type: str
    id: str
    name: str | None = None


class AuditEvent(BaseModel):
    """Audit trail event."""

    event_id: str
    event_type: str
    actor: Actor
    resource: AuditResource
    timestamp: datetime
    details: dict[str, Any] | None = None
    integrity_hash: str | None = None
    previous_event_hash: str | None = None


class AuditFilter(BaseModel):
    """Audit trail filter parameters."""

    event_type: str | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class VerifyAuditChainRequest(BaseModel):
    """Verify audit chain request."""

    from_event_id: str | None = None
    to_event_id: str | None = None


class VerifyAuditChainResponse(BaseModel):
    """Verify audit chain response."""

    verification_status: str
    events_verified: int
    chain_intact: bool
    first_event_id: str | None = None
    last_event_id: str | None = None
    verified_at: datetime
