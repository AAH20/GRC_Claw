"""Webhook-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(str, Enum):
    """Supported webhook event types."""

    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_STATUS_CHANGED = "policy.status_changed"
    POLICY_DELETED = "policy.deleted"
    POLICY_COMPILED = "policy.compiled"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_DEPRECATED = "policy.deprecated"
    ENFORCEMENT_DECISION_MADE = "enforcement.decision_made"
    ENFORCEMENT_APPROVAL_REQUIRED = "enforcement.approval_required"
    ENFORCEMENT_AGENT_QUARANTINED = "enforcement.agent_quarantined"
    ENFORCEMENT_POLICY_VIOLATION = "enforcement.policy_violation"
    EVIDENCE_COLLECTED = "evidence.collected"
    EVIDENCE_VERIFIED = "evidence.verified"
    EVIDENCE_EXPORTED = "evidence.exported"
    EVIDENCE_EXPIRED = "evidence.expired"
    ASSESSMENT_CREATED = "assessment.created"
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_COMPLETED = "assessment.completed"
    ASSESSMENT_FINDING_ADDED = "assessment.finding_added"
    ASSESSMENT_FINDING_RESOLVED = "assessment.finding_resolved"
    COMPLIANCE_POSTURE_CHANGED = "compliance.posture_changed"
    COMPLIANCE_CONTROL_SATISFIED = "compliance.control_satisfied"
    COMPLIANCE_CONTROL_VIOLATED = "compliance.control_violated"
    COMPLIANCE_REPORT_GENERATED = "compliance.report_generated"
    COMPLIANCE_MAPPING_CREATED = "compliance.mapping_created"
    AGENT_REGISTERED = "agent.registered"
    AGENT_UPDATED = "agent.updated"
    AGENT_LIFECYCLE_CHANGED = "agent.lifecycle_changed"
    AGENT_TRUST_SCORE_CHANGED = "agent.trust_score_changed"
    AGENT_SUSPENDED = "agent.suspended"
    AGENT_TERMINATED = "agent.terminated"
    AUDIT_EVENT_CREATED = "audit.event_created"
    AUDIT_CHAIN_VERIFIED = "audit.chain_verified"


class WebhookSubscriptionCreate(BaseModel):
    """Create webhook subscription request."""

    url: str = Field(..., pattern=r"^https://")
    events: list[WebhookEvent]
    secret: str = Field(..., min_length=16)
    description: str | None = None
    active: bool = True
    metadata: dict[str, Any] | None = None


class WebhookSubscriptionUpdate(BaseModel):
    """Update webhook subscription request."""

    url: str | None = None
    events: list[WebhookEvent] | None = None
    secret: str | None = None
    description: str | None = None
    active: bool | None = None
    metadata: dict[str, Any] | None = None


class WebhookSubscription(BaseModel):
    """Webhook subscription response."""

    subscription_id: str
    url: str
    events: list[str]
    secret: str
    description: str | None = None
    active: bool
    metadata: dict[str, Any] | None = None
    created_at: datetime
    delivery_stats: dict[str, Any] | None = None


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""

    delivery_id: str
    subscription_id: str
    event_id: str
    event_type: str
    status: str
    http_status: int | None = None
    response_time_ms: float | None = None
    attempts: int = 1
    delivered_at: datetime | None = None
    next_retry_at: datetime | None = None


class WebhookPayload(BaseModel):
    """Webhook delivery payload envelope."""

    webhook_id: str
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    data: dict[str, Any]
    metadata: dict[str, Any] | None = None


class TestWebhookResponse(BaseModel):
    """Test webhook response."""

    subscription_id: str
    test_event_id: str
    delivery_status: str
    http_status: int | None = None
    response_time_ms: float | None = None
    delivered_at: datetime | None = None
