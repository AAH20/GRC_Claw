"""Discovery agent for finding potential influencers across platforms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.integrations.instagram import InstagramClient
from influencer_marketing.integrations.tiktok import TikTokClient
from influencer_marketing.integrations.youtube import YouTubeClient

logger = structlog.get_logger(__name__)


@dataclass
class DiscoveryCriteria:
    """Criteria for influencer discovery."""

    platforms: list[str] = field(default_factory=lambda: ["instagram", "tiktok", "youtube"])
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    min_followers: int = 1000
    max_followers: int = 10_000_000
    min_engagement_rate: float = 0.01
    locations: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=lambda: ["en"])
    max_results: int = 50


@dataclass
class DiscoveredInfluencer:
    """An influencer discovered during search."""

    platform: str
    platform_id: str
    username: str
    display_name: str
    bio: str
    follower_count: int
    following_count: int
    post_count: int
    engagement_rate: float
    profile_url: str
    profile_image_url: str
    email: str | None = None
    categories: list[str] = field(default_factory=list)
    location: str | None = None
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


class DiscoveryAgent(BaseAgent[DiscoveryCriteria, list[DiscoveredInfluencer]]):
    """Agent responsible for discovering potential influencers across social platforms."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="discovery",
            description="Discovers potential influencers across social media platforms",
            max_retries=3,
            timeout_seconds=120,
        )
        super().__init__(config)
        self._instagram: InstagramClient | None = None
        self._tiktok: TikTokClient | None = None
        self._youtube: YouTubeClient | None = None

    async def _get_instagram(self) -> InstagramClient:
        if self._instagram is None:
            self._instagram = InstagramClient()
        return self._instagram

    async def _get_tiktok(self) -> TikTokClient:
        if self._tiktok is None:
            self._tiktok = TikTokClient()
        return self._tiktok

    async def _get_youtube(self) -> YouTubeClient:
        if self._youtube is None:
            self._youtube = YouTubeClient()
        return self._youtube

    async def validate_input(self, input_data: DiscoveryCriteria) -> bool:
        """Validate discovery criteria."""
        if not input_data.platforms:
            self.logger.warning("No platforms specified for discovery")
            return False
        if input_data.min_followers < 0 or input_data.max_followers < 0:
            self.logger.warning("Invalid follower count range")
            return False
        if input_data.min_followers > input_data.max_followers:
            self.logger.warning("min_followers exceeds max_followers")
            return False
        if not 0 <= input_data.min_engagement_rate <= 1:
            self.logger.warning("Invalid engagement rate")
            return False
        return True

    async def execute(
        self, input_data: DiscoveryCriteria
    ) -> AgentResult[list[DiscoveredInfluencer]]:
        """Execute influencer discovery across specified platforms."""
        discovered: list[DiscoveredInfluencer] = []
        errors: list[str] = []

        platform_map = {
            "instagram": self._discover_instagram,
            "tiktok": self._discover_tiktok,
            "youtube": self._discover_youtube,
        }

        for platform in input_data.platforms:
            discover_fn = platform_map.get(platform)
            if discover_fn is None:
                self.logger.warning("Unsupported platform", platform=platform)
                continue
            try:
                results = await discover_fn(input_data)
                discovered.extend(results)
            except Exception as exc:
                self.logger.error(
                    "Platform discovery failed", platform=platform, error=str(exc)
                )
                errors.append(f"{platform}: {exc}")

        # Deduplicate by platform_id
        seen: set[tuple[str, str]] = set()
        unique: list[DiscoveredInfluencer] = []
        for inf in discovered:
            key = (inf.platform, inf.platform_id)
            if key not in seen:
                seen.add(key)
                unique.append(inf)

        # Sort by engagement rate descending, limit results
        unique.sort(key=lambda x: x.engagement_rate, reverse=True)
        unique = unique[: input_data.max_results]

        self.logger.info(
            "Discovery completed",
            total_found=len(discovered),
            unique_count=len(unique),
            errors=len(errors),
        )

        return AgentResult(
            success=True,
            data=unique,
            metadata={"errors": errors, "total_candidates": len(discovered)},
        )

    async def _discover_instagram(
        self, criteria: DiscoveryCriteria
    ) -> list[DiscoveredInfluencer]:
        """Discover influencers on Instagram."""
        client = await self._get_instagram()
        return await client.search_influencers(criteria)

    async def _discover_tiktok(
        self, criteria: DiscoveryCriteria
    ) -> list[DiscoveredInfluencer]:
        """Discover influencers on TikTok."""
        client = await self._get_tiktok()
        return await client.search_influencers(criteria)

    async def _discover_youtube(
        self, criteria: DiscoveryCriteria
    ) -> list[DiscoveredInfluencer]:
        """Discover influencers on YouTube."""
        client = await self._get_youtube()
        return await client.search_influencers(criteria)
