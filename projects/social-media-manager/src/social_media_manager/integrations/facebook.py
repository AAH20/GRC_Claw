"""Facebook Graph API client."""

from __future__ import annotations

from typing import Any

from social_media_manager.integrations.base import BasePlatformClient


class FacebookClient(BasePlatformClient):
    """Client for the Facebook Graph API (Pages)."""

    platform = "facebook"
    base_url = "https://graph.facebook.com/v18.0"

    async def create_post(
        self, page_id: str, message: str, link: str | None = None
    ) -> dict[str, Any]:
        """Publish a post to a Facebook Page.

        Args:
            page_id: Facebook Page id.
            message: Post body text.
            link: Optional URL to attach.

        Returns:
            API response containing the post id.
        """
        if not page_id or not message.strip():
            raise ValueError("page_id and message are required")
        body: dict[str, Any] = {"message": message}
        if link:
            body["link"] = link
        return await self._request("POST", f"/{page_id}/feed", json=body)

    async def get_page_insights(self, page_id: str, period: str = "day") -> dict[str, Any]:
        """Fetch Page insights for a period."""
        if not page_id:
            raise ValueError("page_id is required")
        if period not in {"day", "week", "days_28"}:
            raise ValueError("period must be one of: day, week, days_28")
        return await self._request(
            "GET",
            f"/{page_id}/insights",
            params={"metric": "page_impressions,page_engaged_users", "period": period},
        )

    async def get_page_posts(self, page_id: str, limit: int = 10) -> dict[str, Any]:
        """Fetch recent posts from a Page."""
        if not page_id:
            raise ValueError("page_id is required")
        return await self._request(
            "GET",
            f"/{page_id}/posts",
            params={"limit": max(1, min(int(limit), 100))},
        )
