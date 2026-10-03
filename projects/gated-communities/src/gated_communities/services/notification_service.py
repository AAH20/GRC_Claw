"""Notification service for gated communities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-memory store keyed by user_id, each value a list of notification dicts.
# In production this would be backed by a database.
_notifications_store: dict[str, list[dict[str, Any]]] = {}


class NotificationError(Exception):
    """Raised when a notification operation fails."""


class NotificationNotFoundError(NotificationError):
    """Raised when a notification cannot be found."""


def send_notification(user_id: str, message: str) -> dict[str, Any]:
    """Send a notification to a user.

    Args:
        user_id: The unique identifier of the recipient user.
        message: The notification message body.

    Returns:
        The created notification record.

    Raises:
        NotificationError: If the notification could not be sent.
    """
    if not user_id or not user_id.strip():
        raise NotificationError("user_id must be a non-empty string")
    if not message or not message.strip():
        raise NotificationError("message must be a non-empty string")

    notification: dict[str, Any] = {
        "id": _generate_id(),
        "user_id": user_id,
        "message": message,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        _notifications_store.setdefault(user_id, []).append(notification)
    except Exception as exc:
        logger.error("Failed to store notification for user %s: %s", user_id, exc)
        raise NotificationError(f"Failed to send notification: {exc}") from exc

    logger.info("Notification %s sent to user %s", notification["id"], user_id)
    return notification


def get_notifications(user_id: str) -> list[dict[str, Any]]:
    """Retrieve all notifications for a user.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        A list of notification records, newest first.

    Raises:
        NotificationError: If notifications could not be retrieved.
    """
    if not user_id or not user_id.strip():
        raise NotificationError("user_id must be a non-empty string")

    try:
        user_notifications = _notifications_store.get(user_id, [])
        return sorted(
            user_notifications,
            key=lambda n: n.get("created_at", ""),
            reverse=True,
        )
    except Exception as exc:
        logger.error("Failed to retrieve notifications for user %s: %s", user_id, exc)
        raise NotificationError(f"Failed to retrieve notifications: {exc}") from exc


def mark_as_read(notification_id: str) -> dict[str, Any]:
    """Mark a notification as read.

    Args:
        notification_id: The unique identifier of the notification.

    Returns:
        The updated notification record.

    Raises:
        NotificationNotFoundError: If no notification with the given ID exists.
        NotificationError: If the notification could not be updated.
    """
    if not notification_id or not notification_id.strip():
        raise NotificationError("notification_id must be a non-empty string")

    try:
        for user_notifications in _notifications_store.values():
            for notification in user_notifications:
                if notification.get("id") == notification_id:
                    notification["read"] = True
                    notification["read_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info("Notification %s marked as read", notification_id)
                    return notification
    except Exception as exc:
        logger.error("Failed to mark notification %s as read: %s", notification_id, exc)
        raise NotificationError(f"Failed to mark notification as read: {exc}") from exc

    raise NotificationNotFoundError(
        f"Notification with id '{notification_id}' not found"
    )


def _generate_id() -> str:
    """Generate a unique notification identifier."""
    import uuid

    return uuid.uuid4().hex
