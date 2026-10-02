"""Notification service integration."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class NotificationResult:
    """Result of a notification operation."""

    def __init__(self, success: bool, message_id: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self.success = success
        self.message_id = message_id
        self.metadata = metadata or {}


class NotificationService(ABC):
    """Abstract base class for notification services."""

    @abstractmethod
    async def send_notification(
        self, recipient: str, subject: str, body: str, metadata: Optional[dict[str, Any]] = None
    ) -> NotificationResult:
        """Send a notification."""
        ...


class EmailNotificationService(NotificationService):
    """Email notification service using SendGrid."""

    def __init__(self, api_key: str, from_email: str = "noreply@content-marketplace.com") -> None:
        self.api_key = api_key
        self.from_email = from_email

    async def send_notification(
        self, recipient: str, subject: str, body: str, metadata: Optional[dict[str, Any]] = None
    ) -> NotificationResult:
        """Send an email notification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "personalizations": [{"to": [{"email": recipient}]}],
                        "from": {"email": self.from_email},
                        "subject": subject,
                        "content": [{"type": "text/plain", "value": body}],
                    },
                )
                response.raise_for_status()
                return NotificationResult(
                    success=True,
                    message_id=response.headers.get("X-Message-Id", "unknown"),
                )
        except httpx.HTTPError as e:
            logger.error("Email notification failed: %s", e)
            return NotificationResult(success=False, message_id="failed", metadata={"error": str(e)})


class WebhookNotificationService(NotificationService):
    """Webhook notification service for real-time events."""

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        self.webhook_url = webhook_url
        self.secret = secret

    async def send_notification(
        self, recipient: str, subject: str, body: str, metadata: Optional[dict[str, Any]] = None
    ) -> NotificationResult:
        """Send a webhook notification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "recipient": recipient,
                        "subject": subject,
                        "body": body,
                        "metadata": metadata or {},
                    },
                    headers={"X-Webhook-Secret": self.secret} if self.secret else {},
                )
                response.raise_for_status()
                return NotificationResult(success=True, message_id=str(response.status_code))
        except httpx.HTTPError as e:
            logger.error("Webhook notification failed: %s", e)
            return NotificationResult(success=False, message_id="failed", metadata={"error": str(e)})
