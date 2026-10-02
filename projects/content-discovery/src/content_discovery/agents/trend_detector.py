"""Trend detection agent for identifying emerging topics and patterns."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import structlog
from langchain_core.tools import tool

from content_discovery.agents.base import BaseAgent
from content_discovery.integrations.analytics import AnalyticsClient
from content_discovery.models import Trend, TrendDirection, TrendRequest, TrendResponse

logger = structlog.get_logger()


class TrendDetectorAgent(BaseAgent[TrendRequest, TrendResponse]):
    """Agent that detects emerging trends from content and search analytics.

    Analyzes temporal patterns in content volume, search queries, and
    engagement metrics to identify rising and falling topics.
    """

    def __init__(self, analytics: AnalyticsClient, llm: Any | None = None) -> None:
        """Initialize the trend detector agent.

        Args:
            analytics: Client for analytics data.
            llm: Optional LLM for trend interpretation.
        """
        self.analytics = analytics
        super().__init__(name="trend_detector", llm=llm)

    def _get_tools(self) -> list[Any]:
        """Get tools available to the trend detector agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return [self._get_volume_tool, self._get_related_topics_tool]

    @tool
    def _get_volume_tool(self, topic: str, days: int = 7) -> list[dict[str, Any]]:
        """Get search volume data for a topic over time.

        Args:
            topic: Topic or keyword.
            days: Number of days to analyze.

        Returns:
            list[dict[str, Any]]: Daily volume data points.
        """
        return self.analytics.get_volume(topic=topic, days=days)

    @tool
    def _get_related_topics_tool(self, topic: str) -> list[str]:
        """Get topics related to a given topic.

        Args:
            topic: Base topic.

        Returns:
            list[str]: Related topic strings.
        """
        return self.analytics.get_related_topics(topic=topic)

    async def execute(self, input_data: TrendRequest) -> TrendResponse:
        """Detect trends from analytics data.

        Args:
            input_data: Trend detection request.

        Returns:
            TrendResponse: Detected trends with direction and scores.
        """
        start = time.monotonic()

        # Get topics to analyze
        topics = input_data.topics or await self._discover_topics(input_data.window_days)

        # Analyze each topic for trends
        trends: list[Trend] = []
        for topic in topics:
            trend = await self._analyze_topic(topic, input_data.window_days)
            if trend is not None:
                trends.append(trend)

        # Sort by score and limit
        trends.sort(key=lambda t: t.score, reverse=True)
        trends = trends[: input_data.limit]

        elapsed = (time.monotonic() - start) * 1000

        return TrendResponse(
            trends=trends,
            window_days=input_data.window_days,
            took_ms=round(elapsed, 2),
        )

    async def _discover_topics(self, window_days: int) -> list[str]:
        """Discover trending topics from analytics.

        Args:
            window_days: Analysis window in days.

        Returns:
            list[str]: Discovered topic strings.
        """
        try:
            return self.analytics.get_top_topics(days=window_days, limit=20)
        except Exception as exc:
            logger.error("topic_discovery_failed", error=str(exc))
            return []

    async def _analyze_topic(self, topic: str, window_days: int) -> Trend | None:
        """Analyze a single topic for trend patterns.

        Args:
            topic: Topic to analyze.
            window_days: Analysis window in days.

        Returns:
            Trend | None: Detected trend or None if insufficient data.
        """
        try:
            volume_data = self.analytics.get_volume(topic=topic, days=window_days)
            if not volume_data or len(volume_data) < 2:
                return None

            # Calculate trend metrics
            volumes = [d["count"] for d in volume_data]
            total_volume = sum(volumes)
            avg_volume = total_volume / len(volumes)

            if avg_volume < 1:
                return None

            # Determine direction
            first_half = sum(volumes[: len(volumes) // 2])
            second_half = sum(volumes[len(volumes) // 2 :])

            if first_half == 0:
                change_percent = 100.0 if second_half > 0 else 0.0
            else:
                change_percent = ((second_half - first_half) / first_half) * 100

            # Classify direction
            if change_percent > 20:
                direction = TrendDirection.RISING
            elif change_percent < -20:
                direction = TrendDirection.FALLING
            elif abs(change_percent) < 5:
                direction = TrendDirection.STABLE
            else:
                direction = TrendDirection.VOLATILE

            # Calculate trend score
            score = min(abs(change_percent) / 100, 1.0)

            # Get related topics
            related = self.analytics.get_related_topics(topic=topic)

            # Find peak
            peak_idx = volumes.index(max(volumes))
            peak_at = datetime.utcnow() - timedelta(days=window_days - peak_idx)

            return Trend(
                id=f"trend_{topic.replace(' ', '_')}",
                topic=topic,
                direction=direction,
                score=round(score, 3),
                volume=total_volume,
                change_percent=round(change_percent, 2),
                related_topics=related[:5],
                started_at=datetime.utcnow() - timedelta(days=window_days),
                peak_at=peak_at,
            )
        except Exception as exc:
            logger.error("topic_analysis_failed", topic=topic, error=str(exc))
            return None
