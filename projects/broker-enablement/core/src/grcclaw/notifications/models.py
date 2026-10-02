"""
Data models for the GRC_Claw notification and alerting framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


# ─── Enums ───────────────────────────────────────────────────────────────────

class NotificationType(str, Enum):
    """Types of notifications the system can send."""

    COMPLIANCE_VIOLATION = "compliance_violation"
    POLICY_BREACH = "policy_breach"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    AUDIT_FINDING = "audit_finding"
    INCIDENT_TRIGGERED = "incident_triggered"
    CERTIFICATE_EXPIRING = "certificate_expiring"
    CONTROL_FAILURE = "control_failure"
    EVIDENCE_OVERDUE = "evidence_overdue"
    FRAMEWORK_DEADLINE = "framework_deadline"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_REPORT = "weekly_report"
    SYSTEM_HEALTH = "system_health"
    CUSTOM = "custom"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NotificationStatus(str, Enum):
    """Delivery status of a notification."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    SUPPRESSED = "suppressed"
    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Lifecycle status of an alert."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
    SUPPRESSED = "suppressed"


# ─── Core Models ─────────────────────────────────────────────────────────────

@dataclass
class Notification:
    """A single notification to be delivered through one or more channels."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.CUSTOM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    status: NotificationStatus = NotificationStatus.PENDING
    title: str = ""
    body: str = ""
    summary: str = ""
    source: str = ""
    source_id: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    channels: list[str] = field(default_factory=list)
    recipients: list[str] = field(default_factory=list)
    template_id: Optional[str] = None
    template_data: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scheduled_at: Optional[str] = None
    delivered_at: Optional[str] = None
    expires_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    delivery_results: list[DeliveryResult] = field(default_factory=list)
    correlation_id: Optional[str] = None
    parent_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "body": self.body,
            "summary": self.summary,
            "source": self.source,
            "source_id": self.source_id,
            "tags": self.tags,
            "metadata": self.metadata,
            "channels": self.channels,
            "recipients": self.recipients,
            "template_id": self.template_id,
            "template_data": self.template_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scheduled_at": self.scheduled_at,
            "delivered_at": self.delivered_at,
            "expires_at": self.expires_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "correlation_id": self.correlation_id,
            "parent_id": self.parent_id,
        }


@dataclass
class Alert:
    """An alert representing a detected issue requiring attention."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    status: AlertStatus = AlertStatus.OPEN
    title: str = ""
    description: str = ""
    source: str = ""
    source_type: str = ""
    entity_id: str = ""
    entity_type: str = ""
    framework: str = ""
    control_id: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    assigned_to: Optional[str] = None
    escalated_to: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    notification_ids: list[str] = field(default_factory=list)
    runbook_url: Optional[str] = None
    related_alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "source_type": self.source_type,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "framework": self.framework,
            "control_id": self.control_id,
            "evidence": self.evidence,
            "context": self.context,
            "assigned_to": self.assigned_to,
            "escalated_to": self.escalated_to,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "closed_at": self.closed_at,
            "notification_ids": self.notification_ids,
            "runbook_url": self.runbook_url,
            "related_alerts": self.related_alerts,
        }


@dataclass
class AlertRule:
    """A rule that defines conditions for triggering alerts."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    enabled: bool = True
    severity: AlertSeverity = AlertSeverity.MEDIUM
    notification_type: NotificationType = NotificationType.CUSTOM
    conditions: dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.0
    comparison: str = "gte"  # gte, lte, eq, gt, lt
    window_minutes: int = 60
    cooldown_minutes: int = 30
    auto_escalate: bool = False
    escalation_delay_minutes: int = 60
    escalation_severity: AlertSeverity = AlertSeverity.CRITICAL
    channels: list[str] = field(default_factory=list)
    recipients: list[str] = field(default_factory=list)
    template_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    framework: str = ""
    control_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "severity": self.severity.value,
            "notification_type": self.notification_type.value,
            "conditions": self.conditions,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "window_minutes": self.window_minutes,
            "cooldown_minutes": self.cooldown_minutes,
            "auto_escalate": self.auto_escalate,
            "escalation_delay_minutes": self.escalation_delay_minutes,
            "escalation_severity": self.escalation_severity.value,
            "channels": self.channels,
            "recipients": self.recipients,
            "template_id": self.template_id,
            "tags": self.tags,
            "framework": self.framework,
            "control_id": self.control_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_triggered_at": self.last_triggered_at,
            "trigger_count": self.trigger_count,
        }


@dataclass
class DeliveryResult:
    """Result of delivering a notification through a specific channel."""

    channel: str = ""
    success: bool = False
    status: NotificationStatus = NotificationStatus.PENDING
    recipient: str = ""
    message_id: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "success": self.success,
            "status": self.status.value,
            "recipient": self.recipient,
            "message_id": self.message_id,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class TemplateVariable:
    """A variable definition for notification templates."""

    name: str = ""
    description: str = ""
    required: bool = True
    default: Any = None
    type: str = "string"  # string, number, boolean, list, dict


@dataclass
class Template:
    """A reusable notification template."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    notification_type: NotificationType = NotificationType.CUSTOM
    title_template: str = ""
    body_template: str = ""
    summary_template: str = ""
    variables: list[TemplateVariable] = field(default_factory=list)
    channel_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version: int = 1
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "notification_type": self.notification_type.value,
            "title_template": self.title_template,
            "body_template": self.body_template,
            "summary_template": self.summary_template,
            "variables": [
                {
                    "name": v.name,
                    "description": v.description,
                    "required": v.required,
                    "default": v.default,
                    "type": v.type,
                }
                for v in self.variables
            ],
            "channel_overrides": self.channel_overrides,
            "tags": self.tags,
            "version": self.version,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ChannelConfig:
    """Configuration for a notification channel."""

    channel: str = ""
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    rate_limit_per_minute: int = 60
    retry_policy: dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_factor": 2.0,
        "initial_delay_seconds": 1.0,
    })
    priority_filter: list[NotificationPriority] = field(default_factory=list)
    type_filter: list[NotificationType] = field(default_factory=list)
    tag_filter: list[str] = field(default_factory=list)


@dataclass
class RoutingRule:
    """A rule for routing notifications to specific channels and recipients."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    enabled: bool = True
    priority: int = 100
    conditions: dict[str, Any] = field(default_factory=dict)
    channels: list[str] = field(default_factory=list)
    recipients: list[str] = field(default_factory=list)
    template_id: Optional[str] = None
    throttle_minutes: int = 0
    suppress_duplicates: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "conditions": self.conditions,
            "channels": self.channels,
            "recipients": self.recipients,
            "template_id": self.template_id,
            "throttle_minutes": self.throttle_minutes,
            "suppress_duplicates": self.suppress_duplicates,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AnalyticsSummary:
    """Aggregated analytics for notification delivery."""

    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_suppressed: int = 0
    delivery_rate: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    by_channel: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_priority: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_type: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    top_failures: list[dict[str, Any]] = field(default_factory=list)
    period_start: str = ""
    period_end: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sent": self.total_sent,
            "total_delivered": self.total_delivered,
            "total_failed": self.total_failed,
            "total_suppressed": self.total_suppressed,
            "delivery_rate": self.delivery_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "by_channel": self.by_channel,
            "by_priority": self.by_priority,
            "by_type": self.by_type,
            "by_status": self.by_status,
            "top_failures": self.top_failures,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }
