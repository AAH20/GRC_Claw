"""Zapier integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from workflow_automation.config import get_settings

logger = structlog.get_logger(__name__)


class ZapierZap(BaseModel):
    """Represents a Zapier Zap."""

    id: str
    title: str
    status: str = "on"
    url: str = ""
    created_at: str = ""
    updated_at: str = ""


class ZapierWebhookPayload(BaseModel):
    """Payload sent to a Zapier webhook."""

    event: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


class ZapierClient:
    """Client for interacting with Zapier webhooks and the Zapier Platform API.

    Provides methods to trigger webhooks, manage Zaps, and handle
    Zapier platform operations.
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        api_key: str | None = None,
        base_url: str = "https://hooks.zapier.com",
    ) -> None:
        """Initialize the Zapier client.

        Args:
            webhook_url: The Zapier webhook URL. If None, loads from settings.
            api_key: Zapier Platform API key.
            base_url: Base URL for Zapier webhooks.
        """
        settings = get_settings()
        self._webhook_url = webhook_url or settings.zapier_webhook_url
        self._api_key = api_key or ""
        self._base_url = base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the Zapier webhook is reachable.

        Returns:
            True if the webhook URL is configured and reachable.
        """
        if not self._webhook_url:
            logger.warning("Zapier webhook URL not configured")
            return False

        try:
            response = await self._client.get(self._webhook_url)
            return response.status_code < 500
        except Exception as e:
            logger.error("Zapier health check failed", error=str(e))
            return False

    async def trigger_webhook(
        self, event: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Trigger a Zapier webhook.

        Args:
            event: The event type/name.
            data: Data payload to send.

        Returns:
            Webhook response data.

        Raises:
            ValueError: If webhook URL is not configured.
            httpx.HTTPError: If the request fails.
        """
        if not self._webhook_url:
            raise ValueError("Zapier webhook URL not configured")

        payload = ZapierWebhookPayload(
            event=event,
            data=data or {},
        )

        logger.info("Triggering Zapier webhook", event_name=event)

        response = await self._client.post(
            self._webhook_url, json=payload.model_dump()
        )
        response.raise_for_status()

        return {
            "status_code": response.status_code,
            "event": event,
            "success": response.status_code < 300,
        }

    async def trigger_catch_hook(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Trigger a Zapier Catch Hook.

        Args:
            data: Data payload to send.

        Returns:
            Webhook response data.

        Raises:
            ValueError: If webhook URL is not configured.
            httpx.HTTPError: If the request fails.
        """
        if not self._webhook_url:
            raise ValueError("Zapier webhook URL not configured")

        logger.info("Triggering Zapier Catch Hook")

        response = await self._client.post(self._webhook_url, json=data)
        response.raise_for_status()

        return {
            "status_code": response.status_code,
            "success": response.status_code < 300,
        }

    async def list_zaps(self) -> list[ZapierZap]:
        """List Zaps from the Zapier Platform API.

        Returns:
            List of Zaps.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If the API request fails.
        """
        if not self._api_key:
            raise ValueError("Zapier API key not configured")

        response = await self._client.get(
            "https://api.zapier.com/api/v1/zaps",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return [ZapierZap(**zap) for zap in data]

    async def get_zap(self, zap_id: str) -> ZapierZap:
        """Get a specific Zap by ID.

        Args:
            zap_id: The Zap identifier.

        Returns:
            The Zap details.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If the API request fails.
        """
        if not self._api_key:
            raise ValueError("Zapier API key not configured")

        response = await self._client.get(
            f"https://api.zapier.com/api/v1/zaps/{zap_id}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        return ZapierZap(**response.json())

    async def toggle_zap(self, zap_id: str, turn_on: bool) -> ZapierZap:
        """Turn a Zap on or off.

        Args:
            zap_id: The Zap identifier.
            turn_on: True to turn on, False to turn off.

        Returns:
            The updated Zap.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If the API request fails.
        """
        if not self._api_key:
            raise ValueError("Zapier API key not configured")

        response = await self._client.patch(
            f"https://api.zapier.com/api/v1/zaps/{zap_id}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"status": "on" if turn_on else "off"},
        )
        response.raise_for_status()
        return ZapierZap(**response.json())
