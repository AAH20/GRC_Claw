"""Notification service for moderation queue alerts."""

from __future__ import annotations

import structlog

from moderation_queue.config import Settings, get_settings

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for sending notifications about moderation events.

    Supports multiple notification channels including Slack, email,
    and webhooks for escalation and alerting.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the notification service.

        Args:
            settings: Application settings.
        """
        self.settings = settings or get_settings()

    async def send_escalation_alert(
        self,
        escalation_id: str,
        item_id: str,
        reason: str,
        priority: str,
        channels: list[str] | None = None,
    ) -> bool:
        """Send an escalation alert.

        Args:
            escalation_id: Escalation identifier.
            item_id: Item identifier.
            reason: Escalation reason.
            priority: Priority level.
            channels: Notification channels to use.

        Returns:
            bool: True if notification was sent successfully.
        """
        channels = channels or ["slack"]
        message = (
            f"🚨 Escalation Alert\n"
            f"ID: {escalation_id}\n"
            f"Item: {item_id}\n"
            f"Reason: {reason}\n"
            f"Priority: {priority}"
        )

        for channel in channels:
            await self._send_to_channel(channel, message)

        logger.info(
            "Escalation alert sent",
            escalation_id=escalation_id,
            channels=channels,
        )
        return True

    async def send_queue_alert(
        self,
        queue_id: str,
        alert_type: str,
        message: str,
        channels: list[str] | None = None,
    ) -> bool:
        """Send a queue-related alert.

        Args:
            queue_id: Queue identifier.
            alert_type: Type of alert.
            message: Alert message.
            channels: Notification channels.

        Returns:
            bool: True if notification was sent successfully.
        """
        channels = channels = channels or ["slack"]
        formatted = f"📋 Queue Alert [{alert_type}]\nQueue: {queue_id}\n{message}"

        for channel in channels:
            await self._send_to_channel(channel, formatted)

        logger.info("Queue alert sent", queue_id=queue_id, alert_type=alert_type)
        return True

    async def send_review_reminder(
        self,
        item_id: str,
        reviewer_id: str,
        age_hours: float,
    ) -> bool:
        """Send a review reminder.

        Args:
            item_id: Item identifier.
            reviewer_id: Reviewer identifier.
            age_hours: Age of the item in hours.

        Returns:
            bool: True if notification was sent successfully.
        """
        message = (
            f"⏰ Review Reminder\n"
            f"Item: {item_id}\n"
            f"Reviewer: {reviewer_id}\n"
            f"Age: {age_hours:.1f} hours"
        )
        await self._send_to_channel("email", message)
        logger.info("Review reminder sent", item_id=item_id)
        return True

    async def _send_to_channel(self, channel: str, message: str) -> None:
        """Send a message to a specific channel.

        Args:
            channel: Channel name.
            message: Message content.
        """
        # In production, this would integrate with Slack, email, etc.
        logger.debug("Sending notification", channel=channel, message=message[:100])
