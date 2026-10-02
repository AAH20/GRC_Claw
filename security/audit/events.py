"""Immutable audit event schema for agentic AI marketing security layer.

Provides structured audit events, event serialization, schema validation,
and tamper-evident event logging.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union


class AuditEventType(str, Enum):
    """Audit event types."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCESS = "access"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_ALERT = "security_alert"
    AGENT_ACTION = "agent_action"
    POLICY_VIOLATION = "policy_violation"
    ENCRYPTION_OPERATION = "encryption_operation"
    SECRET_ACCESS = "secret_access"
    NETWORK_ACCESS = "network_access"
    COMPLIANCE_EVENT = "compliance_event"
    SYSTEM_EVENT = "system_event"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class AuditOutcome(str, Enum):
    """Audit event outcomes."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"
    PARTIAL = "partial"


@dataclass(frozen=True)
class Actor:
    """Actor performing the action."""

    id: str
    type: str
    name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Resource:
    """Resource being accessed or modified."""

    id: str
    type: str
    name: Optional[str] = None
    uri: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Action:
    """Action being performed."""

    name: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None


@dataclass(frozen=True)
class Context:
    """Event context."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    environment: str = "production"
    service: Optional[str] = None
    version: Optional[str] = None
    region: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit event."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    type: AuditEventType = AuditEventType.SYSTEM_EVENT
    severity: AuditSeverity = AuditSeverity.INFO
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    actor: Optional[Actor] = None
    resource: Optional[Resource] = None
    action: Optional[Action] = None
    context: Context = field(default_factory=Context)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    compliance: List[str] = field(default_factory=list)
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None

    def __post_init__(self) -> None:
        if self.event_hash is None:
            object.__setattr__(self, "event_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        """Compute the event hash for tamper evidence."""
        data = {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type.value,
            "severity": self.severity.value,
            "outcome": self.outcome.value,
            "actor": asdict(self.actor) if self.actor else None,
            "resource": asdict(self.resource) if self.resource else None,
            "action": asdict(self.action) if self.action else None,
            "context": asdict(self.context),
            "message": self.message,
            "details": self.details,
            "tags": self.tags,
            "compliance": self.compliance,
            "previous_hash": self.previous_hash,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type.value,
            "severity": self.severity.value,
            "outcome": self.outcome.value,
            "actor": asdict(self.actor) if self.actor else None,
            "resource": asdict(self.resource) if self.resource else None,
            "action": asdict(self.action) if self.action else None,
            "context": asdict(self.context),
            "message": self.message,
            "details": self.details,
            "tags": self.tags,
            "compliance": self.compliance,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        actor = Actor(**data["actor"]) if data.get("actor") else None
        resource = Resource(**data["resource"]) if data.get("resource") else None
        action = Action(**data["action"]) if data.get("action") else None
        context = Context(**data.get("context", {}))
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            type=AuditEventType(data["type"]),
            severity=AuditSeverity(data["severity"]),
            outcome=AuditOutcome(data["outcome"]),
            actor=actor,
            resource=resource,
            action=action,
            context=context,
            message=data.get("message", ""),
            details=data.get("details", {}),
            tags=data.get("tags", []),
            compliance=data.get("compliance", []),
            previous_hash=data.get("previous_hash"),
            event_hash=data.get("event_hash"),
        )

    def verify_integrity(self) -> bool:
        """Verify the event's integrity by recomputing the hash."""
        return self.event_hash == self._compute_hash()


class AuditEventBuilder:
    """Builder for audit events."""

    def __init__(self) -> None:
        self._id = str(uuid.uuid4())
        self._timestamp = time.time()
        self._type = AuditEventType.SYSTEM_EVENT
        self._severity = AuditSeverity.INFO
        self._outcome = AuditOutcome.SUCCESS
        self._actor: Optional[Actor] = None
        self._resource: Optional[Resource] = None
        self._action: Optional[Action] = None
        self._context = Context()
        self._message = ""
        self._details: Dict[str, Any] = {}
        self._tags: List[str] = []
        self._compliance: List[str] = []
        self._previous_hash: Optional[str] = None

    def with_type(self, event_type: AuditEventType) -> "AuditEventBuilder":
        self._type = event_type
        return self

    def with_severity(self, severity: AuditSeverity) -> "AuditEventBuilder":
        self._severity = severity
        return self

    def with_outcome(self, outcome: AuditOutcome) -> "AuditEventBuilder":
        self._outcome = outcome
        return self

    def with_actor(self, actor: Actor) -> "AuditEventBuilder":
        self._actor = actor
        return self

    def with_resource(self, resource: Resource) -> "AuditEventBuilder":
        self._resource = resource
        return self

    def with_action(self, action: Action) -> "AuditEventBuilder":
        self._action = action
        return self

    def with_context(self, context: Context) -> "AuditEventBuilder":
        self._context = context
        return self

    def with_message(self, message: str) -> "AuditEventBuilder":
        self._message = message
        return self

    def with_details(self, details: Dict[str, Any]) -> "AuditEventBuilder":
        self._details = details
        return self

    def with_tags(self, tags: List[str]) -> "AuditEventBuilder":
        self._tags = tags
        return self

    def with_compliance(self, compliance: List[str]) -> "AuditEventBuilder":
        self._compliance = compliance
        return self

    def with_previous_hash(self, previous_hash: Optional[str]) -> "AuditEventBuilder":
        self._previous_hash = previous_hash
        return self

    def build(self) -> AuditEvent:
        """Build the audit event."""
        return AuditEvent(
            id=self._id,
            timestamp=self._timestamp,
            type=self._type,
            severity=self._severity,
            outcome=self._outcome,
            actor=self._actor,
            resource=self._resource,
            action=self._action,
            context=self._context,
            message=self._message,
            details=self._details,
            tags=self._tags,
            compliance=self._compliance,
            previous_hash=self._previous_hash,
        )


class AuditEventSchema:
    """Schema validation for audit events."""

    REQUIRED_FIELDS = {"id", "timestamp", "type", "severity", "outcome"}
    VALID_TYPES = {e.value for e in AuditEventType}
    VALID_SEVERITIES = {e.value for e in AuditSeverity}
    VALID_OUTCOMES = {e.value for e in AuditOutcome}

    @classmethod
    def validate(cls, event: Union[AuditEvent, Dict[str, Any]]) -> bool:
        """Validate an audit event against the schema."""
        if isinstance(event, AuditEvent):
            data = event.to_dict()
        else:
            data = event

        # Check required fields
        missing = cls.REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate enum values
        if data["type"] not in cls.VALID_TYPES:
            raise ValueError(f"Invalid event type: {data['type']}")
        if data["severity"] not in cls.VALID_SEVERITIES:
            raise ValueError(f"Invalid severity: {data['severity']}")
        if data["outcome"] not in cls.VALID_OUTCOMES:
            raise ValueError(f"Invalid outcome: {data['outcome']}")

        # Validate timestamp
        if not isinstance(data["timestamp"], (int, float)):
            raise ValueError("Timestamp must be numeric")

        return True
