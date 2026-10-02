"""Slack integration for escalation notifications."""

from __future__ import annotations

import structlog
from typing import Any

import httpx

from escalation_workflow.config import Settings
from escalation_workflow.integrations.notifications import NotificationChannel

logger = structlog.get_logger(__name__)


class SlackIntegration(NotificationChannel):
    """Slack webhook integration for sending notifications."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize Slack integration.

        Args:
            webhook_url: Slack incoming webhook URL.
        """
        self.webhook_url = webhook_url
        self.logger = logger.bind(integration="slack")

    async def send(self, message: str, **kwargs: Any) -> bool:
        """Send a message to Slack.

        Args:
            message: The message text.
            **kwargs: Additional parameters (channel, username, icon_emoji).

        Returns:
            bool: True if sent successfully.
        """
        if not self.webhook_url:
            self.logger.warning("Slack webhook URL not configured")
            return False

        payload = {
            "text": message,
            "channel": kwargs.get("channel", "#escalations"),
            "username": kwargs.get("username", "Escalation Bot"),
            "icon_emoji": kwargs.get("icon_emoji", ":rotating_light:"),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                success = response.status_code == 200
                if not success:
                    self.logger.error(
                        "Slack API error",
                        status=response.status_code,
                        body=response.text,
                    )
                return success
        except httpx.HTTPError as exc:
            self.logger.error("Slack request failed", error=str(exc))
            return False
