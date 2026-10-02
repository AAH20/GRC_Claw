"""
Base channel interface for notification delivery.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from ..models import ChannelConfig, DeliveryResult, Notification, NotificationStatus


class BaseChannel(ABC):
    """Abstract base class for all notification channels."""

    def __init__(self, config: ChannelConfig):
        self.config = config
        self._rate_limit_timestamps: list[float] = []

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the unique name of this channel."""
        ...

    @abstractmethod
    async def send(self, notification: Notification, recipient: str) -> DeliveryResult:
        """Deliver a notification to a recipient through this channel."""
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check if the channel is healthy and configured correctly."""
        ...

    def check_rate_limit(self) -> bool:
        """Check if sending would exceed the configured rate limit."""
        now = time.time()
        window_start = now - 60.0
        self._rate_limit_timestamps = [
            ts for ts in self._rate_limit_timestamps if ts > window_start
        ]
        return len(self._rate_limit_timestamps) < self.config.rate_limit_per_minute

    def record_send(self):
        """Record a send attempt for rate limiting."""
        self._rate_limit_timestamps.append(time.time())

    def should_deliver(self, notification: Notification) -> bool:
        """Check if this channel should deliver the given notification."""
        if not self.config.enabled:
            return False

        if self.config.priority_filter:
            from ..models import NotificationPriority
            if notification.priority not in self.config.priority_filter:
                return False

        if self.config.type_filter:
            from ..models import NotificationType
            if notification.type not in self.config.type_filter:
                return False

        if self.config.tag_filter:
            if not any(tag in notification.tags for tag in self.config.tag_filter):
                return False

        return True

    def create_result(
        self,
        success: bool,
        recipient: str,
        message_id: str | None = None,
        error: str | None = None,
        latency_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> DeliveryResult:
        """Create a standardized delivery result."""
        return DeliveryResult(
            channel=self.channel_name,
            success=success,
            status=NotificationStatus.DELIVERED if success else NotificationStatus.FAILED,
            recipient=recipient,
            message_id=message_id,
            error=error,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )
