"""Instagram integration for influencer marketing."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from influencer_marketing.agents.discovery import DiscoveryCriteria, DiscoveredInfluencer

logger = structlog.get_logger(__name__)


class InstagramClient:
    """Client for interacting with Instagram API."""

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token

    async def search_influencers(
        self, criteria: DiscoveryCriteria
    ) -> list[DiscoveredInfluencer]:
        """Search for influencers on Instagram."""
        logger.info("Searching Instagram for influencers")
        return []
