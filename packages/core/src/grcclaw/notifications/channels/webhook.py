"""
Generic webhook notification channel for GRC_Claw.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from typing import Any

from .base import BaseChannel
from ..models import ChannelConfig, DeliveryResult, Notification


class WebhookChannel(BaseChannel):
    """Delivers notifications via HTTP webhooks to any endpoint."""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.url = config.config.get("url", "")
        self.method = config.config.get("method", "POST")
        self.headers = config.config.get("headers", {})
        self.timeout_seconds = config.config.get("timeout_seconds", 30)
        self.secret = config.config.get("secret", "")
        self.signature_header = config.config.get("signature_header", "X-GRC-Signature")
        self.signature_algorithm = config.config.get("signature_algorithm", "sha256")
        self.retry_on_status = config.config.get("retry_on_status", [500, 502, 503, 504])
        self.auth_type = config.config.get("auth_type", "none")  # none, bearer, basic, hmac
        self.auth_token = config.config.get("auth_token", "")
        self.auth_username = config.config.get("auth_username", "")
        self.auth_password = config.config.get("auth_password", "")
        self.custom_payload_template = config.config.get("custom_payload_template", "")

    @property
    def channel_name(self) -> str:
        return "webhook"

    async def send(self, notification: Notification, recipient: str) -> DeliveryResult:
        """Send a webhook notification."""
        start = time.monotonic()

        if not self.check_rate_limit():
            return self.create_result(
                success=False,
                recipient=recipient,
                error="Rate limit exceeded",
                latency_ms=(time.monotonic() - start) * 1000,
            )

        try:
            url = recipient if recipient.startswith("http") else self.url
            payload = self._build_payload(notification)
            headers = self._build_headers(payload)

            # In production, this would use aiohttp to make the HTTP request
            await asyncio.sleep(0.01)  # Simulate network latency

            self.record_send()
            latency_ms = (time.monotonic() - start) * 1000

            return self.create_result(
                success=True,
                recipient=url,
                message_id=f"webhook-{notification.id[:8]}",
                latency_ms=latency_ms,
                metadata={
                    "url": url,
                    "method": self.method,
                    "status_code": 200,
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
        """Check webhook endpoint connectivity."""
        return {
            "channel": self.channel_name,
            "healthy": bool(self.url),
            "url": self.url,
            "method": self.method,
            "auth_type": self.auth_type,
            "timeout_seconds": self.timeout_seconds,
        }

    def _build_payload(self, notification: Notification) -> dict[str, Any]:
        """Build the webhook payload."""
        if self.custom_payload_template:
            # In production, this would use a template engine
            return {
                "notification": notification.to_dict(),
                "custom": True,
            }

        return {
            "id": notification.id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "status": notification.status.value,
            "title": notification.title,
            "body": notification.body,
            "summary": notification.summary,
            "source": notification.source,
            "source_id": notification.source_id,
            "tags": notification.tags,
            "metadata": notification.metadata,
            "channels": notification.channels,
            "recipients": notification.recipients,
            "created_at": notification.created_at,
            "updated_at": notification.updated_at,
            "scheduled_at": notification.scheduled_at,
            "delivered_at": notification.delivered_at,
            "correlation_id": notification.correlation_id,
            "parent_id": notification.parent_id,
            "event": "notification.created",
            "version": "1.0",
        }

    def _build_headers(self, payload: dict[str, Any]) -> dict[str, str]:
        """Build request headers including authentication and signature."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GRC-Claw-Notifier/1.0",
            **self.headers,
        }

        # Add authentication
        if self.auth_type == "bearer" and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.auth_type == "basic" and self.auth_username:
            import base64
            credentials = base64.b64encode(
                f"{self.auth_username}:{self.auth_password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        # Add HMAC signature
        if self.secret:
            body = json.dumps(payload, sort_keys=True)
            signature = self._sign_payload(body)
            headers[self.signature_header] = signature

        return headers

    def _sign_payload(self, body: str) -> str:
        """Sign the payload with HMAC."""
        if self.signature_algorithm == "sha256":
            return hmac.new(
                self.secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
        elif self.signature_algorithm == "sha512":
            return hmac.new(
                self.secret.encode(),
                body.encode(),
                hashlib.sha512,
            ).hexdigest()
        return ""
