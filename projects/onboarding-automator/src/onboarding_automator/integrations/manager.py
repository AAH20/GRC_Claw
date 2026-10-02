"""Integration manager for external service connections.

Manages connections to external services like email providers, Slack,
HR systems, and document storage backends.
"""

from __future__ import annotations

from typing import Any

from onboarding_automator.config.settings import Settings

__all__ = ["IntegrationManager"]


class IntegrationManager:
    """Manages connections and clients for external service integrations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the integration manager.

        Args:
            settings: Application settings containing integration configs.
        """
        self.settings = settings
        self._clients: dict[str, Any] = {}
        self._connected: dict[str, bool] = {}

    async def connect(self, service: str) -> bool:
        """Establish a connection to an external service.

        Args:
            service: The service name (e.g. 'email', 'slack', 'hr_system').

        Returns:
            True if connection was successful.
        """
        self._connected[service] = True
        return True

    async def disconnect(self, service: str) -> None:
        """Disconnect from an external service.

        Args:
            service: The service name to disconnect.
        """
        self._connected.pop(service, None)
        self._clients.pop(service, None)

    async def close(self) -> None:
        """Close all active connections."""
        for service in list(self._connected.keys()):
            await self.disconnect(service)

    def is_connected(self, service: str) -> bool:
        """Check if a service is currently connected.

        Args:
            service: The service name to check.

        Returns:
            True if the service is connected.
        """
        return self._connected.get(service, False)

    def get_client(self, service: str) -> Any:
        """Get the client for a specific service.

        Args:
            service: The service name.

        Returns:
            The service client instance.

        Raises:
            KeyError: If the service is not connected.
        """
        if service not in self._clients:
            raise KeyError(f"Service '{service}' is not connected")
        return self._clients[service]

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> dict[str, Any]:
        """Send an email via the configured email provider.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Email body content.
            html: Whether the body is HTML.

        Returns:
            Dict with send result information.
        """
        if not self.is_connected("email"):
            await self.connect("email")
        return {"success": True, "message_id": "mock-id", "recipient": to}

    async def send_slack_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a message to a Slack channel.

        Args:
            channel: Target Slack channel.
            text: Message text.
            blocks: Optional Slack Block Kit blocks.

        Returns:
            Dict with send result information.
        """
        if not self.is_connected("slack"):
            await self.connect("slack")
        return {"success": True, "channel": channel, "ts": "mock-timestamp"}

    async def notify_hr_system(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a notification to the HR system.

        Args:
            event_type: The type of HR event.
            payload: Event data payload.

        Returns:
            Dict with notification result.
        """
        if not self.is_connected("hr_system"):
            await self.connect("hr_system")
        return {"success": True, "event": event_type}
