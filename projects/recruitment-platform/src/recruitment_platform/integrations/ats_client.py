"""Applicant Tracking System (ATS) client integration."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class ATSClient(BaseIntegration):
    """Client for interacting with Applicant Tracking Systems.

    Syncs candidate data, job postings, and application
    status with external ATS platforms.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize the ATS client.

        Args:
            base_url: Base URL for the ATS API.
            api_key: API key for authentication.
        """
        super().__init__(base_url=base_url, api_key=api_key)

    async def get_candidates(self, status: str = "") -> list[dict[str, Any]]:
        """Get candidates from the ATS.

        Args:
            status: Optional status filter.

        Returns:
            List of candidate records.
        """
        params = {"status": status} if status else {}
        response = await self.get("/candidates", params=params)
        return response.json().get("candidates", [])

    async def update_candidate(self, candidate_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a candidate record.

        Args:
            candidate_id: Candidate identifier.
            data: Updated candidate data.

        Returns:
            Updated candidate record.
        """
        response = await self.put(f"/candidates/{candidate_id}", json=data)
        return response.json()

    async def get_jobs(self) -> list[dict[str, Any]]:
        """Get job postings from the ATS.

        Returns:
            List of job records.
        """
        response = await self.get("/jobs")
        return response.json().get("jobs", [])

    async def create_application(self, application_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new application record.

        Args:
            application_data: Application details.

        Returns:
            Created application record.
        """
        response = await self.post("/applications", json=application_data)
        return response.json()

    async def health_check(self) -> bool:
        """Check if the ATS is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
