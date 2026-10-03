"""Glassdoor integration for employer branding."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class GlassdoorIntegration(BaseIntegration):
    """Integration with Glassdoor for employer branding.

    Monitors and manages company presence on Glassdoor.
    """

    def __init__(
        self, api_key: str, base_url: str = "https://api.glassdoor.com"
    ) -> None:
        """Initialize the Glassdoor integration.

        Args:
            api_key: API key for Glassdoor.
            base_url: Base URL for the API.
        """
        super().__init__(base_url=base_url, api_key=api_key)

    async def get_company_profile(self, company_id: str) -> dict[str, Any]:
        """Get company profile from Glassdoor.

        Args:
            company_id: Company identifier.

        Returns:
            Company profile data.
        """
        response = await self.get(f"/companies/{company_id}")
        return response.json()

    async def get_reviews(self, company_id: str) -> list[dict[str, Any]]:
        """Get company reviews.

        Args:
            company_id: Company identifier.

        Returns:
            List of reviews.
        """
        response = await self.get(f"/companies/{company_id}/reviews")
        return response.json().get("reviews", [])

    async def get_rating(self, company_id: str) -> dict[str, Any]:
        """Get company rating.

        Args:
            company_id: Company identifier.

        Returns:
            Rating data.
        """
        response = await self.get(f"/companies/{company_id}/rating")
        return response.json()

    async def health_check(self) -> bool:
        """Check if the Glassdoor API is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
