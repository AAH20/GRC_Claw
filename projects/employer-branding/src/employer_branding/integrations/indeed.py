"""Indeed API integration client."""

from __future__ import annotations

from typing import Any

import structlog

from employer_branding.integrations.base import BaseReviewClient

logger = structlog.get_logger(__name__)


class IndeedClient(BaseReviewClient):
    """Client for interacting with the Indeed API."""

    BASE_URL = "https://api.indeed.com/v2"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Indeed client.

        Args:
            api_key: Indeed API key. Uses settings if not provided.
        """
        super().__init__(api_key or self._settings.indeed_api_key)
        self._base_url = self.BASE_URL

    async def fetch_reviews(
        self, company_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch reviews from Indeed.

        Args:
            company_name: Company name to search.
            limit: Maximum number of reviews.

        Returns:
            List of raw review dictionaries.

        Raises:
            ValueError: If API key is not configured.
        """
        if not self._api_key:
            raise ValueError("Indeed API key is not configured")

        self._logger.info("fetching_indeed_reviews", company=company_name, limit=limit)

        # Mock response for demonstration
        return [
            {
                "id": f"ind_{i}",
                "rating": 3.5,
                "title": "Good company overall",
                "content": "Decent place to work, good work-life balance.",
                "pros": "Work-life balance, good benefits",
                "cons": "Bureaucracy",
                "date": "2024-01-10",
            }
            for i in range(min(limit, 5))
        ]

    async def get_company_info(self, company_name: str) -> dict[str, Any]:
        """Get company information from Indeed.

        Args:
            company_name: Company name to search.

        Returns:
            Dictionary with company information.
        """
        if not self._api_key:
            raise ValueError("Indeed API key is not configured")

        self._logger.info("fetching_indeed_company_info", company=company_name)

        return {
            "name": company_name,
            "rating": 3.8,
            "review_count": 2000,
            "salary_rating": 3.5,
            "work_life_balance": 4.0,
        }
