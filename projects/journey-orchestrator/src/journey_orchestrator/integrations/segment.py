"""Segment CDP integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SegmentClient:
    """Client for Segment CDP API integration.

    Handles user identification, event tracking, and segment
    management through the Segment platform.
    """

    def __init__(self, write_key: str) -> None:
        """Initialize the Segment client.

        Args:
            write_key: Segment write key.
        """
        self.write_key = write_key
        self.base_url = "https://api.segment.io/v1"
        self.logger = logger.bind(integration="segment")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def identify(self, user_id: str, traits: dict[str, Any] | None = None) -> dict[str, Any]:
        """Identify a user in Segment.

        Args:
            user_id: The user ID.
            traits: Optional user traits.

        Returns:
            The API response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/identify"
        payload = {
            "userId": user_id,
            "traits": traits or {},
        }
        headers = {"Content-Type": "application/json"}
        auth = (self.write_key, "")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, auth=auth)
            response.raise_for_status()
            self.logger.info("User identified", user_id=user_id)
            return {"success": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def track(
        self,
        user_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Track an event in Segment.

        Args:
            user_id: The user ID.
            event: The event name.
            properties: Optional event properties.

        Returns:
            The API response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/track"
        payload = {
            "userId": user_id,
            "event": event,
            "properties": properties or {},
        }
        headers = {"Content-Type": "application/json"}
        auth = (self.write_key, "")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, auth=auth)
            response.raise_for_status()
            self.logger.info("Event tracked", user_id=user_id, event=event)
            return {"success": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get a user profile from Segment.

        Args:
            user_id: The user ID.

        Returns:
            The user profile data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/users/{user_id}"
        auth = (self.write_key, "")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            return response.json()
