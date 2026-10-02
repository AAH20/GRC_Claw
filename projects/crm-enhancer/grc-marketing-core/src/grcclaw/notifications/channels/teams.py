"""
Microsoft Teams notification channel for GRC_Claw.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import BaseChannel
from ..models import ChannelConfig, DeliveryResult, Notification


class TeamsChannel(BaseChannel):
    """Delivers notifications via Microsoft Teams webhooks or Graph API."""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url", "")
        self.tenant_id = config.config.get("tenant_id", "")
        self.client_id = config.config.get("client_id", "")
        self.client_secret = config.config.get("client_secret", "")
        self.default_channel = config.config.get("default_channel", "General")
        self.team_id = config.config.get("team_id", "")
        self.channel_id = config.config.get("channel_id", "")
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @property
    def channel_name(self) -> str:
        return "teams"

    async def send(self, notification: Notification, recipient: str) -> DeliveryResult:
        """Send a Microsoft Teams notification."""
        start = time.monotonic()

        if not self.check_rate_limit():
            return self.create_result(
                success=False,
                recipient=recipient,
                error="Rate limit exceeded",
                latency_ms=(time.monotonic() - start) * 1000,
            )

        try:
            payload = self._build_teams_payload(notification)

            # In production, this would use aiohttp to POST to Teams webhook
            # or use the Graph API with OAuth2 authentication
            await asyncio.sleep(0.01)  # Simulate network latency

            self.record_send()
            latency_ms = (time.monotonic() - start) * 1000

            return self.create_result(
                success=True,
                recipient=recipient or self.default_channel,
                message_id=f"teams-{notification.id[:8]}",
                latency_ms=latency_ms,
                metadata={"channel": self.default_channel, "team_id": self.team_id},
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
        """Check Teams connectivity."""
        return {
            "channel": self.channel_name,
            "healthy": bool(self.webhook_url or (self.tenant_id and self.client_id)),
            "webhook_configured": bool(self.webhook_url),
            "graph_api_configured": bool(self.tenant_id and self.client_id),
            "default_channel": self.default_channel,
            "team_id": self.team_id,
        }

    def _build_teams_payload(self, notification: Notification) -> dict[str, Any]:
        """Build a Microsoft Teams Adaptive Card payload."""
        theme_color_map = {
            "critical": "attention",
            "high": "warning",
            "medium": "accent",
            "low": "good",
            "info": "default",
        }
        theme_color = theme_color_map.get(notification.priority.value, "default")

        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "msteams": {"width": "Full"},
            "body": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": self._get_emoji(notification.priority.value),
                                    "size": "Large",
                                    "weight": "Bolder",
                                }
                            ],
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": notification.title,
                                    "weight": "Bolder",
                                    "size": "Medium",
                                    "color": theme_color,
                                    "wrap": True,
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"{notification.priority.value.upper()} — {notification.type.value.replace('_', ' ').title()}",
                                    "size": "Small",
                                    "color": "Accent",
                                    "spacing": "None",
                                    "wrap": True,
                                },
                            ],
                        },
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": notification.body,
                    "wrap": True,
                    "spacing": "Medium",
                },
            ],
            "actions": [],
        }

        # Add metadata as facts
        if notification.metadata:
            facts = []
            for key, value in notification.metadata.items():
                facts.append({"title": key, "value": str(value)[:500]})
            if facts:
                card["body"].append({
                    "type": "FactSet",
                    "facts": facts[:10],
                    "spacing": "Medium",
                })

        # Add action buttons
        actions = []
        if notification.runbook_url:
            actions.append({
                "type": "Action.OpenUrl",
                "title": "View Runbook",
                "url": notification.runbook_url,
            })
        if notification.priority.value in ("critical", "high"):
            actions.append({
                "type": "Action.Submit",
                "title": "Acknowledge",
                "data": {"action": "acknowledge", "notification_id": notification.id},
            })
        if actions:
            card["actions"] = actions

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                }
            ],
        }

    def _get_emoji(self, priority: str) -> str:
        """Get an emoji for the priority level."""
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }
        return emoji_map.get(priority, "⚪")
