"""TikTok integration for influencer marketing."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from influencer_marketing.agents.discovery import DiscoveryCriteria, DiscoveredInfluencer

logger = structlog.get_logger(__name__)


class TikTokClient:
    """Client for interacting with TikTok API."""

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token

    async def search_influencers(
        self, criteria: DiscoveryCriteria
    ) -> list[DiscoveredInfluencer]:
        """Search for influencers on TikTok."""
        logger.info("Searching TikTok for influencers")
        return []
