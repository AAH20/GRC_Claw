"""LinkedIn API integration client."""

from __future__ import annotations

from typing import Any

import structlog

from employer_branding.integrations.base import BaseReviewClient

logger = structlog.get_logger(__name__)


class LinkedInClient(BaseReviewClient):
    """Client for interacting with the LinkedIn API."""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize LinkedIn client.

        Args:
            api_key: LinkedIn API key. Uses settings if not provided.
        """
        super().__init__(api_key or self._settings.linkedin_api_key)
        self._base_url = self.BASE_URL

    async def fetch_reviews(
        self, company_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch reviews from LinkedIn.

        Args:
            company_name: Company name to search.
            limit: Maximum number of reviews.

        Returns:
            List of raw review dictionaries.

        Raises:
            ValueError: If API key is not configured.
        """
        if not self._api_key:
            raise ValueError("LinkedIn API key is not configured")

        self._logger.info("fetching_linkedin_reviews", company=company_name, limit=limit)

        # Mock response for demonstration
        return [
            {
                "id": f"li_{i}",
                "rating": 4.5,
                "title": "Excellent employer",
                "content": "Great career opportunities and learning culture.",
                "pros": "Career growth, learning budget",
                "cons": "Fast-paced environment",
                "date": "2024-01-20",
            }
            for i in range(min(limit, 5))
        ]

    async def get_company_info(self, company_name: str) -> dict[str, Any]:
        """Get company information from LinkedIn.

        Args:
            company_name: Company name to search.

        Returns:
            Dictionary with company information.
        """
        if not self._api_key:
            raise ValueError("LinkedIn API key is not configured")

        self._logger.info("fetching_linkedin_company_info", company=company_name)

        return {
            "name": company_name,
            "followers": 50000,
            "employee_count": 5000,
            "industry": "Technology",
        }
