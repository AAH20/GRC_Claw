"""Escalation workflow agent for gated-communities.

Provides functions to create and resolve escalation records for issues
that require elevated attention within gated community operations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class EscalationPriority(str, Enum):
    """Priority levels for escalations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, Enum):
    """Status values for an escalation."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


@dataclass
class EscalationDetails:
    """Details of a created escalation."""

    escalation_id: str
    issue_id: str
    priority: EscalationPriority
    status: EscalationStatus
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    notes: str = ""
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""


# In-memory store for mock escalation records
_escalation_store: Dict[str, EscalationDetails] = {}


def create_escalation(
    issue_id: str,
    priority: EscalationPriority | str,
    *,
    assigned_to: Optional[str] = None,
    notes: str = "",
) -> EscalationDetails:
    """Create a new escalation for the given issue.

    Args:
        issue_id: The identifier of the issue being escalated.
        priority: The priority level for the escalation.
        assigned_to: Optional assignee for the escalation.
        notes: Optional notes or context for the escalation.

    Returns:
        EscalationDetails containing the created escalation information.

    Raises:
        ValueError: If issue_id is empty or priority is invalid.
    """
    if not issue_id or not issue_id.strip():
        raise ValueError("issue_id must be a non-empty string")

    if isinstance(priority, str):
        try:
            priority = EscalationPriority(priority.lower())
        except ValueError:
            valid = ", ".join(p.value for p in EscalationPriority)
            raise ValueError(f"Invalid priority '{priority}'. Valid: {valid}")

    now = datetime.now(timezone.utc)
    escalation_id = f"ESC-{uuid.uuid4().hex[:12].upper()}"

    details = EscalationDetails(
        escalation_id=escalation_id,
        issue_id=issue_id.strip(),
        priority=priority,
        status=EscalationStatus.OPEN,
        created_at=now,
        updated_at=now,
        assigned_to=assigned_to,
        notes=notes,
    )

    _escalation_store[escalation_id] = details
    return details


def resolve_escalation(
    escalation_id: str,
    *,
    resolution_notes: str = "",
) -> EscalationDetails:
    """Mark an escalation as resolved.

    Args:
        escalation_id: The identifier of the escalation to resolve.
        resolution_notes: Optional notes describing the resolution.

    Returns:
        EscalationDetails containing the updated escalation information.

    Raises:
        KeyError: If the escalation_id does not exist.
        ValueError: If the escalation is already resolved or cancelled.
    """
    if escalation_id not in _escalation_store:
        raise KeyError(f"Escalation '{escalation_id}' not found")

    details = _escalation_store[escalation_id]

    if details.status == EscalationStatus.RESOLVED:
        raise ValueError(f"Escalation '{escalation_id}' is already resolved")
    if details.status == EscalationStatus.CANCELLED:
        raise ValueError(f"Escalation '{escalation_id}' has been cancelled and cannot be resolved")

    now = datetime.now(timezone.utc)
    details.status = EscalationStatus.RESOLVED
    details.resolved_at = now
    details.updated_at = now
    if resolution_notes:
        details.resolution_notes = resolution_notes

    return details


def get_escalation(escalation_id: str) -> Optional[EscalationDetails]:
    """Retrieve an escalation by ID (utility function)."""
    return _escalation_store.get(escalation_id)


def list_escalations() -> list[EscalationDetails]:
    """List all escalations (utility function)."""
    return list(_escalation_store.values())
