"""PagerDuty integration for critical escalation alerts."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from escalation_workflow.integrations.notifications import NotificationChannel

logger = structlog.get_logger(__name__)


class PagerDutyIntegration(NotificationChannel):
    """PagerDuty Events API integration for critical alerts."""

    def __init__(self, api_key: str, service_key: str = "") -> None:
        """Initialize PagerDuty integration.

        Args:
            api_key: PagerDuty API key.
            service_key: PagerDuty service key for event routing.
        """
        self.api_key = api_key
        self.service_key = service_key
        self.base_url = "https://events.pagerduty.com/v2/enqueue"
        self.logger = logger.bind(integration="pagerduty")

    async def send(self, message: str, **kwargs: Any) -> bool:
        """Send a PagerDuty event.

        Args:
            message: The event description.
            **kwargs: Additional parameters (severity, source, dedup_key).

        Returns:
            bool: True if sent successfully.
        """
        if not self.api_key:
            self.logger.warning("PagerDuty API key not configured")
            return False

        payload = {
            "routing_key": self.service_key or self.api_key,
            "event_action": kwargs.get("event_action", "trigger"),
            "dedup_key": kwargs.get("dedup_key", ""),
            "payload": {
                "summary": message,
                "severity": kwargs.get("severity", "critical"),
                "source": kwargs.get("source", "escalation-workflow"),
                "custom_details": kwargs.get("custom_details", {}),
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={"Authorization": f"Token token={self.api_key}"},
                )
                success = response.status_code == 202
                if not success:
                    self.logger.error(
                        "PagerDuty API error",
                        status=response.status_code,
                        body=response.text,
                    )
                return success
        except httpx.HTTPError as exc:
            self.logger.error("PagerDuty request failed", error=str(exc))
            return False
