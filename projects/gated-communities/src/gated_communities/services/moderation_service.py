"""Moderation service for gated communities.

Handles creation, retrieval, and resolution of moderation items
such as reported content, flagged posts, and user appeals.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ModerationAction(str, Enum):
    """Valid actions for resolving a moderation item."""

    APPROVE = "approve"
    REJECT = "reject"
    DISMISS = "dismiss"
    ESCALATE = "escalate"


class ModerationStatus(str, Enum):
    """Lifecycle status of a moderation item."""

    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class ModerationError(Exception):
    """Base exception for moderation service errors."""


class ValidationError(ModerationItemError := ModerationError):
    """Raised when input data fails validation."""


class ItemNotFoundError(ModerationError):
    """Raised when a moderation item cannot be found."""


class InvalidActionError(ModerationError):
    """Raised when an invalid resolution action is provided."""


@dataclass
class ModerationItem:
    """Represents a single moderation queue entry."""

    id: str
    community_id: str
    reporter_id: str
    target_type: str
    target_id: str
    reason: str
    status: ModerationStatus = ModerationStatus.PENDING
    action: Optional[ModerationAction] = None
    moderator_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# In-memory store — replace with database persistence in production
_moderation_store: Dict[str, ModerationItem] = {}


def _validate_moderation_data(data: Dict[str, Any]) -> None:
    """Validate incoming moderation item data.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    required_fields = ("community_id", "reporter_id", "target_type", "target_id", "reason")
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(data["community_id"], str) or not data["community_id"].strip():
        raise ValidationError("community_id must be a non-empty string")
    if not isinstance(data["reporter_id"], str) or not data["reporter_id"].strip():
        raise ValidationError("reporter_id must be a non-empty string")
    if not isinstance(data["target_type"], str) or not data["target_type"].strip():
        raise ValidationError("target_type must be a non-empty string")
    if not isinstance(data["target_id"], str) or not data["target_id"].strip():
        raise ValidationError("target_id must be a non-empty string")
    if not isinstance(data["reason"], str) or not data["reason"].strip():
        raise ValidationError("reason must be a non-empty string")


def create_moderation_item(data: Dict[str, Any]) -> ModerationItem:
    """Create a new moderation item after validating input data.

    Args:
        data: Dictionary containing moderation item fields.

    Returns:
        The newly created ModerationItem.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    _validate_moderation_data(data)

    item = ModerationItem(
        id=str(uuid.uuid4()),
        community_id=data["community_id"].strip(),
        reporter_id=data["reporter_id"].strip(),
        target_type=data["target_type"].strip(),
        target_id=data["target_id"].strip(),
        reason=data["reason"].strip(),
        metadata=data.get("metadata", {}),
    )

    _moderation_store[item.id] = item
    return item


def get_moderation_queue(
    community_id: Optional[str] = None,
    status: Optional[ModerationStatus] = None,
) -> List[ModerationItem]:
    """Retrieve the moderation queue, optionally filtered.

    Args:
        community_id: Filter by community ID.
        status: Filter by moderation status.

    Returns:
        List of ModerationItem matching the filters, newest first.
    """
    items = list(_moderation_store.values())

    if community_id is not None:
        items = [i for i in items if i.community_id == community_id]
    if status is not None:
        items = [i for i in items if i.status == status]

    items.sort(key=lambda i: i.created_at, reverse=True)
    return items


def resolve_moderation_item(
    item_id: str,
    action: ModerationAction | str,
    moderator_id: Optional[str] = None,
) -> ModerationItem:
    """Resolve a moderation item with the given action.

    Args:
        item_id: The ID of the moderation item to resolve.
        action: The resolution action (approve, reject, dismiss, escalate).
        moderator_id: Optional ID of the moderator performing the action.

    Returns:
        The updated ModerationItem.

    Raises:
        ItemNotFoundError: If the item does not exist.
        InvalidActionError: If the action is not valid.
        ModerationError: If the item is already resolved.
    """
    if item_id not in _moderation_store:
        raise ItemNotFoundError(f"Moderation item '{item_id}' not found")

    item = _moderation_store[item_id]

    if item.status != ModerationStatus.PENDING:
        raise ModerationError(
            f"Item '{item_id}' is already {item.status.value}"
        )

    if isinstance(action, str):
        try:
            action = ModerationAction(action.lower())
        except ValueError:
            valid = ", ".join(a.value for a in ModerationAction)
            raise InvalidActionError(
                f"Invalid action '{action}'. Valid actions: {valid}"
            )

    if not isinstance(action, ModerationAction):
        raise InvalidActionError("action must be a ModerationAction or valid string")

    item.action = action
    item.moderator_id = moderator_id
    item.resolved_at = datetime.now(timezone.utc)

    if action == ModerationAction.ESCALATE:
        item.status = ModerationStatus.ESCALATED
    else:
        item.status = ModerationStatus.RESOLVED

    return item
