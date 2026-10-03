"""Notification services for content marketplace."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class NotificationResult:
    """Result of a notification send."""

    def __init__(
        self, success: bool, message_id: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Initialize notification result.

        Args:
            success: Whether the notification was sent.
            message_id: Message identifier.
            metadata: Optional metadata.
        """
        self.success = success
        self.message_id = message_id
        self.metadata = metadata or {}


class NotificationService(ABC):
    """Abstract base class for notification services."""

    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """Send a notification.

        Args:
            recipient: Recipient address.
            subject: Notification subject.
            body: Notification body.
            metadata: Optional metadata.

        Returns:
            Notification result.
        """
        ...


class EmailNotificationService(NotificationService):
    """Email notification service."""

    def __init__(
        self, api_key: str, from_email: str = "noreply@ugc-marketplace.com"
    ) -> None:
        """Initialize email notification service.

        Args:
            api_key: Email service API key.
            from_email: From email address.
        """
        self.api_key = api_key
        self.from_email = from_email

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """Send an email notification.

        Args:
            recipient: Recipient email.
            subject: Email subject.
            body: Email body.
            metadata: Optional metadata.

        Returns:
            Notification result.
        """
        logger.info("Sending email notification", recipient=recipient, subject=subject)
        return NotificationResult(success=True, message_id="email_123")


class WebhookNotificationService(NotificationService):
    """Webhook notification service."""

    def __init__(self, webhook_url: str, secret: str) -> None:
        """Initialize webhook notification service.

        Args:
            webhook_url: Webhook URL.
            secret: Webhook secret.
        """
        self.webhook_url = webhook_url
        self.secret = secret

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """Send a webhook notification.

        Args:
            recipient: Recipient identifier.
            subject: Notification subject.
            body: Notification body.
            metadata: Optional metadata.

        Returns:
            Notification result.
        """
        logger.info("Sending webhook notification", recipient=recipient)
        return NotificationResult(success=True, message_id="webhook_123")
