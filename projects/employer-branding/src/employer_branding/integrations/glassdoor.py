"""Glassdoor API integration client."""

from __future__ import annotations

from typing import Any

import structlog

from employer_branding.integrations.base import BaseReviewClient

logger = structlog.get_logger(__name__)


class GlassdoorClient(BaseReviewClient):
    """Client for interacting with the Glassdoor API."""

    BASE_URL = "https://api.glassdoor.com/api/v1"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Glassdoor client.

        Args:
            api_key: Glassdoor API key. Uses settings if not provided.
        """
        super().__init__(api_key or self._settings.glassdoor_api_key)
        self._base_url = self.BASE_URL

    async def fetch_reviews(
        self, company_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch reviews from Glassdoor.

        Args:
            company_name: Company name to search.
            limit: Maximum number of reviews.

        Returns:
            List of raw review dictionaries.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self._api_key:
            raise ValueError("Glassdoor API key is not configured")

        self._logger.info("fetching_glassdoor_reviews", company=company_name, limit=limit)

        # In production, make actual API call
        # response = await self._client.get(
        #     f"{self._base_url}/reviews",
        #     params={"company": company_name, "limit": limit},
        #     headers={"Authorization": f"Bearer {self._api_key}"},
        # )
        # response.raise_for_status()
        # return response.json().get("reviews", [])

        # Mock response for demonstration
        return [
            {
                "id": f"gd_{i}",
                "rating": 4.0,
                "title": "Great company",
                "content": "Wonderful place to work with great benefits.",
                "pros": "Good culture, flexible hours",
                "cons": "Limited parking",
                "date": "2024-01-15",
            }
            for i in range(min(limit, 5))
        ]

    async def get_company_info(self, company_name: str) -> dict[str, Any]:
        """Get company information from Glassdoor.

        Args:
            company_name: Company name to search.

        Returns:
            Dictionary with company information.
        """
        if not self._api_key:
            raise ValueError("Glassdoor API key is not configured")

        self._logger.info("fetching_glassdoor_company_info", company=company_name)

        # Mock response
        return {
            "name": company_name,
            "rating": 4.2,
            "review_count": 1500,
            "recommend_to_friend": 75,
            "ceo_approval": 80,
        }
