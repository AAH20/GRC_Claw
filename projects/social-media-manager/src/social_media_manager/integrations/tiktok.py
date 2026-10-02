"""TikTok API client."""

from __future__ import annotations

from typing import Any

from social_media_manager.integrations.base import BasePlatformClient


class TikTokClient(BasePlatformClient):
    """Client for the TikTok Open API."""

    platform = "tiktok"
    base_url = "https://open-api.tiktok.com"

    async def get_user_info(self, open_id: str) -> dict[str, Any]:
        """Fetch a TikTok user's public profile information."""
        if not open_id:
            raise ValueError("open_id is required")
        return await self._request(
            "GET",
            "/user/info/",
            params={"open_id": open_id, "fields": "display_name,follower_count,likes_count"},
        )

    async def get_video_list(self, open_id: str, cursor: int = 0) -> dict[str, Any]:
        """List videos published by a user."""
        if not open_id:
            raise ValueError("open_id is required")
        return await self._request(
            "POST",
            "/video/list/",
            json={"open_id": open_id, "cursor": int(cursor), "max_count": 20},
        )

    async def get_video_metrics(self, video_ids: list[str]) -> dict[str, Any]:
        """Fetch metrics for one or more videos."""
        if not video_ids:
            raise ValueError("video_ids must be a non-empty list")
        return await self._request(
            "POST",
            "/video/query/",
            json={"filters": {"video_ids": video_ids[:20]}},
        )

    async def upload_video(
        self, open_id: str, video_url: str, caption: str = ""
    ) -> dict[str, Any]:
        """Publish a video from a URL to TikTok."""
        if not open_id or not video_url:
            raise ValueError("open_id and video_url are required")
        return await self._request(
            "POST",
            "/video/upload/",
            json={"open_id": open_id, "video_url": video_url, "text": caption},
        )
