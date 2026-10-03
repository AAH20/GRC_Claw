"""Notification service for the recruitment platform."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Raised when a notification operation fails."""


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db: Any | None = None) -> None:
        """Initialize the notification service.

        Args:
            db: Optional database session/connection for persistence.
        """
        self._db = db
        self._notifications: dict[str, list[dict[str, Any]]] = {}

    def send_notification(self, user_id: str, message: str) -> dict[str, Any]:
        """Send a notification to a user.

        Args:
            user_id: The unique identifier of the recipient.
            message: The notification message content.

        Returns:
            The created notification record.

        Raises:
            NotificationError: If the notification cannot be sent.
            ValueError: If user_id or message is empty.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id must not be empty")
        if not message or not message.strip():
            raise ValueError("message must not be empty")

        notification: dict[str, Any] = {
            "id": self._generate_id(),
            "user_id": user_id,
            "message": message,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if self._db is not None:
                self._persist_notification(notification)
            else:
                self._notifications.setdefault(user_id, []).append(notification)
        except Exception as exc:
            logger.error("Failed to send notification to %s: %s", user_id, exc)
            raise NotificationError(
                f"Failed to send notification to user {user_id}"
            ) from exc

        return notification

    def get_notifications(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieve all notifications for a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            A list of notification records, newest first.

        Raises:
            NotificationError: If notifications cannot be retrieved.
            ValueError: If user_id is empty.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id must not be empty")

        try:
            if self._db is not None:
                return self._fetch_notifications(user_id)
            return list(reversed(self._notifications.get(user_id, [])))
        except Exception as exc:
            logger.error("Failed to get notifications for %s: %s", user_id, exc)
            raise NotificationError(
                f"Failed to get notifications for user {user_id}"
            ) from exc

    def mark_as_read(self, notification_id: str) -> dict[str, Any]:
        """Mark a notification as read.

        Args:
            notification_id: The unique identifier of the notification.

        Returns:
            The updated notification record.

        Raises:
            NotificationError: If the notification cannot be updated.
            ValueError: If notification_id is empty.
            LookupError: If the notification is not found.
        """
        if not notification_id or not notification_id.strip():
            raise ValueError("notification_id must not be empty")

        try:
            if self._db is not None:
                return self._update_read_status(notification_id, True)

            for notifications in self._notifications.values():
                for notification in notifications:
                    if notification["id"] == notification_id:
                        notification["read"] = True
                        return notification
            raise LookupError(
                f"Notification {notification_id} not found"
            )
        except LookupError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to mark notification %s as read: %s",
                notification_id,
                exc,
            )
            raise NotificationError(
                f"Failed to mark notification {notification_id} as read"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique notification identifier."""
        import uuid

        return str(uuid.uuid4())

    def _persist_notification(self, notification: dict[str, Any]) -> None:
        """Persist a notification via the database session."""
        if self._db is None:
            raise NotificationError("No database session available")
        self._db.add(notification)

    def _fetch_notifications(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch notifications for a user from the database."""
        if self._db is None:
            raise NotificationError("No database session available")
        return self._db.query(user_id=user_id)

    def _update_read_status(
        self, notification_id: str, read: bool
    ) -> dict[str, Any]:
        """Update the read status of a notification in the database."""
        if self._db is None:
            raise NotificationError("No database session available")
        return self._db.update(notification_id, read=read)
