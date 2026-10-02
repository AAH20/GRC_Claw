"""Notification service for escalation alerts."""

from __future__ import annotations

import structlog
from abc import ABC, abstractmethod
from typing import Any

import httpx

from escalation_workflow.config import Settings

logger = structlog.get_logger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, message: str, **kwargs: Any) -> bool:
        """Send a notification.

        Args:
            message: The notification message.
            **kwargs: Additional channel-specific parameters.

        Returns:
            bool: True if sent successfully.
        """
        ...


class NotificationService:
    """Service for managing and dispatching notifications across channels."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the notification service.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.channels: dict[str, NotificationChannel] = {}
        self.logger = logger.bind(service="notification")

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel.

        Args:
            name: Channel identifier.
            channel: The notification channel implementation.
        """
        self.channels[name] = channel

    async def notify(
        self,
        message: str,
        channels: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, bool]:
        """Send notification to specified channels.

        Args:
            message: The notification message.
            channels: List of channel names. If None, sends to all registered.
            **kwargs: Additional parameters passed to channels.

        Returns:
            dict[str, bool]: Success status per channel.
        """
        target_channels = channels or list(self.channels.keys())
        results: dict[str, bool] = {}

        for channel_name in target_channels:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    results[channel_name] = await channel.send(message, **kwargs)
                except Exception as exc:
                    self.logger.error(
                        "Notification failed",
                        channel=channel_name,
                        error=str(exc),
                    )
                    results[channel_name] = False
            else:
                self.logger.warning("Channel not found", channel=channel_name)
                results[channel_name] = False

        return results
