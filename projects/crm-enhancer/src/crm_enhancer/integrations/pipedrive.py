"""Pipedrive integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class PipedriveError(Exception):
    """Pipedrive API error."""


class PipedriveClient:
    """Client for Pipedrive API integration.

    Provides methods to interact with Pipedrive CRM including
    person management, deal tracking, and activity data.
    """

    def __init__(self, api_token: str, company_domain: str = "") -> None:
        """Initialize Pipedrive client.

        Args:
            api_token: Pipedrive API token.
            company_domain: Pipedrive company domain.
        """
        self.api_token = api_token
        self.company_domain = company_domain
        self._base_url = f"https://{company_domain}.pipedrive.com/api/v1" if company_domain else "https://api.pipedrive.com/api/v1"
        self._rate_limit = 5  # requests per second

        logger.info("PipedriveClient initialized")

    def _get_params(self) -> dict[str, str]:
        """Get request parameters with authentication."""
        return {"api_token": self.api_token}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_persons(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get persons from Pipedrive.

        Args:
            limit: Maximum number of persons to retrieve.

        Returns:
            List of person records.
        """
        logger.info("Fetching persons from Pipedrive", limit=limit)

        url = f"{self._base_url}/persons"
        params = {**self._get_params(), "limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        persons = data.get("data", [])
        logger.info("Persons fetched", count=len(persons))
        return persons

    async def get_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get deals from Pipedrive.

        Args:
            limit: Maximum number of deals to retrieve.

        Returns:
            List of deal records.
        """
        logger.info("Fetching deals from Pipedrive", limit=limit)

        url = f"{self._base_url}/deals"
        params = {**self._get_params(), "limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        deals = data.get("data", [])
        logger.info("Deals fetched", count=len(deals))
        return deals

    async def create_person(self, person_data: dict[str, Any]) -> dict[str, Any]:
        """Create a person in Pipedrive.

        Args:
            person_data: Person data to create.

        Returns:
            Created person record.
        """
        logger.info("Creating person in Pipedrive")

        url = f"{self._base_url}/persons"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params=self._get_params(),
                json=person_data,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def update_person(self, person_id: int, person_data: dict[str, Any]) -> dict[str, Any]:
        """Update a person in Pipedrive.

        Args:
            person_id: Person ID to update.
            person_data: Data to update.

        Returns:
            Updated person record.
        """
        logger.info("Updating person", person_id=person_id)

        url = f"{self._base_url}/persons/{person_id}"

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                params=self._get_params(),
                json=person_data,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_activities(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get activities from Pipedrive.

        Args:
            limit: Maximum number of activities to retrieve.

        Returns:
            List of activity records.
        """
        logger.info("Fetching activities from Pipedrive", limit=limit)

        url = f"{self._base_url}/activities"
        params = {**self._get_params(), "limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        activities = data.get("data", [])
        logger.info("Activities fetched", count=len(activities))
        return activities

    async def create_activity(self, activity_data: dict[str, Any]) -> dict[str, Any]:
        """Create an activity in Pipedrive.

        Args:
            activity_data: Activity data to create.

        Returns:
            Created activity record.
        """
        logger.info("Creating activity in Pipedrive")

        url = f"{self._base_url}/activities"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params=self._get_params(),
                json=activity_data,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check Pipedrive API connectivity.

        Returns:
            True if connection is healthy.
        """
        try:
            url = f"{self._base_url}/users"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=self._get_params(),
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as exc:
            logger.error("Pipedrive health check failed", error=str(exc))
            return False
