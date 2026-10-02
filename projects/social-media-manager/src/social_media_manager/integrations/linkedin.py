"""LinkedIn API client."""

from __future__ import annotations

from typing import Any

from social_media_manager.integrations.base import BasePlatformClient


class LinkedInClient(BasePlatformClient):
    """Client for the LinkedIn v2 REST API."""

    platform = "linkedin"
    base_url = "https://api.linkedin.com/v2"

    async def create_post(
        self, author_urn: str, text: str, visibility: str = "PUBLIC"
    ) -> dict[str, Any]:
        """Create a text share on behalf of an author.

        Args:
            author_urn: Author URN, e.g. ``urn:li:person:abc123``.
            text: Share commentary text.
            visibility: ``PUBLIC`` or ``CONNECTIONS``.

        Returns:
            API response containing the post id.
        """
        if not author_urn or not text.strip():
            raise ValueError("author_urn and text are required")
        if visibility not in {"PUBLIC", "CONNECTIONS"}:
            raise ValueError("visibility must be PUBLIC or CONNECTIONS")
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }
        return await self._request("POST", "/ugcPosts", json=body)

    async def get_profile(self) -> dict[str, Any]:
        """Fetch the authenticated member's profile."""
        return await self._request("GET", "/userinfo")

    async def get_share_statistics(self, share_urn: str) -> dict[str, Any]:
        """Fetch social statistics for a share."""
        if not share_urn:
            raise ValueError("share_urn is required")
        return await self._request(
            "GET", "/socialActions", params={"shares": share_urn}
        )
