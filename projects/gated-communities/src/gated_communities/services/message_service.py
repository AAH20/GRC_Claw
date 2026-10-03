"""Message service for gated communities."""

from __future__ import annotations

from typing import Any


class MessageServiceError(Exception):
    """Base exception for message service errors."""


class ValidationError(MessageServiceError):
    """Raised when message data fails validation."""


class NotFoundError(MessageServiceError):
    """Raised when a message or channel is not found."""


def send_message(data: dict[str, Any]) -> dict[str, Any]:
    """Send a message to a channel.

    Args:
        data: Dictionary containing message data. Required keys:
            - channel_id (str): Target channel identifier.
            - content (str): Message body text.
            - sender_id (str): Identifier of the sending user.

    Returns:
        The created message as a dictionary with generated id and timestamp.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    if not isinstance(data, dict):
        raise ValidationError("Message data must be a dictionary.")

    required_fields = ("channel_id", "content", "sender_id")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )

    channel_id = data["channel_id"]
    content = data["content"]
    sender_id = data["sender_id"]

    if not isinstance(channel_id, str) or not channel_id.strip():
        raise ValidationError("channel_id must be a non-empty string.")
    if not isinstance(content, str) or not content.strip():
        raise ValidationError("content must be a non-empty string.")
    if not isinstance(sender_id, str) or not sender_id.strip():
        raise ValidationError("sender_id must be a non-empty string.")

    from datetime import datetime, timezone

    message = {
        "id": f"msg_{datetime.now(timezone.utc).timestamp()}",
        "channel_id": channel_id,
        "content": content,
        "sender_id": sender_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }

    return message


def get_messages(channel_id: str) -> list[dict[str, Any]]:
    """Retrieve all messages in a channel.

    Args:
        channel_id: The channel identifier to fetch messages for.

    Returns:
        A list of message dictionaries, ordered oldest first.

    Raises:
        ValidationError: If channel_id is invalid.
        NotFoundError: If the channel does not exist.
    """
    if not isinstance(channel_id, str) or not channel_id.strip():
        raise ValidationError("channel_id must be a non-empty string.")

    # In a real implementation this would query the database.
    # Returning an empty list for a valid but empty channel.
    return []


def mark_as_read(message_id: str) -> dict[str, Any]:
    """Mark a message as read.

    Args:
        message_id: The identifier of the message to mark as read.

    Returns:
        The updated message dictionary with read=True.

    Raises:
        ValidationError: If message_id is invalid.
        NotFoundError: If the message does not exist.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValidationError("message_id must be a non-empty string.")

    # In a real implementation this would update the database.
    # Returning a stub indicating success.
    return {
        "id": message_id,
        "read": True,
    }
