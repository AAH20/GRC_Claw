"""Webhook delivery service with retry logic and signature verification."""

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from structlog import get_logger

from app.core.config import get_settings
from app.core.security import compute_webhook_signature

logger = get_logger()
settings = get_settings()


@dataclass
class DeliveryResult:
    """Result of a webhook delivery attempt."""

    success: bool
    status_code: int | None = None
    response_time_ms: float = 0.0
    error: str | None = None
    attempts: int = 0


@dataclass
class WebhookDeliveryService:
    """Service for delivering webhooks with retry logic."""

    max_retries: int = 6
    retry_delays: list[int] = field(default_factory=lambda: [0, 60, 300, 1800, 7200, 28800])
    timeout_seconds: int = 10
    timestamp_tolerance: int = 300

    def __post_init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
                follow_redirects=False,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _compute_signature(self, secret: str, timestamp: str, payload: str) -> str:
        """Compute HMAC-SHA256 signature."""
        return compute_webhook_signature(secret, timestamp, payload)

    def _should_retry(self, status_code: int) -> bool:
        """Determine if a failed delivery should be retried."""
        if status_code >= 500:
            return True
        if status_code == 429:
            return True
        return False

    async def deliver(
        self,
        url: str,
        secret: str,
        event_type: str,
        event_id: str,
        data: dict[str, Any],
        tenant_id: str,
        subscription_id: str,
        attempt: int = 1,
    ) -> DeliveryResult:
        """Deliver a webhook with retry logic."""
        timestamp = str(int(time.time()))
        payload = json.dumps({
            "webhook_id": f"wh-{event_id}",
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "data": data,
            "metadata": {
                "delivery_attempt": attempt,
                "subscription_id": subscription_id,
            },
        }, default=str)

        signature = self._compute_signature(secret, timestamp, payload)

        headers = {
            "Content-Type": "application/json",
            "X-GRC-Signature": f"t={timestamp},v1={signature}",
            "X-GRC-Event-ID": event_id,
            "X-GRC-Event-Type": event_type,
            "X-GRC-Tenant-ID": tenant_id,
            "User-Agent": "GRC_Claw-Webhook/1.0",
        }

        start_time = time.monotonic()

        try:
            client = await self._get_client()
            response = await client.post(url, content=payload, headers=headers)
            elapsed_ms = (time.monotonic() - start_time) * 1000

            success = 200 <= response.status_code < 300

            if not success:
                logger.warning(
                    "webhook_delivery_failed",
                    url=url,
                    event_type=event_type,
                    event_id=event_id,
                    status_code=response.status_code,
                    attempt=attempt,
                )

            return DeliveryResult(
                success=success,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                error=None if success else f"HTTP {response.status_code}",
                attempts=attempt,
            )

        except httpx.TimeoutException:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "webhook_delivery_timeout",
                url=url,
                event_type=event_type,
                event_id=event_id,
                attempt=attempt,
            )
            return DeliveryResult(
                success=False,
                response_time_ms=elapsed_ms,
                error="Timeout",
                attempts=attempt,
            )

        except httpx.RequestError as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "webhook_delivery_error",
                url=url,
                event_type=event_type,
                event_id=event_id,
                error=str(e),
                attempt=attempt,
            )
            return DeliveryResult(
                success=False,
                response_time_ms=elapsed_ms,
                error=str(e),
                attempts=attempt,
            )

    async def deliver_with_retry(
        self,
        url: str,
        secret: str,
        event_type: str,
        event_id: str,
        data: dict[str, Any],
        tenant_id: str,
        subscription_id: str,
    ) -> DeliveryResult:
        """Deliver a webhook with automatic retry."""
        last_result = None

        for attempt in range(1, self.max_retries + 1):
            result = await self.deliver(
                url=url,
                secret=secret,
                event_type=event_type,
                event_id=event_id,
                data=data,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                attempt=attempt,
            )

            if result.success:
                return result

            last_result = result

            # Check if we should retry
            if result.status_code and not self._should_retry(result.status_code):
                logger.info(
                    "webhook_non_retryable_failure",
                    url=url,
                    event_type=event_type,
                    status_code=result.status_code,
                )
                return result

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                logger.info(
                    "webhook_retry_scheduled",
                    url=url,
                    event_type=event_type,
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    delay_seconds=delay,
                )
                await asyncio.sleep(delay)

        return last_result or DeliveryResult(success=False, error="Max retries exceeded")

    async def verify_signature(
        self,
        payload_body: str,
        signature_header: str,
        secret: str,
    ) -> bool:
        """Verify a webhook signature from an incoming request."""
        try:
            parts = signature_header.split(",")
            timestamp = None
            signature = None

            for part in parts:
                key, value = part.split("=", 1)
                if key == "t":
                    timestamp = value
                elif key == "v1":
                    signature = value

            if not timestamp or not signature:
                return False

            # Check timestamp tolerance
            ts = int(timestamp)
            now = int(time.time())
            if abs(now - ts) > self.timestamp_tolerance:
                return False

            # Verify signature
            signed_payload = f"{timestamp}.{payload_body}"
            expected = hmac.new(
                secret.encode(),
                signed_payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected)

        except (ValueError, IndexError):
            return False


# Singleton instance
webhook_delivery_service = WebhookDeliveryService()
