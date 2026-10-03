"""Community Curation Agent for UGC Marketplace.

Provides content curation and ranking capabilities using mock data.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ContentCategory(str, Enum):
    """Content categories available in the marketplace."""

    TUTORIAL = "tutorial"
    REVIEW = "review"
    SHOWCASE = "showcase"
    DISCUSSION = "discussion"
    NEWS = "news"


class ContentQuality(str, Enum):
    """Quality tiers for curated content."""

    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"


@dataclass
class UserPreferences:
    """User preferences for feed curation."""

    favorite_categories: list[ContentCategory] = field(default_factory=list)
    min_quality: ContentQuality = ContentQuality.AVERAGE
    max_results: int = 20
    recency_weight: float = 0.3
    diversity_weight: float = 0.2
    engagement_weight: float = 0.5


@dataclass
class ContentItem:
    """Represents a single piece of UGC content."""

    content_id: str
    title: str
    author_id: str
    category: ContentCategory
    quality: ContentQuality
    tags: list[str] = field(default_factory=list)
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    is_featured: bool = False


@dataclass
class RankedContent:
    """A content item with its computed rank score."""

    content: ContentItem
    score: float
    rank_reason: str = ""


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

MOCK_CONTENT_DB: list[ContentItem] = [
    ContentItem(
        content_id="c001",
        title="Getting Started with 3D Modeling in Blender",
        author_id="u101",
        category=ContentCategory.TUTORIAL,
        quality=ContentQuality.EXCELLENT,
        tags=["blender", "3d", "beginner"],
        likes=342,
        comments=56,
        shares=28,
        views=5200,
        created_at=datetime.now() - timedelta(hours=3),
        is_featured=True,
    ),
    ContentItem(
        content_id="c002",
        title="My Honest Review of the New RTX 5090",
        author_id="u205",
        category=ContentCategory.REVIEW,
        quality=ContentQuality.GOOD,
        tags=["gpu", "hardware", "review"],
        likes=189,
        comments=134,
        shares=45,
        views=8900,
        created_at=datetime.now() - timedelta(hours=12),
    ),
    ContentItem(
        content_id="c003",
        title="Showcase: Procedural City Generator",
        author_id="u310",
        category=ContentCategory.SHOWCASE,
        quality=ContentQuality.EXCELLENT,
        tags=["procedural", "city", "blender"],
        likes=567,
        comments=89,
        shares=120,
        views=12400,
        created_at=datetime.now() - timedelta(days=1),
        is_featured=True,
    ),
    ContentItem(
        content_id="c004",
        title="Best Practices for Texture Optimization",
        author_id="u102",
        category=ContentCategory.TUTORIAL,
        quality=ContentQuality.GOOD,
        tags=["textures", "optimization", "performance"],
        likes=210,
        comments=34,
        shares=19,
        views=3400,
        created_at=datetime.now() - timedelta(days=2),
    ),
    ContentItem(
        content_id="c005",
        title="Community Discussion: Future of Real-Time Rendering",
        author_id="u401",
        category=ContentCategory.DISCUSSION,
        quality=ContentQuality.AVERAGE,
        tags=["rendering", "discussion", "future"],
        likes=98,
        comments=210,
        shares=12,
        views=4100,
        created_at=datetime.now() - timedelta(hours=6),
    ),
    ContentItem(
        content_id="c006",
        title="Weekly News Roundup – October 2026",
        author_id="u501",
        category=ContentCategory.NEWS,
        quality=ContentQuality.GOOD,
        tags=["news", "weekly", "industry"],
        likes=145,
        comments=22,
        shares=67,
        views=6700,
        created_at=datetime.now() - timedelta(hours=1),
    ),
    ContentItem(
        content_id="c007",
        title="Quick Tip: Lighting Setups for Interior Scenes",
        author_id="u103",
        category=ContentCategory.TUTORIAL,
        quality=ContentQuality.EXCELLENT,
        tags=["lighting", "interior", "quick-tip"],
        likes=278,
        comments=41,
        shares=33,
        views=4800,
        created_at=datetime.now() - timedelta(hours=8),
    ),
    ContentItem(
        content_id="c008",
        title="Showcase: Hand-Painted Texture Pack",
        author_id="u311",
        category=ContentCategory.SHOWCASE,
        quality=ContentQuality.GOOD,
        tags=["textures", "hand-painted", "art"],
        likes=195,
        comments=28,
        shares=15,
        views=3200,
        created_at=datetime.now() - timedelta(days=3),
    ),
    ContentItem(
        content_id="c009",
        title="Review: Budget Laptops for Game Dev in 2026",
        author_id="u206",
        category=ContentCategory.REVIEW,
        quality=ContentQuality.AVERAGE,
        tags=["laptop", "budget", "game-dev"],
        likes=112,
        comments=78,
        shares=22,
        views=5600,
        created_at=datetime.now() - timedelta(days=1, hours=4),
    ),
    ContentItem(
        content_id="c010",
        title="Discussion: Open Source vs Proprietary Tools",
        author_id="u402",
        category=ContentCategory.DISCUSSION,
        quality=ContentQuality.GOOD,
        tags=["open-source", "tools", "debate"],
        likes=167,
        comments=195,
        shares=31,
        views=7300,
        created_at=datetime.now() - timedelta(hours=18),
    ),
    ContentItem(
        content_id="c011",
        title="Tutorial: Rigging Characters for Animation",
        author_id="u104",
        category=ContentCategory.TUTORIAL,
        quality=ContentQuality.EXCELLENT,
        tags=["rigging", "animation", "characters"],
        likes=423,
        comments=67,
        shares=54,
        views=9100,
        created_at=datetime.now() - timedelta(hours=5),
        is_featured=True,
    ),
    ContentItem(
        content_id="c012",
        title="Showcase: Photorealistic Forest Environment",
        author_id="u312",
        category=ContentCategory.SHOWCASE,
        quality=ContentQuality.EXCELLENT,
        tags=["environment", "photorealistic", "nature"],
        likes=612,
        comments=94,
        shares=145,
        views=15200,
        created_at=datetime.now() - timedelta(hours=2),
        is_featured=True,
    ),
    ContentItem(
        content_id="c013",
        title="News: Major Engine Update Released",
        author_id="u502",
        category=ContentCategory.NEWS,
        quality=ContentQuality.GOOD,
        tags=["engine", "update", "release"],
        likes=234,
        comments=45,
        shares=89,
        views=11000,
        created_at=datetime.now() - timedelta(hours=4),
    ),
    ContentItem(
        content_id="c014",
        title="Review: Top 5 Drawing Tablets for Digital Artists",
        author_id="u207",
        category=ContentCategory.REVIEW,
        quality=ContentQuality.BELOW_AVERAGE,
        tags=["tablet", "digital-art", "review"],
        likes=67,
        comments=23,
        shares=8,
        views=2100,
        created_at=datetime.now() - timedelta(days=4),
    ),
    ContentItem(
        content_id="c015",
        title="Discussion: AI-Assisted Content Creation Ethics",
        author_id="u403",
        category=ContentCategory.DISCUSSION,
        quality=ContentQuality.GOOD,
        tags=["ai", "ethics", "creation"],
        likes=189,
        comments=267,
        shares=42,
        views=8400,
        created_at=datetime.now() - timedelta(hours=10),
    ),
]


# ---------------------------------------------------------------------------
# Quality Score Mapping
# ---------------------------------------------------------------------------

_QUALITY_SCORES: dict[ContentQuality, float] = {
    ContentQuality.EXCELLENT: 1.0,
    ContentQuality.GOOD: 0.75,
    ContentQuality.AVERAGE: 0.5,
    ContentQuality.BELOW_AVERAGE: 0.25,
}


# ---------------------------------------------------------------------------
# Community Curation Agent
# ---------------------------------------------------------------------------


class CommunityCurationAgent:
    """Agent responsible for curating and ranking community content."""

    def __init__(self, content_pool: list[ContentItem] | None = None) -> None:
        """Initialize the agent with an optional content pool.

        Args:
            content_pool: List of ContentItem objects to curate from.
                         Defaults to MOCK_CONTENT_DB if not provided.
        """
        self._content_pool: list[ContentItem] = content_pool if content_pool is not None else list(MOCK_CONTENT_DB)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def curate_feed(
        self,
        user_id: str,
        preferences: UserPreferences,
    ) -> list[ContentItem]:
        """Return a curated content feed tailored to the user.

        The curation algorithm considers:
        - User's favorite categories (boosted)
        - Minimum quality threshold
        - Content recency
        - Engagement metrics (likes, comments, shares, views)
        - Content diversity (penalizes over-representation of a category)

        Args:
            user_id: The unique identifier of the user requesting the feed.
            preferences: UserPreferences object defining curation parameters.

        Returns:
            A list of ContentItem objects ordered by relevance score,
            limited to preferences.max_results.
        """
        if not self._content_pool:
            return []

        scored_items: list[tuple[ContentItem, float]] = []

        for item in self._content_pool:
            # Filter by minimum quality
            if _QUALITY_SCORES[item.quality] < _QUALITY_SCORES[preferences.min_quality]:
                continue

            score = self._compute_curation_score(item, preferences)
            scored_items.append((item, score))

        # Sort descending by score
        scored_items.sort(key=lambda pair: pair[1], reverse=True)

        # Apply diversity: limit items per category to avoid monotony
        curated: list[ContentItem] = []
        category_counts: dict[ContentCategory, int] = {}
        max_per_category = max(1, preferences.max_results // 3)

        for item, _score in scored_items:
            if len(curated) >= preferences.max_results:
                break
            cat_count = category_counts.get(item.category, 0)
            if cat_count >= max_per_category:
                continue
            curated.append(item)
            category_counts[item.category] = cat_count + 1

        return curated

    def rank_content(
        self,
        content_ids: list[str],
        criteria: dict[str, Any],
    ) -> list[RankedContent]:
        """Return a ranked list of content based on the given criteria.

        Supported criteria keys:
            - "engagement_weight" (float): Weight for engagement score (default 0.4)
            - "recency_weight" (float): Weight for recency score (default 0.3)
            - "quality_weight" (float): Weight for quality score (default 0.3)
            - "featured_boost" (float): Bonus multiplier for featured items (default 1.2)
            - "tag_filters" (list[str]): Only include content matching at least one tag
            - "category" (ContentCategory): Filter to a single category

        Args:
            content_ids: List of content IDs to rank.
            criteria: Dictionary of ranking criteria and weights.

        Returns:
            A list of RankedContent objects ordered by descending score.
        """
        # Build lookup
        content_lookup: dict[str, ContentItem] = {
            item.content_id: item for item in self._content_pool
        }

        # Filter to requested IDs that exist
        candidates: list[ContentItem] = []
        for cid in content_ids:
            if cid in content_lookup:
                candidates.append(content_lookup[cid])

        # Apply tag filter if specified
        tag_filters: list[str] | None = criteria.get("tag_filters")
        if tag_filters:
            candidates = [
                item for item in candidates
                if any(tag in item.tags for tag in tag_filters)
            ]

        # Apply category filter if specified
        category_filter: ContentCategory | None = criteria.get("category")
        if category_filter is not None:
            candidates = [item for item in candidates if item.category == category_filter]

        # Extract weights
        engagement_weight: float = float(criteria.get("engagement_weight", 0.4))
        recency_weight: float = float(criteria.get("recency_weight", 0.3))
        quality_weight: float = float(criteria.get("quality_weight", 0.3))
        featured_boost: float = float(criteria.get("featured_boost", 1.2))

        # Normalize weights
        total_weight = engagement_weight + recency_weight + quality_weight
        if total_weight <= 0:
            engagement_weight = recency_weight = quality_weight = 1.0 / 3.0
        else:
            engagement_weight /= total_weight
            recency_weight /= total_weight
            quality_weight /= total_weight

        # Compute max values for normalization
        max_engagement = max(
            (self._engagement_score(item) for item in candidates),
            default=1.0,
        )
        max_engagement = max(max_engagement, 1.0)

        now = datetime.now()
        max_age_hours = max(
            ((now - item.created_at).total_seconds() / 3600.0 for item in candidates),
            default=1.0,
        )
        max_age_hours = max(max_age_hours, 1.0)

        ranked: list[RankedContent] = []
        for item in candidates:
            engagement = self._engagement_score(item) / max_engagement
            recency = 1.0 - ((now - item.created_at).total_seconds() / 3600.0) / max_age_hours
            recency = max(0.0, min(1.0, recency))
            quality = _QUALITY_SCORES.get(item.quality, 0.5)

            score = (
                engagement_weight * engagement
                + recency_weight * recency
                + quality_weight * quality
            )

            if item.is_featured:
                score *= featured_boost

            reason_parts: list[str] = []
            if item.is_featured:
                reason_parts.append("featured")
            if engagement > 0.7:
                reason_parts.append("high engagement")
            if recency > 0.8:
                reason_parts.append("recent")
            if quality >= 0.75:
                reason_parts.append("high quality")

            reason = ", ".join(reason_parts) if reason_parts else "standard"

            ranked.append(RankedContent(content=item, score=round(score, 4), rank_reason=reason))

        ranked.sort(key=lambda rc: rc.score, reverse=True)
        return ranked

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _compute_curation_score(
        self,
        item: ContentItem,
        preferences: UserPreferences,
    ) -> float:
        """Compute a single curation score for a content item."""
        # Base engagement score (normalized)
        engagement = self._engagement_score(item) / 100.0
        engagement = min(engagement, 1.0)

        # Recency score (exponential decay over 7 days)
        age_hours = (datetime.now() - item.created_at).total_seconds() / 3600.0
        recency = max(0.0, 1.0 - (age_hours / 168.0))

        # Quality score
        quality = _QUALITY_SCORES.get(item.quality, 0.5)

        # Category preference boost
        category_boost = 1.3 if item.category in preferences.favorite_categories else 1.0

        # Featured boost
        featured_boost = 1.2 if item.is_featured else 1.0

        score = (
            preferences.engagement_weight * engagement
            + preferences.recency_weight * recency
            + (1.0 - preferences.engagement_weight - preferences.recency_weight) * quality
        ) * category_boost * featured_boost

        return round(score, 4)

    @staticmethod
    def _engagement_score(item: ContentItem) -> float:
        """Compute raw engagement score from likes, comments, shares, views."""
        return float(
            item.likes * 3.0
            + item.comments * 5.0
            + item.shares * 8.0
            + item.views * 0.1
        )


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def curate_feed(
    user_id: str,
    preferences: UserPreferences,
) -> list[ContentItem]:
    """Module-level convenience function to curate a content feed.

    Args:
        user_id: The unique identifier of the user.
        preferences: UserPreferences object defining curation parameters.

    Returns:
        A list of ContentItem objects ordered by relevance score.
    """
    agent = CommunityCurationAgent()
    return agent.curate_feed(user_id, preferences)


def rank_content(
    content_ids: list[str],
    criteria: dict[str, Any],
) -> list[RankedContent]:
    """Module-level convenience function to rank content.

    Args:
        content_ids: List of content IDs to rank.
        criteria: Dictionary of ranking criteria and weights.

    Returns:
        A list of RankedContent objects ordered by descending score.
    """
    agent = CommunityCurationAgent()
    return agent.rank_content(content_ids, criteria)
