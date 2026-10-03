"""Notification service for ugc-marketplace."""

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
            db: Database session/connection for persistence.
        """
        self._db = db
        self._notifications: dict[str, list[dict[str, Any]]] = {}

    def send_notification(self, user_id: str, message: str) -> dict[str, Any]:
        """Send a notification to a user.

        Args:
            user_id: The ID of the user to notify.
            message: The notification message content.

        Returns:
            The created notification record.

        Raises:
            NotificationError: If the notification could not be sent.
            ValueError: If user_id or message is empty.
        """
        if not user_id:
            raise ValueError("user_id must not be empty")
        if not message:
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
            logger.error("Failed to send notification to user %s: %s", user_id, exc)
            raise NotificationError(
                f"Failed to send notification to user {user_id}"
            ) from exc

        logger.info("Notification sent to user %s", user_id)
        return notification

    def get_notifications(self, user_id: str) -> list[dict[str, Any]]:
        """Get all notifications for a user.

        Args:
            user_id: The ID of the user whose notifications to retrieve.

        Returns:
            A list of notification records for the user.

        Raises:
            NotificationError: If notifications could not be retrieved.
            ValueError: If user_id is empty.
        """
        if not user_id:
            raise ValueError("user_id must not be empty")

        try:
            if self._db is not None:
                return self._fetch_notifications(user_id)
            return list(self._notifications.get(user_id, []))
        except Exception as exc:
            logger.error("Failed to get notifications for user %s: %s", user_id, exc)
            raise NotificationError(
                f"Failed to get notifications for user {user_id}"
            ) from exc

    def mark_as_read(self, notification_id: str) -> dict[str, Any]:
        """Mark a notification as read.

        Args:
            notification_id: The ID of the notification to mark as read.

        Returns:
            The updated notification record.

        Raises:
            NotificationError: If the notification could not be updated.
            ValueError: If notification_id is empty or not found.
        """
        if not notification_id:
            raise ValueError("notification_id must not be empty")

        try:
            if self._db is not None:
                return self._update_read_status(notification_id)

            for notifications in self._notifications.values():
                for notification in notifications:
                    if notification["id"] == notification_id:
                        notification["read"] = True
                        return notification
            raise ValueError(f"Notification {notification_id} not found")
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to mark notification %s as read: %s", notification_id, exc)
            raise NotificationError(
                f"Failed to mark notification {notification_id} as read"
            ) from exc

    def _generate_id(self) -> str:
        """Generate a unique notification ID."""
        import uuid

        return str(uuid.uuid4())

    def _persist_notification(self, notification: dict[str, Any]) -> None:
        """Persist a notification to the database."""
        if self._db is None:
            raise NotificationError("No database connection available")
        self._db.execute(
            "INSERT INTO notifications (id, user_id, message, read, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                notification["id"],
                notification["user_id"],
                notification["message"],
                notification["read"],
                notification["created_at"],
            ),
        )

    def _fetch_notifications(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch notifications from the database."""
        if self._db is None:
            raise NotificationError("No database connection available")
        cursor = self._db.execute(
            "SELECT id, user_id, message, read, created_at FROM notifications "
            "WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "message": row[2],
                "read": bool(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def _update_read_status(self, notification_id: str) -> dict[str, Any]:
        """Update the read status of a notification in the database."""
        if self._db is None:
            raise NotificationError("No database connection available")
        cursor = self._db.execute(
            "UPDATE notifications SET read = ? WHERE id = ? RETURNING id, user_id, message, read, created_at",
            (True, notification_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Notification {notification_id} not found")
        return {
            "id": row[0],
            "user_id": row[1],
            "message": row[2],
            "read": bool(row[3]),
            "created_at": row[4],
        }
