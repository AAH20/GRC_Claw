"""Content ranking agent implementation."""

from __future__ import annotations

import math
from datetime import UTC, datetime

import structlog

from community_curation.agents.base import BaseCurationAgent
from community_curation.config.settings import get_settings
from community_curation.models import ContentItem, RankedContent

logger = structlog.get_logger(__name__)


class ContentRankerAgent(BaseCurationAgent[list[ContentItem], list[RankedContent]]):
    """Agent that ranks community content using engagement, recency, quality, and
    relevance signals."""

    def __init__(self) -> None:
        """Initialize the content ranker agent."""
        super().__init__(
            name="ContentRankerAgent",
            description="Ranks community content by engagement, recency, quality, and relevance",
        )
        self.settings = get_settings()

    def _compute_engagement_score(self, item: ContentItem) -> float:
        """Compute normalized engagement score.

        Args:
            item: Content item to score.

        Returns:
            Engagement score between 0 and 1.
        """
        score = item.score
        comments = item.comment_count
        # Logarithmic scaling to handle viral content
        engagement = math.log1p(score) + 0.5 * math.log1p(comments)
        # Normalize with sigmoid-like function
        return min(1.0, engagement / 10.0)

    def _compute_recency_score(self, item: ContentItem) -> float:
        """Compute recency score based on content age.

        Args:
            item: Content item to score.

        Returns:
            Recency score between 0 and 1.
        """
        now = datetime.now(UTC)
        age_hours = (now - item.created_at).total_seconds() / 3600.0
        # Exponential decay with 48-hour half-life
        return math.exp(-age_hours / 48.0)

    def _compute_quality_score(self, item: ContentItem) -> float:
        """Compute quality score based on content metadata.

        Args:
            item: Content item to score.

        Returns:
            Quality score between 0 and 1.
        """
        metadata = item.metadata
        quality_signals = 0.0
        total_signals = 0

        if "upvote_ratio" in metadata:
            quality_signals += float(metadata["upvote_ratio"])
            total_signals += 1
        if "award_count" in metadata:
            quality_signals += min(1.0, float(metadata["award_count"]) / 5.0)
            total_signals += 1
        if "verified_author" in metadata:
            quality_signals += 1.0 if metadata["verified_author"] else 0.0
            total_signals += 1

        if total_signals == 0:
            return 0.5  # Default neutral quality
        return quality_signals / total_signals

    def _compute_relevance_score(self, item: ContentItem, query: str) -> float:
        """Compute relevance score based on query match.

        Args:
            item: Content item to score.
            query: Search query.

        Returns:
            Relevance score between 0 and 1.
        """
        query_lower = query.lower()
        title_lower = item.title.lower()
        body_lower = item.body.lower()

        score = 0.0
        if query_lower in title_lower:
            score += 0.6
        if query_lower in body_lower:
            score += 0.3
        # Check individual query terms
        query_terms = query_lower.split()
        matching_terms = sum(1 for term in query_terms if term in title_lower or term in body_lower)
        if query_terms:
            score += 0.1 * (matching_terms / len(query_terms))

        return min(1.0, score)

    async def run(self, input_data: list[ContentItem], query: str = "") -> list[RankedContent]:
        """Rank content items.

        Args:
            input_data: List of content items to rank.
            query: Search query for relevance scoring.

        Returns:
            List of ranked content items sorted by score.
        """
        if not self.is_available:
            logger.warning("agent_unavailable", agent=self.name)
            return self._fallback_rank(input_data, query)

        weights = self.settings.ranking_weights
        ranked: list[RankedContent] = []

        for item in input_data:
            engagement = self._compute_engagement_score(item)
            recency = self._compute_recency_score(item)
            quality = self._compute_quality_score(item)
            relevance = self._compute_relevance_score(item, query)

            total_score = (
                weights.get("engagement", 0.35) * engagement
                + weights.get("recency", 0.25) * recency
                + weights.get("quality", 0.25) * quality
                + weights.get("relevance", 0.15) * relevance
            )

            ranked.append(
                RankedContent(
                    content=item,
                    rank=1,  # Will be set after sorting
                    ranking_score=round(total_score, 4),
                    score_breakdown={
                        "engagement": round(engagement, 4),
                        "recency": round(recency, 4),
                        "quality": round(quality, 4),
                        "relevance": round(relevance, 4),
                    },
                    ranking_reason=self._generate_reason(engagement, recency, quality, relevance),
                )
            )

        # Sort by score descending
        ranked.sort(key=lambda x: x.ranking_score, reverse=True)

        # Assign ranks
        for idx, item in enumerate(ranked, start=1):
            item.rank = idx

        logger.info("content_ranked", count=len(ranked), query=query)
        return ranked

    def _fallback_rank(self, items: list[ContentItem], query: str) -> list[RankedContent]:
        """Fallback ranking when agent is unavailable.

        Args:
            items: Content items to rank.
            query: Search query.

        Returns:
            Ranked content list.
        """
        ranked = []
        for idx, item in enumerate(items, start=1):
            score = (
                self._compute_engagement_score(item) * 0.5
                + self._compute_recency_score(item) * 0.5
            )
            ranked.append(
                RankedContent(
                    content=item,
                    rank=idx,
                    ranking_score=round(score, 4),
                    score_breakdown={"engagement": 0.5, "recency": 0.5},
                    ranking_reason="Fallback ranking (agent unavailable)",
                )
            )
        ranked.sort(key=lambda x: x.ranking_score, reverse=True)
        for idx, item in enumerate(ranked, start=1):
            item.rank = idx
        return ranked

    def _generate_reason(
        self, engagement: float, recency: float, quality: float, relevance: float
    ) -> str:
        """Generate human-readable ranking reason.

        Args:
            engagement: Engagement score.
            recency: Recency score.
            quality: Quality score.
            relevance: Relevance score.

        Returns:
            Ranking reason string.
        """
        scores = {
            "engagement": engagement,
            "recency": recency,
            "quality": quality,
            "relevance": relevance,
        }
        top_factor = max(scores, key=scores.get)
        return f"High {top_factor} score ({scores[top_factor]:.2f})"
