"""Trend surfacing agent implementation."""

from __future__ import annotations

import structlog
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from community_curation.agents.base import BaseCurationAgent
from community_curation.config.settings import get_settings
from community_curation.models import ContentItem, Trend

logger = structlog.get_logger(__name__)


class TrendSurferAgent(BaseCurationAgent[list[ContentItem], list[Trend]]):
    """Agent that surfaces emerging trends from community content."""

    def __init__(self) -> None:
        """Initialize the trend surfer agent."""
        super().__init__(
            name="TrendSurferAgent",
            description="Surfaces emerging trends and viral content from community discussions",
        )
        self.settings = get_settings()

    def _extract_keywords(self, items: list[ContentItem]) -> Counter[str]:
        """Extract and count keywords from content items.

        Args:
            items: Content items to analyze.

        Returns:
            Counter of keyword frequencies.
        """
        keywords: Counter[str] = Counter()
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
            "during", "before", "after", "above", "below", "between", "and", "but",
            "or", "nor", "not", "so", "yet", "both", "either", "neither", "each",
            "every", "all", "any", "few", "more", "most", "other", "some", "such",
            "no", "only", "own", "same", "than", "too", "very", "just", "because",
            "if", "when", "while", "that", "this", "these", "those", "it", "its",
        }

        for item in items:
            text = f"{item.title} {item.body}".lower()
            # Simple tokenization
            words = text.split()
            for word in words:
                # Strip punctuation
                cleaned = word.strip(".,!?;:\"'()[]{}")
                if len(cleaned) > 2 and cleaned not in stop_words:
                    keywords[cleaned] += 1

        return keywords

    def _compute_velocity(self, items: list[ContentItem], window_hours: int) -> float:
        """Compute trend velocity (items per hour).

        Args:
            items: Content items in the trend.
            window_hours: Time window in hours.

        Returns:
            Velocity as items per hour.
        """
        if not items or window_hours <= 0:
            return 0.0
        return len(items) / window_hours

    def _estimate_sentiment(self, items: list[ContentItem]) -> float:
        """Estimate sentiment score for a group of content items.

        Args:
            items: Content items to analyze.

        Returns:
            Sentiment score between -1 and 1.
        """
        positive_words = {
            "good", "great", "excellent", "amazing", "awesome", "fantastic",
            "wonderful", "brilliant", "outstanding", "superb", "love", "best",
            "happy", "excited", "impressive", "remarkable", "exceptional",
        }
        negative_words = {
            "bad", "terrible", "awful", "horrible", "worst", "hate", "poor",
            "disappointing", "useless", "broken", "fail", "wrong", "ugly",
            "sad", "angry", "frustrated", "annoying", "stupid",
        }

        total_score = 0.0
        count = 0

        for item in items:
            text = f"{item.title} {item.body}".lower()
            pos_count = sum(1 for w in positive_words if w in text)
            neg_count = sum(1 for w in negative_words if w in text)
            if pos_count + neg_count > 0:
                total_score += (pos_count - neg_count) / (pos_count + neg_count)
                count += 1

        if count == 0:
            return 0.0
        return total_score / count

    async def run(self, input_data: list[ContentItem]) -> list[Trend]:
        """Surface trends from content items.

        Args:
            input_data: List of content items to analyze.

        Returns:
            List of detected trends.
        """
        if not self.is_available:
            logger.warning("agent_unavailable", agent=self.name)
            return self._fallback_trends(input_data)

        if not input_data:
            return []

        lookback = self.settings.trend_lookback_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback)

        # Filter to recent content
        recent_items = [item for item in input_data if item.created_at >= cutoff]
        if not recent_items:
            recent_items = input_data  # Use all if none in window

        # Extract keywords
        keywords = self._extract_keywords(recent_items)
        top_keywords = [kw for kw, _ in keywords.most_common(20)]

        # Group content by keyword clusters
        trend_groups: dict[str, list[ContentItem]] = {}
        for item in recent_items:
            text = f"{item.title} {item.body}".lower()
            for keyword in top_keywords:
                if keyword in text:
                    trend_groups.setdefault(keyword, []).append(item)

        # Build trends from groups
        trends: list[Trend] = []
        for idx, (keyword, items) in enumerate(
            sorted(trend_groups.items(), key=lambda x: len(x[1]), reverse=True)
        ):
            if len(items) < 2:
                continue

            velocity = self._compute_velocity(items, lookback)
            sentiment = self._estimate_sentiment(items)

            # Find related trends
            related = [
                f"trend_{i}"
                for i, (kw, _) in enumerate(
                    sorted(trend_groups.items(), key=lambda x: len(x[1]), reverse=True)
                )
                if kw != keyword and i < 5
            ][:3]

            trends.append(
                Trend(
                    id=f"trend_{idx}",
                    name=keyword.title(),
                    description=f"Emerging trend around '{keyword}' with {len(items)} related items",
                    keywords=[keyword],
                    content_count=len(items),
                    velocity=round(velocity, 2),
                    sentiment=round(sentiment, 2),
                    started_at=min(item.created_at for item in items),
                    peak_at=max(item.created_at for item in items),
                    related_trends=related,
                )
            )

        logger.info("trends_surfaced", count=len(trends))
        return trends

    def _fallback_trends(self, items: list[ContentItem]) -> list[Trend]:
        """Fallback trend detection when agent is unavailable.

        Args:
            items: Content items to analyze.

        Returns:
            List of trends.
        """
        if not items:
            return []

        keywords = self._extract_keywords(items)
        top = keywords.most_common(5)

        trends = []
        for idx, (kw, count) in enumerate(top):
            trends.append(
                Trend(
                    id=f"trend_{idx}",
                    name=kw.title(),
                    description=f"Fallback trend: '{kw}'",
                    keywords=[kw],
                    content_count=count,
                    velocity=0.0,
                    sentiment=0.0,
                )
            )
        return trends
