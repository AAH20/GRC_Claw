"""Amplitude analytics integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class AmplitudeClient:
    """Client for Amplitude analytics API integration.

    Handles event tracking, user identification, and cohort
    management through the Amplitude platform.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the Amplitude client.

        Args:
            api_key: Amplitude API key.
        """
        self.api_key = api_key
        self.base_url = "https://api2.amplitude.com"
        self.logger = logger.bind(integration="amplitude")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def track_event(
        self,
        user_id: str,
        event_type: str,
        event_properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Track an event in Amplitude.

        Args:
            user_id: The user ID.
            event_type: The event type.
            event_properties: Optional event properties.

        Returns:
            The API response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/2/httpapi"
        payload = {
            "api_key": self.api_key,
            "events": [
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    "event_properties": event_properties or {},
                }
            ],
        }
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            self.logger.info("Event tracked", user_id=user_id, event_type=event_type)
            return {"success": True, "code": 200}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def identify_user(
        self,
        user_id: str,
        user_properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Identify a user in Amplitude.

        Args:
            user_id: The user ID.
            user_properties: Optional user properties.

        Returns:
            The API response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/identify"
        payload = {
            "api_key": self.api_key,
            "identification": {
                "user_id": user_id,
                "user_properties": user_properties or {},
            },
        }
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            self.logger.info("User identified", user_id=user_id)
            return {"success": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_user_activity(self, user_id: str) -> dict[str, Any]:
        """Get user activity from Amplitude.

        Args:
            user_id: The user ID.

        Returns:
            The user activity data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}/useractivity"
        params = {"user_id": user_id}
        headers = {"Authorization": f"Basic {self.api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
