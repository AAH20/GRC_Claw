"""Listening Agent - Collects brand mentions from social media and news platforms."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class Platform(StrEnum):
    """Supported platforms for brand monitoring."""

    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWSAPI = "newsapi"


class MentionType(StrEnum):
    """Type of brand mention."""

    POST = "post"
    COMMENT = "comment"
    ARTICLE = "article"
    REVIEW = "review"


@dataclass
class Mention:
    """Represents a brand mention found on a platform."""

    id: str
    platform: Platform
    mention_type: MentionType
    content: str
    author: str
    url: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base class for platform collectors."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logger.bind(collector=self.__class__.__name__)

    @abstractmethod
    async def collect(self, query: str, limit: int = 100) -> list[Mention]:
        """Collect mentions from the platform."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the collector is healthy."""
        ...


class ListeningAgent:
    """Agent responsible for collecting brand mentions from multiple platforms."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logger.bind(agent="listening")
        self.collectors: dict[Platform, BaseCollector] = {}
        self._running = False

    def register_collector(self, platform: Platform, collector: BaseCollector) -> None:
        """Register a collector for a specific platform."""
        self.collectors[platform] = collector
        self.logger.info("Registered collector", platform=platform.value)

    async def start(self) -> None:
        """Start the listening agent."""
        self._running = True
        self.logger.info("Listening agent started")

    async def stop(self) -> None:
        """Stop the listening agent."""
        self._running = False
        self.logger.info("Listening agent stopped")

    async def collect_all(
        self,
        query: str,
        platforms: list[Platform] | None = None,
        limit_per_platform: int = 100,
    ) -> list[Mention]:
        """Collect mentions from all registered platforms."""
        target_platforms = platforms or list(self.collectors.keys())
        all_mentions: list[Mention] = []

        tasks = []
        for platform in target_platforms:
            collector = self.collectors.get(platform)
            if collector is None:
                self.logger.warning("No collector registered", platform=platform.value)
                continue
            tasks.append(self._collect_with_error_handling(collector, query, limit_per_platform))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                self.logger.error("Collection failed", error=str(result))
            else:
                all_mentions.extend(result)

        self.logger.info(
            "Collection complete",
            total_mentions=len(all_mentions),
            platforms=[p.value for p in target_platforms],
        )
        return all_mentions

    async def _collect_with_error_handling(
        self,
        collector: BaseCollector,
        query: str,
        limit: int,
    ) -> list[Mention]:
        """Collect mentions with error handling."""
        try:
            return await collector.collect(query, limit)
        except Exception as exc:
            self.logger.error(
                "Collector failed",
                collector=collector.__class__.__name__,
                error=str(exc),
            )
            return []

    async def health_check(self) -> dict[str, bool]:
        """Check health of all collectors."""
        results: dict[str, bool] = {}
        for platform, collector in self.collectors.items():
            try:
                results[platform.value] = await collector.health_check()
            except Exception as exc:
                self.logger.error(
                    "Health check failed",
                    platform=platform.value,
                    error=str(exc),
                )
                results[platform.value] = False
        return results
