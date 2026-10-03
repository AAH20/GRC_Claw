"""Content Discovery Agent for UGC Marketplace.

Provides personalized content recommendations and trending content discovery.
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
    """Supported content categories."""

    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    MIXED = "mixed"


class TrendingTimeframe(str, Enum):
    """Supported trending timeframes."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ContentItem:
    """Represents a single content item in the marketplace."""

    content_id: str
    title: str
    creator_id: str
    creator_name: str
    category: ContentCategory
    tags: list[str] = field(default_factory=list)
    likes: int = 0
    views: int = 0
    shares: int = 0
    comments: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    trending_score: float = 0.0
    relevance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "content_id": self.content_id,
            "title": self.title,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "category": self.category.value,
            "tags": self.tags,
            "likes": self.likes,
            "views": self.views,
            "shares": self.shares,
            "comments": self.comments,
            "created_at": self.created_at.isoformat(),
            "trending_score": round(self.trending_score, 4),
            "relevance_score": round(self.relevance_score, 4),
        }


@dataclass
class UserProfile:
    """Represents a user's preference profile."""

    user_id: str
    preferred_categories: list[ContentCategory] = field(default_factory=list)
    followed_creators: list[str] = field(default_factory=list)
    interest_tags: list[str] = field(default_factory=list)
    interaction_history: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

MOCK_CONTENT_POOL: list[ContentItem] = [
    ContentItem(
        content_id="c001",
        title="Sunset Timelapse Over the Mountains",
        creator_id="u101",
        creator_name="NatureLens",
        category=ContentCategory.VIDEO,
        tags=["nature", "timelapse", "mountains", "sunset"],
        likes=12400,
        views=89300,
        shares=2100,
        comments=890,
        created_at=datetime.utcnow() - timedelta(hours=6),
        trending_score=94.2,
    ),
    ContentItem(
        content_id="c002",
        title="Minimalist Interior Design Ideas for Small Spaces",
        creator_id="u102",
        creator_name="DesignDaily",
        category=ContentCategory.IMAGE,
        tags=["interior", "design", "minimalist", "small-spaces"],
        likes=8700,
        views=56200,
        shares=1800,
        comments=640,
        created_at=datetime.utcnow() - timedelta(hours=12),
        trending_score=88.7,
    ),
    ContentItem(
        content_id="c003",
        title="Lo-Fi Beats to Code and Relax",
        creator_id="u103",
        creator_name="ChillDev",
        category=ContentCategory.AUDIO,
        tags=["lofi", "music", "coding", "relax"],
        likes=15600,
        views=120000,
        shares=3400,
        comments=1200,
        created_at=datetime.utcnow() - timedelta(hours=3),
        trending_score=97.1,
    ),
    ContentItem(
        content_id="c004",
        title="The Future of AI-Generated Art",
        creator_id="u104",
        creator_name="ArtTechBlog",
        category=ContentCategory.TEXT,
        tags=["ai", "art", "technology", "future"],
        likes=5400,
        views=34100,
        shares=980,
        comments=420,
        created_at=datetime.utcnow() - timedelta(hours=24),
        trending_score=76.5,
    ),
    ContentItem(
        content_id="c005",
        title="Street Food Tour: Bangkok Back Alleys",
        creator_id="u105",
        creator_name="FoodWanderer",
        category=ContentCategory.VIDEO,
        tags=["food", "travel", "bangkok", "street-food"],
        likes=21300,
        views=156000,
        shares=5600,
        comments=2100,
        created_at=datetime.utcnow() - timedelta(hours=2),
        trending_score=99.3,
    ),
    ContentItem(
        content_id="c006",
        title="Abstract Watercolor Techniques for Beginners",
        creator_id="u106",
        creator_name="WatercolorWise",
        category=ContentCategory.IMAGE,
        tags=["art", "watercolor", "tutorial", "beginner"],
        likes=6800,
        views=42300,
        shares=1200,
        comments=530,
        created_at=datetime.utcnow() - timedelta(hours=18),
        trending_score=82.4,
    ),
    ContentItem(
        content_id="c007",
        title="Ambient Soundscapes for Deep Focus",
        creator_id="u107",
        creator_name="FocusAudio",
        category=ContentCategory.AUDIO,
        tags=["ambient", "focus", "productivity", "soundscape"],
        likes=9200,
        views=67800,
        shares=2100,
        comments=780,
        created_at=datetime.utcnow() - timedelta(hours=8),
        trending_score=85.9,
    ),
    ContentItem(
        content_id="c008",
        title="How I Built a SaaS in 30 Days",
        creator_id="u108",
        creator_name="IndieMaker",
        category=ContentCategory.TEXT,
        tags=["saas", "startup", "coding", "indie"],
        likes=11200,
        views=78900,
        shares=3200,
        comments=1500,
        created_at=datetime.utcnow() - timedelta(hours=10),
        trending_score=91.6,
    ),
    ContentItem(
        content_id="c009",
        title="Drone Footage: Iceland's Hidden Waterfalls",
        creator_id="u109",
        creator_name="AerialExplorer",
        category=ContentCategory.VIDEO,
        tags=["drone", "iceland", "waterfalls", "nature"],
        likes=18700,
        views=134000,
        shares=4800,
        comments=1700,
        created_at=datetime.utcnow() - timedelta(hours=4),
        trending_score=96.8,
    ),
    ContentItem(
        content_id="c010",
        title="Typography Inspiration: 50 Modern Font Pairings",
        creator_id="u110",
        creator_name="TypeDesigner",
        category=ContentCategory.IMAGE,
        tags=["typography", "design", "fonts", "inspiration"],
        likes=7300,
        views=48900,
        shares=1500,
        comments=610,
        created_at=datetime.utcnow() - timedelta(hours=14),
        trending_score=79.3,
    ),
    ContentItem(
        content_id="c011",
        title="Jazz Piano for Late Night Coding Sessions",
        creator_id="u111",
        creator_name="JazzKeys",
        category=ContentCategory.AUDIO,
        tags=["jazz", "piano", "coding", "night"],
        likes=13400,
        views=98700,
        shares=2900,
        comments=1050,
        created_at=datetime.utcnow() - timedelta(hours=5),
        trending_score=93.0,
    ),
    ContentItem(
        content_id="c012",
        title="The Psychology of Color in Branding",
        creator_id="u112",
        creator_name="BrandPsych",
        category=ContentCategory.TEXT,
        tags=["branding", "psychology", "color", "marketing"],
        likes=6100,
        views=41200,
        shares=1100,
        comments=480,
        created_at=datetime.utcnow() - timedelta(hours=20),
        trending_score=74.8,
    ),
    ContentItem(
        content_id="c013",
        title="Macro Photography: Insects in Your Garden",
        creator_id="u113",
        creator_name="MacroWorld",
        category=ContentCategory.IMAGE,
        tags=["photography", "macro", "insects", "nature"],
        likes=9800,
        views=62100,
        shares=1900,
        comments=720,
        created_at=datetime.utcnow() - timedelta(hours=16),
        trending_score=84.1,
    ),
    ContentItem(
        content_id="c014",
        title="Cooking Challenge: 5-Ingredient Gourmet Meals",
        creator_id="u114",
        creator_name="GourmetSimplified",
        category=ContentCategory.VIDEO,
        tags=["cooking", "food", "challenge", "gourmet"],
        likes=16500,
        views=112000,
        shares=4100,
        comments=1800,
        created_at=datetime.utcnow() - timedelta(hours=7),
        trending_score=95.5,
    ),
    ContentItem(
        content_id="c015",
        title="Synthwave Retro-Futuristic Visual Mix",
        creator_id="u115",
        creator_name="RetroVision",
        category=ContentCategory.MIXED,
        tags=["synthwave", "retro", "futuristic", "visual"],
        likes=10900,
        views=73400,
        shares=2600,
        comments=890,
        created_at=datetime.utcnow() - timedelta(hours=9),
        trending_score=87.2,
    ),
]

MOCK_USER_PROFILES: dict[str, UserProfile] = {
    "u001": UserProfile(
        user_id="u001",
        preferred_categories=[ContentCategory.VIDEO, ContentCategory.IMAGE],
        followed_creators=["u101", "u105", "u109"],
        interest_tags=["nature", "travel", "food", "drone"],
        interaction_history=["c001", "c005", "c009", "c014"],
    ),
    "u002": UserProfile(
        user_id="u002",
        preferred_categories=[ContentCategory.AUDIO, ContentCategory.TEXT],
        followed_creators=["u103", "u108", "u111"],
        interest_tags=["coding", "music", "saas", "productivity"],
        interaction_history=["c003", "c008", "c011"],
    ),
    "u003": UserProfile(
        user_id="u003",
        preferred_categories=[ContentCategory.IMAGE, ContentCategory.TEXT],
        followed_creators=["u102", "u104", "u110"],
        interest_tags=["design", "ai", "typography", "art"],
        interaction_history=["c002", "c004", "c010", "c012"],
    ),
    "u004": UserProfile(
        user_id="u004",
        preferred_categories=[ContentCategory.VIDEO],
        followed_creators=["u105", "u114"],
        interest_tags=["food", "cooking", "travel"],
        interaction_history=["c005", "c014"],
    ),
    "u005": UserProfile(
        user_id="u005",
        preferred_categories=[ContentCategory.MIXED, ContentCategory.AUDIO],
        followed_creators=["u107", "u115"],
        interest_tags=["ambient", "focus", "synthwave", "retro"],
        interaction_history=["c007", "c015"],
    ),
}


# ---------------------------------------------------------------------------
# Content Discovery Agent
# ---------------------------------------------------------------------------


class ContentDiscoveryAgent:
    """Agent for discovering and recommending content in the UGC marketplace."""

    def __init__(
        self,
        content_pool: list[ContentItem] | None = None,
        user_profiles: dict[str, UserProfile] | None = None,
    ) -> None:
        """Initialize the agent with content and user data.

        Args:
            content_pool: Pool of available content items. Uses mock data if None.
            user_profiles: User preference profiles. Uses mock data if None.
        """
        self._content_pool = content_pool if content_pool is not None else MOCK_CONTENT_POOL
        self._user_profiles = user_profiles if user_profiles is not None else MOCK_USER_PROFILES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_content(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return personalized content recommendations for a user.

        Recommendations are ranked by a relevance score computed from:
        - Category preference match
        - Followed creator boost
        - Tag interest overlap
        - Content engagement metrics
        - Recency factor

        Args:
            user_id: The unique identifier of the user.
            limit: Maximum number of recommendations to return.

        Returns:
            A list of content item dictionaries, sorted by relevance.

        Raises:
            ValueError: If limit is not a positive integer.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit}")

        profile = self._user_profiles.get(user_id)
        if profile is None:
            # Fallback: return trending content for unknown users
            return self._get_fallback_recommendations(limit)

        scored_items: list[tuple[float, ContentItem]] = []
        interacted_ids = set(profile.interaction_history)

        for item in self._content_pool:
            # Skip already-interacted content
            if item.content_id in interacted_ids:
                continue

            relevance = self._compute_relevance(item, profile)
            scored_items.append((relevance, item))

        # Sort by relevance descending
        scored_items.sort(key=lambda pair: pair[0], reverse=True)

        results: list[dict[str, Any]] = []
        for relevance, item in scored_items[:limit]:
            item.relevance_score = relevance
            results.append(item.to_dict())

        return results

    def trending_content(
        self,
        category: str | ContentCategory | None = None,
        timeframe: str | TrendingTimeframe = TrendingTimeframe.DAILY,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return trending content items.

        Args:
            category: Filter by content category. None returns all categories.
            timeframe: Time window for trending calculation.
            limit: Maximum number of items to return.

        Returns:
            A list of content item dictionaries, sorted by trending score.

        Raises:
            ValueError: If limit is not a positive integer or timeframe is invalid.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit}")

        # Normalize timeframe
        if isinstance(timeframe, str):
            try:
                timeframe = TrendingTimeframe(timeframe.lower())
            except ValueError:
                valid = [t.value for t in TrendingTimeframe]
                raise ValueError(
                    f"Invalid timeframe '{timeframe}'. Valid options: {valid}"
                )

        # Normalize category
        cat_filter: ContentCategory | None = None
        if category is not None:
            if isinstance(category, str):
                try:
                    cat_filter = ContentCategory(category.lower())
                except ValueError:
                    valid = [c.value for c in ContentCategory]
                    raise ValueError(
                        f"Invalid category '{category}'. Valid options: {valid}"
                    )
            else:
                cat_filter = category

        # Filter by category if specified
        candidates = self._content_pool
        if cat_filter is not None:
            candidates = [item for item in candidates if item.category == cat_filter]

        # Apply timeframe decay to trending scores
        now = datetime.utcnow()
        timeframe_hours = {
            TrendingTimeframe.DAILY: 24,
            TrendingTimeframe.WEEKLY: 168,
            TrendingTimeframe.MONTHLY: 720,
        }
        window_hours = timeframe_hours[timeframe]

        scored_items: list[tuple[float, ContentItem]] = []
        for item in candidates:
            age_hours = (now - item.created_at).total_seconds() / 3600.0
            # Recency decay: newer items get a boost within the window
            recency_factor = max(0.0, 1.0 - (age_hours / window_hours))
            # Engagement velocity: interactions per hour since publish
            engagement_velocity = (
                (item.likes + item.shares * 2 + item.comments * 3)
                / max(age_hours, 1.0)
            )
            # Combined trending score
            adjusted_score = (
                item.trending_score * 0.4
                + recency_factor * 30.0
                + min(engagement_velocity * 0.1, 30.0)
            )
            scored_items.append((adjusted_score, item))

        # Sort by adjusted trending score descending
        scored_items.sort(key=lambda pair: pair[0], reverse=True)

        results: list[dict[str, Any]] = []
        for score, item in scored_items[:limit]:
            item.trending_score = score
            results.append(item.to_dict())

        return results

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _compute_relevance(self, item: ContentItem, profile: UserProfile) -> float:
        """Compute a relevance score for a content item given a user profile.

        Args:
            item: The content item to score.
            profile: The user's preference profile.

        Returns:
            A float relevance score (higher is more relevant).
        """
        score = 0.0

        # Category preference (weight: 30)
        if item.category in profile.preferred_categories:
            score += 30.0

        # Followed creator boost (weight: 25)
        if item.creator_id in profile.followed_creators:
            score += 25.0

        # Tag overlap (weight: up to 20)
        if profile.interest_tags and item.tags:
            overlap = len(set(item.tags) & set(profile.interest_tags))
            score += min(overlap * 5.0, 20.0)

        # Engagement score (weight: up to 15)
        engagement = item.likes + item.shares * 2 + item.comments * 3
        score += min(engagement / 1000.0, 15.0)

        # Recency factor (weight: up to 10)
        age_hours = (datetime.utcnow() - item.created_at).total_seconds() / 3600.0
        recency = max(0.0, 1.0 - (age_hours / 168.0))  # 1 week half-life
        score += recency * 10.0

        return round(score, 4)

    def _get_fallback_recommendations(self, limit: int) -> list[dict[str, Any]]:
        """Return fallback recommendations for unknown users.

        Uses trending content as a fallback when no user profile exists.

        Args:
            limit: Maximum number of items to return.

        Returns:
            A list of content item dictionaries.
        """
        sorted_pool = sorted(
            self._content_pool, key=lambda item: item.trending_score, reverse=True
        )
        results: list[dict[str, Any]] = []
        for item in sorted_pool[:limit]:
            item.relevance_score = item.trending_score
            results.append(item.to_dict())
        return results


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_agent = ContentDiscoveryAgent()


def recommend_content(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return personalized content recommendations for a user.

    Args:
        user_id: The unique identifier of the user.
        limit: Maximum number of recommendations to return.

    Returns:
        A list of content item dictionaries, sorted by relevance.
    """
    return _default_agent.recommend_content(user_id, limit)


def trending_content(
    category: str | ContentCategory | None = None,
    timeframe: str | TrendingTimeframe = TrendingTimeframe.DAILY,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return trending content items.

    Args:
        category: Filter by content category. None returns all categories.
        timeframe: Time window for trending calculation.
        limit: Maximum number of items to return.

    Returns:
        A list of content item dictionaries, sorted by trending score.
    """
    return _default_agent.trending_content(category, timeframe, limit)
