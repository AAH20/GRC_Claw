"""
Notification engine for GRC_Claw — orchestrates delivery across channels.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .channels import BaseChannel, EmailChannel, SlackChannel, TeamsChannel, WebhookChannel
from .models import (
    ChannelConfig,
    DeliveryResult,
    Notification,
    NotificationStatus,
    RoutingRule,
)

logger = logging.getLogger(__name__)


class NotificationEngine:
    """
    Core notification engine that manages channels, routing, and delivery.

    Usage:
        engine = NotificationEngine()
        engine.register_channel(EmailChannel(config))
        engine.register_channel(SlackChannel(config))

        notification = Notification(
            title="Compliance Violation",
            body="Policy PCI-DSS-1.2 was violated",
            priority=NotificationPriority.HIGH,
            type=NotificationType.COMPLIANCE_VIOLATION,
            channels=["email", "slack"],
            recipients=["security@example.com"],
        )
        result = await engine.send(notification)
    """

    def __init__(self):
        self._channels: dict[str, BaseChannel] = {}
        self._routing_rules: list[RoutingRule] = []
        self._middleware: list[Callable] = []
        self._notification_history: list[Notification] = []
        self._max_history: int = 10_000
        self._dedup_cache: dict[str, str] = {}
        self._dedup_ttl_seconds: int = 300
        self._hooks: dict[str, list[Callable]] = defaultdict(list)

    # ─── Channel Management ──────────────────────────────────────────────────

    def register_channel(self, channel: BaseChannel) -> None:
        """Register a notification channel."""
        self._channels[channel.channel_name] = channel
        logger.info(f"Registered channel: {channel.channel_name}")

    def unregister_channel(self, name: str) -> None:
        """Remove a registered channel."""
        self._channels.pop(name, None)

    def get_channel(self, name: str) -> BaseChannel | None:
        """Get a registered channel by name."""
        return self._channels.get(name)

    @property
    def channels(self) -> dict[str, BaseChannel]:
        """Get all registered channels."""
        return dict(self._channels)

    # ─── Routing Rules ───────────────────────────────────────────────────────

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule. Rules are evaluated in priority order."""
        self._routing_rules.append(rule)
        self._routing_rules.sort(key=lambda r: r.priority)

    def remove_routing_rule(self, rule_id: str) -> None:
        """Remove a routing rule by ID."""
        self._routing_rules = [r for r in self._routing_rules if r.id != rule_id]

    # ─── Middleware ──────────────────────────────────────────────────────────

    def add_middleware(self, middleware: Callable) -> None:
        """Add a middleware function that processes notifications before delivery.

        Middleware signature: (notification: Notification) -> Notification
        Can modify or suppress notifications by returning None.
        """
        self._middleware.append(middleware)

    # ─── Hooks ───────────────────────────────────────────────────────────────

    def on(self, event: str, callback: Callable) -> None:
        """Register a hook for a specific event.

        Events: 'before_send', 'after_send', 'on_success', 'on_failure', 'on_retry'
        """
        self._hooks[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unregister a hook."""
        if callback in self._hooks[event]:
            self._hooks[event].remove(callback)

    async def _emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all registered hooks."""
        for callback in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")

    # ─── Core Delivery ───────────────────────────────────────────────────────

    async def send(self, notification: Notification) -> Notification:
        """
        Send a notification through all specified channels.

        Returns the updated notification with delivery results.
        """
        await self._emit("before_send", notification)

        # Apply middleware
        for mw in self._middleware:
            try:
                if asyncio.iscoroutinefunction(mw):
                    notification = await mw(notification)
                else:
                    notification = mw(notification)
                if notification is None:
                    notification.status = NotificationStatus.SUPPRESSED
                    return notification
            except Exception as e:
                logger.error(f"Middleware error: {e}")

        # Apply routing rules
        notification = self._apply_routing(notification)

        # Check for duplicates
        if self._is_duplicate(notification):
            notification.status = NotificationStatus.SUPPRESSED
            logger.info(f"Suppressed duplicate notification: {notification.id}")
            return notification

        # Determine channels and recipients
        channels_to_use = notification.channels or list(self._channels.keys())
        recipients = notification.recipients or [""]

        # Deliver to each channel
        tasks = []
        for channel_name in channels_to_use:
            channel = self._channels.get(channel_name)
            if channel is None:
                logger.warning(f"Channel not found: {channel_name}")
                notification.delivery_results.append(DeliveryResult(
                    channel=channel_name,
                    success=False,
                    error="Channel not registered",
                ))
                continue

            if not channel.should_deliver(notification):
                continue

            for recipient in recipients:
                tasks.append(self._deliver_with_retry(channel, notification, recipient))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    notification.delivery_results.append(DeliveryResult(
                        channel="unknown",
                        success=False,
                        error=str(result),
                    ))
                else:
                    notification.delivery_results.append(result)

        # Update status based on results
        notification.status = self._compute_status(notification.delivery_results)
        notification.delivered_at = datetime.now(UTC).isoformat()

        # Record in history
        self._record_notification(notification)

        # Emit post-send events
        await self._emit("after_send", notification)
        if notification.status == NotificationStatus.DELIVERED:
            await self._emit("on_success", notification)
        elif notification.status == NotificationStatus.FAILED:
            await self._emit("on_failure", notification)

        return notification

    async def send_batch(self, notifications: list[Notification]) -> list[Notification]:
        """Send multiple notifications concurrently."""
        tasks = [self.send(n) for n in notifications]
        return await asyncio.gather(*tasks)

    async def _deliver_with_retry(
        self,
        channel: BaseChannel,
        notification: Notification,
        recipient: str,
    ) -> DeliveryResult:
        """Deliver a notification with retry logic."""
        max_retries = notification.max_retries
        last_result = None

        for attempt in range(max_retries + 1):
            result = await channel.send(notification, recipient)
            result.retry_count = attempt

            if result.success:
                return result

            last_result = result
            notification.retry_count = attempt + 1

            if attempt < max_retries:
                delay = self._compute_backoff(attempt, channel.config.retry_policy)
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for {notification.id} "
                    f"on {channel.channel_name} after {delay:.1f}s"
                )
                await self._emit("on_retry", notification, result, attempt)
                await asyncio.sleep(delay)

        return last_result

    def _compute_backoff(self, attempt: int, retry_policy: dict[str, Any]) -> float:
        """Compute exponential backoff delay."""
        initial = retry_policy.get("initial_delay_seconds", 1.0)
        factor = retry_policy.get("backoff_factor", 2.0)
        return initial * (factor ** attempt)

    def _compute_status(self, results: list[DeliveryResult]) -> NotificationStatus:
        """Compute overall notification status from delivery results."""
        if not results:
            return NotificationStatus.FAILED

        successes = sum(1 for r in results if r.success)
        total = len(results)

        if successes == 0:
            return NotificationStatus.FAILED
        if successes == total:
            return NotificationStatus.DELIVERED
        return NotificationStatus.PARTIALLY_DELIVERED

    # ─── Routing ─────────────────────────────────────────────────────────────

    def _apply_routing(self, notification: Notification) -> Notification:
        """Apply routing rules to determine channels and recipients."""
        for rule in self._routing_rules:
            if not rule.enabled:
                continue
            if self._matches_rule(notification, rule):
                if rule.channels:
                    notification.channels = list(set(notification.channels + rule.channels))
                if rule.recipients:
                    notification.recipients = list(set(notification.recipients + rule.recipients))
                if rule.template_id and not notification.template_id:
                    notification.template_id = rule.template_id
        return notification

    def _matches_rule(self, notification: Notification, rule: RoutingRule) -> bool:
        """Check if a notification matches a routing rule's conditions."""
        conditions = rule.conditions
        if not conditions:
            return True

        for key, value in conditions.items():
            if key == "priority":
                if notification.priority.value not in (value if isinstance(value, list) else [value]):
                    return False
            elif key == "type":
                if notification.type.value not in (value if isinstance(value, list) else [value]):
                    return False
            elif key == "source":
                if notification.source != value:
                    return False
            elif key == "tags":
                tags = value if isinstance(value, list) else [value]
                if not any(t in notification.tags for t in tags):
                    return False
            elif key == "channels":
                if not any(c in notification.channels for c in (value if isinstance(value, list) else [value])):
                    return False
        return True

    # ─── Deduplication ───────────────────────────────────────────────────────

    def _is_duplicate(self, notification: Notification) -> bool:
        """Check if this notification is a duplicate of a recently sent one."""
        dedup_key = self._dedup_key(notification)
        if dedup_key in self._dedup_cache:
            return True
        self._dedup_cache[dedup_key] = notification.id
        # Simple cache cleanup
        if len(self._dedup_cache) > 1000:
            self._dedup_cache.clear()
        return False

    def _dedup_key(self, notification: Notification) -> str:
        """Generate a deduplication key for a notification."""
        parts = [
            notification.type.value,
            notification.source,
            notification.source_id,
            notification.title,
        ]
        return ":".join(parts)

    # ─── History ─────────────────────────────────────────────────────────────

    def _record_notification(self, notification: Notification) -> None:
        """Record a notification in the history buffer."""
        self._notification_history.append(notification)
        if len(self._notification_history) > self._max_history:
            self._notification_history = self._notification_history[-self._max_history:]

    @property
    def history(self) -> list[Notification]:
        """Get the notification history."""
        return list(self._notification_history)

    def get_recent(self, count: int = 100) -> list[Notification]:
        """Get the most recent notifications."""
        return self._notification_history[-count:]

    # ─── Health ──────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Check health of all registered channels."""
        results = {}
        for name, channel in self._channels.items():
            try:
                results[name] = await channel.health_check()
            except Exception as e:
                results[name] = {"channel": name, "healthy": False, "error": str(e)}
        return {
            "engine": "grc_claw_notification_engine",
            "channels": results,
            "total_channels": len(self._channels),
            "healthy_channels": sum(1 for r in results.values() if r.get("healthy", False)),
            "routing_rules": len(self._routing_rules),
            "middleware_count": len(self._middleware),
        }

    # ─── Factory ─────────────────────────────────────────────────────────────

    @classmethod
    def create_default(cls) -> NotificationEngine:
        """Create a pre-configured notification engine with all channels."""
        engine = cls()

        engine.register_channel(EmailChannel(ChannelConfig(
            channel="email",
            config={"from_address": "grc-claw@localhost", "smtp_host": "localhost"},
        )))
        engine.register_channel(SlackChannel(ChannelConfig(
            channel="slack",
            config={"default_channel": "#grc-alerts"},
        )))
        engine.register_channel(TeamsChannel(ChannelConfig(
            channel="teams",
            config={"default_channel": "General"},
        )))
        engine.register_channel(WebhookChannel(ChannelConfig(
            channel="webhook",
            config={"url": "http://localhost:8080/webhook"},
        )))

        return engine
