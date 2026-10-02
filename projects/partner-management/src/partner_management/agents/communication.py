"""Communication agent for partner communications and notifications."""

from __future__ import annotations

import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Channel(StrEnum):
    """Communication channels."""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class MessagePriority(StrEnum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(StrEnum):
    """Message delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class PartnerMessage(BaseModel):
    """Partner message data model."""

    id: str = Field(..., description="Unique message identifier")
    partner_id: str = Field(..., description="Target partner ID")
    channel: Channel
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationAgent:
    """Agent responsible for partner communications.

    Handles multi-channel message delivery, templating,
    and notification management.
    """

    def __init__(self) -> None:
        """Initialize the communication agent."""
        self._messages: dict[str, PartnerMessage] = {}
        self._templates: dict[str, str] = {}
        logger.info("CommunicationAgent initialized")

    async def send_message(self, message: PartnerMessage) -> PartnerMessage:
        """Send a message to a partner.

        Args:
            message: The message to send.

        Returns:
            The sent message with updated status.

        Raises:
            ValueError: If a message with the same ID already exists.
        """
        if message.id in self._messages:
            raise ValueError(f"Message with ID '{message.id}' already exists")

        message.status = MessageStatus.SENT
        message.sent_at = datetime.utcnow()
        self._messages[message.id] = message
        logger.info(
            "Message %s sent to partner %s via %s",
            message.id,
            message.partner_id,
            message.channel,
        )
        return message

    async def register_template(self, name: str, template: str) -> None:
        """Register a message template.

        Args:
            name: Template name.
            template: Template body with placeholders.
        """
        self._templates[name] = template
        logger.info("Template '%s' registered", name)

    async def send_templated(
        self,
        message_id: str,
        partner_id: str,
        channel: Channel,
        template_name: str,
        variables: dict[str, str],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> PartnerMessage:
        """Send a message using a registered template.

        Args:
            message_id: Unique message ID.
            partner_id: Target partner.
            channel: Communication channel.
            template_name: Name of the registered template.
            variables: Template variable substitutions.
            priority: Message priority.

        Returns:
            The sent message.

        Raises:
            KeyError: If the template is not found.
        """
        if template_name not in self._templates:
            raise KeyError(f"Template '{template_name}' not found")

        template = self._templates[template_name]
        body = template.format(**variables)
        subject = variables.get("subject", "Notification")

        message = PartnerMessage(
            id=message_id,
            partner_id=partner_id,
            channel=channel,
            subject=subject,
            body=body,
            priority=priority,
        )
        return await self.send_message(message)

    async def get_message(self, message_id: str) -> PartnerMessage | None:
        """Get a message by ID.

        Args:
            message_id: The message ID to look up.

        Returns:
            The message or None if not found.
        """
        return self._messages.get(message_id)

    async def list_messages(
        self,
        partner_id: str | None = None,
        channel: Channel | None = None,
        status: MessageStatus | None = None,
    ) -> list[PartnerMessage]:
        """List messages with optional filtering.

        Args:
            partner_id: Filter by partner.
            channel: Filter by channel.
            status: Filter by status.

        Returns:
            List of matching messages.
        """
        messages = list(self._messages.values())
        if partner_id:
            messages = [m for m in messages if m.partner_id == partner_id]
        if channel:
            messages = [m for m in messages if m.channel == channel]
        if status:
            messages = [m for m in messages if m.status == status]
        return messages

    async def mark_delivered(self, message_id: str) -> PartnerMessage:
        """Mark a message as delivered.

        Args:
            message_id: The message to update.

        Returns:
            The updated message.

        Raises:
            KeyError: If the message is not found.
        """
        if message_id not in self._messages:
            raise KeyError(f"Message '{message_id}' not found")

        message = self._messages[message_id]
        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.utcnow()
        logger.info("Message %s marked as delivered", message_id)
        return message
