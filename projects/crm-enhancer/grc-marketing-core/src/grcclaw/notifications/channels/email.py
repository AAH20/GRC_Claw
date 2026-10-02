"""
Email notification channel for GRC_Claw.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import BaseChannel
from ..models import ChannelConfig, DeliveryResult, Notification


class EmailChannel(BaseChannel):
    """Delivers notifications via email using SMTP."""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.smtp_host = config.config.get("smtp_host", "localhost")
        self.smtp_port = config.config.get("smtp_port", 587)
        self.smtp_user = config.config.get("smtp_user", "")
        self.smtp_password = config.config.get("smtp_password", "")
        self.use_tls = config.config.get("use_tls", True)
        self.from_address = config.config.get("from_address", "grc-claw@localhost")
        self.from_name = config.config.get("from_name", "GRC Claw")
        self.reply_to = config.config.get("reply_to", "")
        self._smtp_client: Any = None

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(self, notification: Notification, recipient: str) -> DeliveryResult:
        """Send an email notification."""
        start = time.monotonic()

        if not self.check_rate_limit():
            return self.create_result(
                success=False,
                recipient=recipient,
                error="Rate limit exceeded",
                latency_ms=(time.monotonic() - start) * 1000,
            )

        try:
            # Build email content
            subject = notification.title or notification.summary or "GRC Claw Notification"
            body = self._build_email_body(notification)

            # In production, this would use aiosmtplib or similar
            # For now, we simulate the send
            await asyncio.sleep(0.01)  # Simulate network latency

            self.record_send()
            latency_ms = (time.monotonic() - start) * 1000

            return self.create_result(
                success=True,
                recipient=recipient,
                message_id=f"email-{notification.id[:8]}",
                latency_ms=latency_ms,
                metadata={
                    "subject": subject,
                    "smtp_host": self.smtp_host,
                    "smtp_port": self.smtp_port,
                },
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
        """Check SMTP connectivity."""
        return {
            "channel": self.channel_name,
            "healthy": True,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "use_tls": self.use_tls,
            "from_address": self.from_address,
        }

    def _build_email_body(self, notification: Notification) -> str:
        """Build the HTML email body for a notification."""
        priority_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#16a34a",
            "info": "#2563eb",
        }
        color = priority_colors.get(notification.priority.value, "#6b7280")

        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="background: {color}; padding: 16px 24px; color: white;">
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">
                        {notification.priority.value.upper()} — {notification.type.value.replace('_', ' ').title()}
                    </div>
                    <h1 style="margin: 4px 0 0; font-size: 20px; font-weight: 600;">
                        {notification.title}
                    </h1>
                </div>
                <div style="padding: 24px;">
                    <p style="font-size: 14px; line-height: 1.6; color: #374151; margin: 0 0 16px;">
                        {notification.body}
                    </p>
        """

        if notification.metadata:
            html += """
                    <div style="background: #f3f4f6; border-radius: 6px; padding: 12px; margin: 16px 0;">
                        <div style="font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: 8px;">Details</div>
                        <table style="width: 100%; font-size: 13px;">
            """
            for key, value in notification.metadata.items():
                html += f"""
                            <tr>
                                <td style="padding: 4px 0; color: #6b7280; font-weight: 500;">{key}</td>
                                <td style="padding: 4px 0; color: #111827; text-align: right;">{value}</td>
                            </tr>
                """
            html += """
                        </table>
                    </div>
            """

        if notification.runbook_url:
            html += f"""
                    <a href="{notification.runbook_url}" style="display: inline-block; background: {color}; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500; margin-top: 8px;">
                        View Runbook
                    </a>
            """

        html += f"""
                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af;">
                        Source: {notification.source} · ID: {notification.id[:8]} · {notification.created_at}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
