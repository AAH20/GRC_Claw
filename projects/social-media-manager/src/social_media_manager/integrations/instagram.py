"""Instagram Graph API client."""

from __future__ import annotations

from typing import Any

from social_media_manager.integrations.base import BasePlatformClient


class InstagramClient(BasePlatformClient):
    """Client for the Instagram Graph API."""

    platform = "instagram"
    base_url = "https://graph.instagram.com/v18.0"

    async def create_media_container(
        self, ig_user_id: str, image_url: str, caption: str = ""
    ) -> dict[str, Any]:
        """Create a media container for a photo post.

        Args:
            ig_user_id: Instagram business account id.
            image_url: Publicly accessible image URL.
            caption: Post caption.

        Returns:
            API response containing the container id.
        """
        if not ig_user_id or not image_url:
            raise ValueError("ig_user_id and image_url are required")
        return await self._request(
            "POST",
            f"/{ig_user_id}/media",
            json={"image_url": image_url, "caption": caption},
        )

    async def publish_media(self, ig_user_id: str, creation_id: str) -> dict[str, Any]:
        """Publish a previously created media container."""
        if not ig_user_id or not creation_id:
            raise ValueError("ig_user_id and creation_id are required")
        return await self._request(
            "POST",
            f"/{ig_user_id}/media_publish",
            json={"creation_id": creation_id},
        )

    async def get_account_insights(
        self, ig_user_id: str, metrics: list[str] | None = None
    ) -> dict[str, Any]:
        """Fetch account-level insights."""
        if not ig_user_id:
            raise ValueError("ig_user_id is required")
        metric_list = metrics or ["impressions", "reach", "profile_views"]
        return await self._request(
            "GET",
            f"/{ig_user_id}/insights",
            params={"metric": ",".join(metric_list)},
        )

    async def get_recent_media(self, ig_user_id: str, limit: int = 10) -> dict[str, Any]:
        """Fetch recent media objects for an account."""
        if not ig_user_id:
            raise ValueError("ig_user_id is required")
        return await self._request(
            "GET",
            f"/{ig_user_id}/media",
            params={"limit": max(1, min(int(limit), 100))},
        )
