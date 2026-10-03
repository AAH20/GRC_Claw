"""Content Ranker Agent for community curation."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import structlog

from ugc_marketplace.agents.community_curation.base import BaseCurationAgent
from ugc_marketplace.config import get_settings

logger = structlog.get_logger(__name__)


class ContentRankerAgent(BaseCurationAgent[list["ContentItem"], list["RankedContent"]]):
    """Agent that ranks content for community curation.

    Uses engagement metrics, quality scores, and recency
    to rank content for community feeds.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for content ranking.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._calculate_engagement_score,
            self._calculate_quality_score,
            self._calculate_recency_score,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a content ranking specialist. Rank content based on "
                "engagement metrics, quality scores, and recency. Provide "
                "explanations for ranking decisions."
            ),
        )
        return agent

    async def execute(self, input_data: list["ContentItem"]) -> list["RankedContent"]:
        """Execute content ranking.

        Args:
            input_data: List of content items to rank.

        Returns:
            List of ranked content.
        """
        self._tasks_processed += 1
        ranked = []
        for item in input_data:
            score = self._calculate_rank_score(item)
            ranked.append(
                RankedContent(
                    content_id=item.content_id,
                    title=item.title,
                    score=score,
                    rank=0,
                    factors={"engagement": 0.5, "quality": 0.3, "recency": 0.2},
                )
            )

        ranked.sort(key=lambda x: x.score, reverse=True)
        for i, r in enumerate(ranked):
            r.rank = i + 1

        logger.info("Content ranking completed", items_ranked=len(ranked))
        return ranked

    def _calculate_rank_score(self, item: "ContentItem") -> float:
        """Calculate ranking score for a content item.

        Args:
            item: Content item to score.

        Returns:
            Ranking score.
        """
        engagement = min(item.like_count / 1000, 1.0) * 0.4
        quality = (item.quality_score or 0.5) * 0.3
        age_hours = (datetime.now(UTC) - item.created_at).total_seconds() / 3600
        recency = math.exp(-age_hours / 24) * 0.3
        return engagement + quality + recency

    @staticmethod
    async def _calculate_engagement_score(metrics: dict[str, Any]) -> float:
        """Calculate engagement score.

        Args:
            metrics: Engagement metrics.

        Returns:
            Engagement score.
        """
        return 0.5

    @staticmethod
    async def _calculate_quality_score(content: str) -> float:
        """Calculate quality score.

        Args:
            content: Content text.

        Returns:
            Quality score.
        """
        return 0.5

    @staticmethod
    async def _calculate_recency_score(created_at: datetime) -> float:
        """Calculate recency score.

        Args:
            created_at: Content creation time.

        Returns:
            Recency score.
        """
        return 0.5
