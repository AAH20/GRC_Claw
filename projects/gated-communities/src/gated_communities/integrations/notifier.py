"""Notification integrations for compliance alerts."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from compliance_monitor.config.settings import get_settings

logger = structlog.get_logger(__name__)


class Notifier:
    """Sends compliance notifications via Slack and email.

    Supports Slack webhook notifications and SMTP email alerts
    for compliance violations and audit reports.
    """

    def __init__(self) -> None:
        """Initialize the notifier with settings."""
        self.settings = get_settings()
        self._http_client = httpx.AsyncClient(timeout=10.0)

    async def send_slack_alert(self, message: str, severity: str = "medium") -> bool:
        """Send a Slack notification.

        Args:
            message: Notification message.
            severity: Alert severity level.

        Returns:
            True if sent successfully.
        """
        if not self.settings.slack_webhook_url:
            logger.warning("Slack webhook not configured, skipping notification")
            return False

        color_map = {
            "low": "#36a64f",
            "medium": "#daa520",
            "high": "#ff4500",
            "critical": "#8b0000",
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(severity, "#808080"),
                    "title": "Compliance Alert",
                    "text": message,
                    "fields": [
                        {"title": "Severity", "value": severity, "short": True},
                        {
                            "title": "Service",
                            "value": "compliance-monitor",
                            "short": True,
                        },
                    ],
                }
            ]
        }

        try:
            response = await self._http_client.post(
                self.settings.slack_webhook_url,
                json=payload,
            )
            response.raise_for_status()
            logger.info("Slack notification sent", severity=severity)
            return True
        except httpx.HTTPError as exc:
            logger.error("Failed to send Slack notification", error=str(exc))
            return False

    async def send_email(
        self,
        subject: str,
        body: str,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send an email notification.

        Args:
            subject: Email subject.
            body: Email body.
            recipients: List of recipient emails.

        Returns:
            True if sent successfully.
        """
        if not self.settings.smtp_host:
            logger.warning("SMTP not configured, skipping email")
            return False

        recipients = (
            recipients or [self.settings.notification_email]
            if self.settings.notification_email
            else []
        )

        if not recipients:
            logger.warning("No recipients configured for email")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.settings.smtp_user
            msg["To"] = ", ".join(recipients)

            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port
            ) as server:
                if self.settings.smtp_user and self.settings.smtp_password:
                    server.starttls()
                    server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(msg)

            logger.info("Email notification sent", recipients=recipients)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email notification", error=str(exc))
            return False

    async def notify_violation(self, violation_data: dict[str, Any]) -> None:
        """Send notifications for a compliance violation.

        Args:
            violation_data: Violation data to include in notification.
        """
        message = (
            f"Compliance Violation Detected\n"
            f"Title: {violation_data.get('title', 'N/A')}\n"
            f"Severity: {violation_data.get('severity', 'N/A')}\n"
            f"Description: {violation_data.get('description', 'N/A')}"
        )
        severity = violation_data.get("severity", "medium")
        await self.send_slack_alert(message, severity)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()
