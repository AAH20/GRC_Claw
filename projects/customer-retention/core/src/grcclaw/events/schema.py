"""
Event schema registry for GRC_Claw.

Defines event types, schema versions, validation rules, and the central
registry that all event producers and consumers reference.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ─── Event Type Enums ────────────────────────────────────────────────────────

class EventCategory(str, Enum):
    """High-level categories for event classification."""

    COMPLIANCE = "compliance"
    RISK = "risk"
    POLICY = "policy"
    EVIDENCE = "evidence"
    WORKFLOW = "workflow"
    AUDIT = "audit"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    INTEGRATION = "integration"
    SECURITY = "security"
    CUSTOM = "custom"


class EventSeverity(str, Enum):
    """Severity levels for events."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventStatus(str, Enum):
    """Lifecycle status of an event."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"
    ARCHIVED = "archived"


# ─── Core Event Model ────────────────────────────────────────────────────────

@dataclass
class Event:
    """
    Core event envelope for all GRC_Claw events.

    Every event flowing through the system uses this structure, ensuring
    consistent metadata, traceability, and schema validation.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    category: EventCategory = EventCategory.CUSTOM
    severity: EventSeverity = EventSeverity.INFO
    status: EventStatus = EventStatus.PENDING
    source: str = ""
    source_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    causation_id: str | None = None
    trace_id: str | None = None
    schema_version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    agent_id: str | None = None
    parent_event_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    processed_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "source": self.source,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "trace_id": self.trace_id,
            "schema_version": self.schema_version,
            "tags": self.tags,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "parent_event_id": self.parent_event_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "processed_at": self.processed_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        """Deserialize an event from a dictionary."""
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            type=d.get("type", ""),
            category=EventCategory(d.get("category", "custom")),
            severity=EventSeverity(d.get("severity", "info")),
            status=EventStatus(d.get("status", "pending")),
            source=d.get("source", ""),
            source_id=d.get("source_id", ""),
            timestamp=d.get("timestamp", datetime.now(UTC).isoformat()),
            data=d.get("data", {}),
            metadata=d.get("metadata", {}),
            correlation_id=d.get("correlation_id"),
            causation_id=d.get("causation_id"),
            trace_id=d.get("trace_id"),
            schema_version=d.get("schema_version", "1.0.0"),
            tags=d.get("tags", []),
            tenant_id=d.get("tenant_id"),
            agent_id=d.get("agent_id"),
            parent_event_id=d.get("parent_event_id"),
            retry_count=d.get("retry_count", 0),
            max_retries=d.get("max_retries", 3),
            processed_at=d.get("processed_at"),
            error=d.get("error"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_json(cls, raw: str) -> Event:
        return cls.from_dict(json.loads(raw))


# ─── Schema Definition ───────────────────────────────────────────────────────

@dataclass
class EventSchema:
    """
    Schema definition for a specific event type.

    Defines the expected structure, required fields, and validation rules
    for events of a given type.
    """

    event_type: str
    category: EventCategory
    version: str = "1.0.0"
    description: str = ""
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    field_types: dict[str, str] = field(default_factory=dict)
    field_validators: dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    example: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False
    deprecation_message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def validate(self, data: dict[str, Any]) -> list[str]:
        """
        Validate event data against this schema.

        Returns a list of validation error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Check required fields
        for field_name in self.required_fields:
            if field_name not in data:
                errors.append(f"missing required field: '{field_name}'")

        # Check field types
        for field_name, expected_type in self.field_types.items():
            if field_name in data:
                value = data[field_name]
                if not self._check_type(value, expected_type):
                    errors.append(
                        f"field '{field_name}' expected type '{expected_type}', "
                        f"got '{type(value).__name__}'"
                    )

        # Run custom validators
        for field_name, validator in self.field_validators.items():
            if field_name in data:
                try:
                    if not validator(data[field_name]):
                        errors.append(
                            f"field '{field_name}' failed custom validation"
                        )
                except Exception as exc:
                    errors.append(
                        f"field '{field_name}' validator raised: {exc}"
                    )

        return errors

    def _check_type(self, value: Any, expected: str) -> bool:
        type_map: dict[str, type] = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "list": list,
            "dict": dict,
            "null": type(None),
        }
        py_type = type_map.get(expected)
        if py_type is None:
            return True
        return isinstance(value, py_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "category": self.category.value,
            "version": self.version,
            "description": self.description,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "field_types": self.field_types,
            "example": self.example,
            "tags": self.tags,
            "deprecated": self.deprecated,
            "deprecation_message": self.deprecation_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ─── Schema Registry ────────────────────────────────────────────────────────

class EventSchemaRegistry:
    """
    Central registry for all event schemas in GRC_Claw.

    Provides registration, lookup, validation, and discovery of event
    schemas. All event producers must register their schemas here.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, EventSchema] = {}
        self._lock: Any = None  # For thread-safety if needed

    def register(self, schema: EventSchema) -> None:
        """Register a new event schema."""
        key = self._key(schema.event_type, schema.version)
        self._schemas[key] = schema

    def unregister(self, event_type: str, version: str = "1.0.0") -> bool:
        """Remove a schema from the registry. Returns True if found and removed."""
        key = self._key(event_type, version)
        if key in self._schemas:
            del self._schemas[key]
            return True
        return False

    def get(self, event_type: str, version: str = "1.0.0") -> EventSchema | None:
        """Retrieve a schema by event type and version."""
        return self._schemas.get(self._key(event_type, version))

    def get_latest(self, event_type: str) -> EventSchema | None:
        """Get the latest (highest version) schema for an event type."""
        matching = [
            s for key, s in self._schemas.items()
            if s.event_type == event_type
        ]
        if not matching:
            return None
        return max(matching, key=lambda s: s.version)

    def list_schemas(
        self,
        category: EventCategory | None = None,
        tag: str | None = None,
    ) -> list[EventSchema]:
        """List all registered schemas, optionally filtered."""
        schemas = list(self._schemas.values())
        if category is not None:
            schemas = [s for s in schemas if s.category == category]
        if tag is not None:
            schemas = [s for s in schemas if tag in s.tags]
        return schemas

    def list_event_types(self) -> list[str]:
        """List all registered event type names."""
        return list({s.event_type for s in self._schemas.values()})

    def validate_event(self, event: Event) -> list[str]:
        """Validate an event against its registered schema."""
        schema = self.get(event.type, event.schema_version)
        if schema is None:
            schema = self.get_latest(event.type)
        if schema is None:
            return [f"no schema registered for event type '{event.type}'"]
        return schema.validate(event.data)

    def is_registered(self, event_type: str, version: str = "1.0.0") -> bool:
        """Check if a schema is registered for the given event type."""
        return self._key(event_type, version) in self._schemas

    def _key(self, event_type: str, version: str) -> str:
        return f"{event_type}:{version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemas": {key: schema.to_dict() for key, schema in self._schemas.items()},
            "total_schemas": len(self._schemas),
            "event_types": self.list_event_types(),
        }


# ─── Pre-built Schema Helpers ───────────────────────────────────────────────

def create_compliance_event_schema() -> EventSchema:
    return EventSchema(
        event_type="compliance.violation.detected",
        category=EventCategory.COMPLIANCE,
        description="Emitted when a compliance violation is detected",
        required_fields=["framework", "control_id", "entity_id", "severity"],
        optional_fields=["evidence_id", "description", "remediation"],
        field_types={
            "framework": "string",
            "control_id": "string",
            "entity_id": "string",
            "severity": "string",
            "evidence_id": "string",
            "description": "string",
            "remediation": "string",
        },
        example={
            "framework": "SOC2",
            "control_id": "CC6.1",
            "entity_id": "aws:us-east-1:instance-123",
            "severity": "high",
            "evidence_id": "ev-001",
            "description": "Unencrypted S3 bucket detected",
            "remediation": "Enable default encryption",
        },
        tags=["compliance", "violation", "detection"],
    )


def create_risk_event_schema() -> EventSchema:
    return EventSchema(
        event_type="risk.threshold.exceeded",
        category=EventCategory.RISK,
        description="Emitted when a risk threshold is exceeded",
        required_fields=["risk_id", "risk_name", "current_value", "threshold"],
        optional_fields=["entity_id", "framework", "trend"],
        field_types={
            "risk_id": "string",
            "risk_name": "string",
            "current_value": "number",
            "threshold": "number",
            "entity_id": "string",
            "framework": "string",
            "trend": "string",
        },
        example={
            "risk_id": "risk-001",
            "risk_name": "Data Exposure Risk",
            "current_value": 0.85,
            "threshold": 0.70,
            "entity_id": "app-payment-service",
            "framework": "NIST",
            "trend": "increasing",
        },
        tags=["risk", "threshold", "alert"],
    )


def create_workflow_event_schema() -> EventSchema:
    return EventSchema(
        event_type="workflow.step.completed",
        category=EventCategory.WORKFLOW,
        description="Emitted when a workflow step completes",
        required_fields=["workflow_id", "run_id", "step_id", "status"],
        optional_fields=["output", "duration_seconds", "error"],
        field_types={
            "workflow_id": "string",
            "run_id": "string",
            "step_id": "string",
            "status": "string",
            "output": "dict",
            "duration_seconds": "number",
            "error": "string",
        },
        example={
            "workflow_id": "wf-001",
            "run_id": "run-001",
            "step_id": "step-001",
            "status": "succeeded",
            "output": {"result": "pass"},
            "duration_seconds": 12.5,
        },
        tags=["workflow", "step", "completion"],
    )


def create_evidence_event_schema() -> EventSchema:
    return EventSchema(
        event_type="evidence.collected",
        category=EventCategory.EVIDENCE,
        description="Emitted when evidence is collected for a control",
        required_fields=["evidence_id", "control_id", "entity_id", "source"],
        optional_fields=["content", "hash", "collected_by", "expires_at"],
        field_types={
            "evidence_id": "string",
            "control_id": "string",
            "entity_id": "string",
            "source": "string",
            "content": "dict",
            "hash": "string",
            "collected_by": "string",
            "expires_at": "string",
        },
        example={
            "evidence_id": "ev-001",
            "control_id": "CC6.1",
            "entity_id": "aws:us-east-1:instance-123",
            "source": "aws-config",
            "content": {"rule": "s3-bucket-encryption", "compliant": True},
            "hash": "sha256:abc123",
            "collected_by": "evidence-collector-agent",
        },
        tags=["evidence", "collection", "control"],
    )


def create_audit_event_schema() -> EventSchema:
    return EventSchema(
        event_type="audit.finding.created",
        category=EventCategory.AUDIT,
        description="Emitted when an audit finding is created",
        required_fields=["audit_id", "finding_id", "severity", "title"],
        optional_fields=["description", "control_id", "entity_id", "remediation"],
        field_types={
            "audit_id": "string",
            "finding_id": "string",
            "severity": "string",
            "title": "string",
            "description": "string",
            "control_id": "string",
            "entity_id": "string",
            "remediation": "string",
        },
        example={
            "audit_id": "audit-001",
            "finding_id": "find-001",
            "severity": "high",
            "title": "Missing MFA on privileged accounts",
            "description": "3 privileged accounts do not have MFA enabled",
            "control_id": "CC6.1",
            "entity_id": "iam:admin-user",
            "remediation": "Enable MFA for all privileged accounts",
        },
        tags=["audit", "finding", "creation"],
    )


def create_policy_event_schema() -> EventSchema:
    return EventSchema(
        event_type="policy.breach.detected",
        category=EventCategory.POLICY,
        description="Emitted when a policy breach is detected",
        required_fields=["policy_id", "entity_id", "breach_type"],
        optional_fields=["details", "severity", "framework"],
        field_types={
            "policy_id": "string",
            "entity_id": "string",
            "breach_type": "string",
            "details": "dict",
            "severity": "string",
            "framework": "string",
        },
        example={
            "policy_id": "pol-001",
            "entity_id": "user-jdoe",
            "breach_type": "access_violation",
            "details": {"action": "unauthorized_export", "resource": "customer-data"},
            "severity": "critical",
            "framework": "GDPR",
        },
        tags=["policy", "breach", "detection"],
    )


def create_system_event_schema() -> EventSchema:
    return EventSchema(
        event_type="system.health.changed",
        category=EventCategory.SYSTEM,
        description="Emitted when system health status changes",
        required_fields=["component", "old_status", "new_status"],
        optional_fields=["details", "metrics"],
        field_types={
            "component": "string",
            "old_status": "string",
            "new_status": "string",
            "details": "dict",
            "metrics": "dict",
        },
        example={
            "component": "evidence-collector",
            "old_status": "healthy",
            "new_status": "degraded",
            "details": {"reason": "high_latency"},
            "metrics": {"latency_p99_ms": 5000, "error_rate": 0.15},
        },
        tags=["system", "health", "status"],
    )


# ─── Default Registry Factory ───────────────────────────────────────────────

def create_default_registry() -> EventSchemaRegistry:
    """Create a pre-populated schema registry with all built-in event types."""
    registry = EventSchemaRegistry()
    registry.register(create_compliance_event_schema())
    registry.register(create_risk_event_schema())
    registry.register(create_workflow_event_schema())
    registry.register(create_evidence_event_schema())
    registry.register(create_audit_event_schema())
    registry.register(create_policy_event_schema())
    registry.register(create_system_event_schema())
    return registry
