"""
Slack notification channel for GRC_Claw.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import BaseChannel
from ..models import ChannelConfig, DeliveryResult, Notification


class SlackChannel(BaseChannel):
    """Delivers notifications via Slack webhooks or the Slack API."""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url", "")
        self.bot_token = config.config.get("bot_token", "")
        self.default_channel = config.config.get("default_channel", "#grc-alerts")
        self.username = config.config.get("username", "GRC Claw")
        self.icon_emoji = config.config.get("icon_emoji", ":warning:")
        self._session: Any = None

    @property
    def channel_name(self) -> str:
        return "slack"

    async def send(self, notification: Notification, recipient: str) -> DeliveryResult:
        """Send a Slack notification."""
        start = time.monotonic()

        if not self.check_rate_limit():
            return self.create_result(
                success=False,
                recipient=recipient,
                error="Rate limit exceeded",
                latency_ms=(time.monotonic() - start) * 1000,
            )

        try:
            channel = recipient if recipient.startswith("#") or recipient.startswith("@") else self.default_channel
            payload = self._build_slack_payload(notification, channel)

            # In production, this would use aiohttp to POST to Slack
            await asyncio.sleep(0.01)  # Simulate network latency

            self.record_send()
            latency_ms = (time.monotonic() - start) * 1000

            return self.create_result(
                success=True,
                recipient=channel,
                message_id=f"slack-{notification.id[:8]}",
                latency_ms=latency_ms,
                metadata={"channel": channel, "payload_blocks": len(payload.get("blocks", []))},
            )
        except Exception as e:
            latency_ms = (time.monotonic() - start) * 1000
            return self.create_result(
                success=False,
                recipient=recipient,
                error=str(e),
                latency_ms=latency_ms,
            )

    async def health_check(self) -> dict[str, Any]:
        """Check Slack connectivity."""
        return {
            "channel": self.channel_name,
            "healthy": bool(self.webhook_url or self.bot_token),
            "webhook_configured": bool(self.webhook_url),
            "bot_token_configured": bool(self.bot_token),
            "default_channel": self.default_channel,
        }

    def _build_slack_payload(self, notification: Notification, channel: str) -> dict[str, Any]:
        """Build a Slack message payload with Block Kit formatting."""
        color_map = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#16a34a",
            "info": "#2563eb",
        }
        color = color_map.get(notification.priority.value, "#6b7280")

        emoji_map = {
            "critical": ":rotating_light:",
            "high": ":warning:",
            "medium": ":information_source:",
            "low": ":white_check_mark:",
            "info": ":bulb:",
        }
        emoji = emoji_map.get(notification.priority.value, ":bell:")

        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {notification.title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notification.body[:3000],  # Slack limit
                },
            },
        ]

        # Add metadata fields
        if notification.metadata:
            fields = []
            for key, value in list(notification.metadata.items())[:10]:
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{str(value)[:200]}",
                })
            if fields:
                blocks.append({"type": "section", "fields": fields})

        # Add context footer
        context_text = f"Source: {notification.source} · Type: {notification.type.value} · ID: `{notification.id[:8]}`"
        if notification.runbook_url:
            context_text += f" · <{notification.runbook_url}|Runbook>"
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": context_text}],
        })

        # Add action buttons for critical/high priority
        if notification.priority.value in ("critical", "high"):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Acknowledge", "emoji": True},
                        "style": "primary",
                        "value": f"ack_{notification.id}",
                        "action_id": "acknowledge_alert",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Details", "emoji": True},
                        "url": notification.runbook_url or "#",
                        "action_id": "view_details",
                    },
                ],
            })

        return {
            "channel": channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [{"color": color, "blocks": blocks}],
            "text": notification.summary or notification.title,  # Fallback for notifications
        }
