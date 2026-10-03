"""
Creator Analytics Agent for UGC Marketplace.

Provides comprehensive creator metrics and comparative analysis
using realistic mock data for development and testing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class EngagementMetrics:
    """Engagement-related metrics for a creator."""

    likes: int
    comments: int
    shares: int
    saves: int
    views: int
    engagement_rate: float  # percentage


@dataclass
class ContentMetrics:
    """Content production metrics for a creator."""

    total_posts: int
    posts_this_period: int
    avg_posts_per_week: float
    top_performing_post_id: str | None
    top_performing_post_views: int
    content_categories: dict[str, int]  # category -> post count


@dataclass
class AudienceMetrics:
    """Audience growth and demographics for a creator."""

    total_followers: int
    new_followers: int
    follower_growth_rate: float  # percentage
    audience_age_distribution: dict[str, float]  # age bracket -> percentage
    top_countries: dict[str, float]  # country code -> percentage
    gender_split: dict[str, float]  # gender -> percentage


@dataclass
class RevenueMetrics:
    """Revenue and monetization metrics for a creator."""

    total_revenue: float
    revenue_this_period: float
    avg_revenue_per_post: float
    brand_deals_count: int
    brand_deals_revenue: float
    affiliate_revenue: float
    subscription_revenue: float


@dataclass
class CreatorMetrics:
    """Comprehensive metrics bundle for a single creator."""

    creator_id: str
    creator_name: str
    period: str
    generated_at: datetime
    engagement: EngagementMetrics
    content: ContentMetrics
    audience: AudienceMetrics
    revenue: RevenueMetrics
    overall_score: float  # 0-100 composite score
    percentile_rank: float  # 0-100, relative to platform


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

_MOCK_CREATOR_NAMES: dict[str, str] = {
    "CR001": "Aisha Patel",
    "CR002": "Marcus Chen",
    "CR003": "Sofia Rodriguez",
    "CR004": "James Okafor",
    "CR005": "Yuki Tanaka",
    "CR006": "Elena Volkov",
    "CR007": "David Kim",
    "CR008": "Priya Sharma",
    "CR009": "Lucas Silva",
    "CR010": "Amara Osei",
}

_MOCK_CATEGORIES: list[str] = [
    "fashion",
    "beauty",
    "fitness",
    "food",
    "travel",
    "tech",
    "lifestyle",
    "gaming",
]

_MOCK_COUNTRIES: list[str] = [
    "US",
    "GB",
    "DE",
    "FR",
    "JP",
    "BR",
    "IN",
    "AU",
]

_MOCK_AGE_BRACKETS: list[str] = [
    "13-17",
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55+",
]


def _seeded_random(creator_id: str) -> random.Random:
    """Return a deterministic RNG seeded by creator_id for reproducible mock data."""
    return random.Random(f"creator-analytics-{creator_id}")


def _generate_engagement(rng: random.Random) -> EngagementMetrics:
    """Generate realistic engagement metrics."""
    views = rng.randint(50_000, 2_000_000)
    likes = int(views * rng.uniform(0.03, 0.12))
    comments = int(likes * rng.uniform(0.05, 0.20))
    shares = int(likes * rng.uniform(0.02, 0.10))
    saves = int(likes * rng.uniform(0.01, 0.08))
    engagement_rate = round(((likes + comments + shares + saves) / max(views, 1)) * 100, 2)

    return EngagementMetrics(
        likes=likes,
        comments=comments,
        shares=shares,
        saves=saves,
        views=views,
        engagement_rate=engagement_rate,
    )


def _generate_content(rng: random.Random) -> ContentMetrics:
    """Generate realistic content production metrics."""
    total_posts = rng.randint(50, 2000)
    posts_this_period = rng.randint(1, 40)
    avg_posts_per_week = round(posts_this_period / 4.0, 1)

    categories: dict[str, int] = {}
    remaining = total_posts
    for i, cat in enumerate(_MOCK_CATEGORIES):
        if i == len(_MOCK_CATEGORIES) - 1:
            categories[cat] = remaining
        else:
            count = rng.randint(0, remaining // 2)
            categories[cat] = count
            remaining -= count

    return ContentMetrics(
        total_posts=total_posts,
        posts_this_period=posts_this_period,
        avg_posts_per_week=avg_posts_per_week,
        top_performing_post_id=f"POST-{rng.randint(10000, 99999)}",
        top_performing_post_views=rng.randint(100_000, 5_000_000),
        content_categories=categories,
    )


def _generate_audience(rng: random.Random) -> AudienceMetrics:
    """Generate realistic audience metrics."""
    total_followers = rng.randint(10_000, 5_000_000)
    new_followers = rng.randint(100, 50_000)
    growth_rate = round((new_followers / max(total_followers, 1)) * 100, 2)

    # Age distribution (must sum to ~100)
    raw_weights = [rng.uniform(5, 35) for _ in _MOCK_AGE_BRACKETS]
    total_weight = sum(raw_weights)
    age_dist = {
        bracket: round((w / total_weight) * 100, 1)
        for bracket, w in zip(_MOCK_AGE_BRACKETS, raw_weights)
    }

    # Top countries
    country_weights = [rng.uniform(5, 40) for _ in range(4)]
    total_cw = sum(country_weights)
    top_countries = {
        country: round((w / total_cw) * 100, 1)
        for country, w in zip(rng.sample(_MOCK_COUNTRIES, 4), country_weights)
    }

    # Gender split
    female_pct = round(rng.uniform(30, 70), 1)
    male_pct = round(100 - female_pct - rng.uniform(0, 5), 1)
    other_pct = round(100 - female_pct - male_pct, 1)
    gender_split = {"female": female_pct, "male": male_pct, "other": other_pct}

    return AudienceMetrics(
        total_followers=total_followers,
        new_followers=new_followers,
        follower_growth_rate=growth_rate,
        audience_age_distribution=age_dist,
        top_countries=top_countries,
        gender_split=gender_split,
    )


def _generate_revenue(rng: random.Random, total_posts: int) -> RevenueMetrics:
    """Generate realistic revenue metrics."""
    brand_deals = rng.randint(0, 20)
    brand_revenue = round(rng.uniform(500, 50_000) * brand_deals, 2)
    affiliate_revenue = round(rng.uniform(100, 10_000), 2)
    subscription_revenue = round(rng.uniform(50, 5_000), 2)
    total_revenue = round(brand_revenue + affiliate_revenue + subscription_revenue, 2)

    # Period revenue is a fraction of total
    revenue_this_period = round(total_revenue * rng.uniform(0.1, 0.4), 2)
    avg_revenue_per_post = round(total_revenue / max(total_posts, 1), 2)

    return RevenueMetrics(
        total_revenue=total_revenue,
        revenue_this_period=revenue_this_period,
        avg_revenue_per_post=avg_revenue_per_post,
        brand_deals_count=brand_deals,
        brand_deals_revenue=brand_revenue,
        affiliate_revenue=affiliate_revenue,
        subscription_revenue=subscription_revenue,
    )


def _compute_overall_score(
    engagement: EngagementMetrics,
    audience: AudienceMetrics,
    revenue: RevenueMetrics,
) -> float:
    """Compute a composite 0-100 score from key metrics."""
    # Normalize components to 0-100 scale
    engagement_score = min(engagement.engagement_rate * 5, 100)  # 20% engagement = 100
    growth_score = min(audience.follower_growth_rate * 10, 100)  # 10% growth = 100
    revenue_score = min(revenue.total_revenue / 1000, 100)  # $100k = 100

    # Weighted composite
    score = (engagement_score * 0.4) + (growth_score * 0.3) + (revenue_score * 0.3)
    return round(min(max(score, 0), 100), 1)


def _compute_percentile_rank(score: float) -> float:
    """Map overall score to a percentile rank (simulated)."""
    # Simple sigmoid-like mapping
    import math

    percentile = 100 / (1 + math.exp(-0.1 * (score - 50)))
    return round(min(max(percentile, 1), 99), 1)


def _metrics_to_dict(metrics: CreatorMetrics) -> dict[str, Any]:
    """Convert a CreatorMetrics dataclass to a plain dictionary."""
    return {
        "creator_id": metrics.creator_id,
        "creator_name": metrics.creator_name,
        "period": metrics.period,
        "generated_at": metrics.generated_at.isoformat(),
        "overall_score": metrics.overall_score,
        "percentile_rank": metrics.percentile_rank,
        "engagement": {
            "likes": metrics.engagement.likes,
            "comments": metrics.engagement.comments,
            "shares": metrics.engagement.shares,
            "saves": metrics.engagement.saves,
            "views": metrics.engagement.views,
            "engagement_rate": metrics.engagement.engagement_rate,
        },
        "content": {
            "total_posts": metrics.content.total_posts,
            "posts_this_period": metrics.content.posts_this_period,
            "avg_posts_per_week": metrics.content.avg_posts_per_week,
            "top_performing_post_id": metrics.content.top_performing_post_id,
            "top_performing_post_views": metrics.content.top_performing_post_views,
            "content_categories": metrics.content.content_categories,
        },
        "audience": {
            "total_followers": metrics.audience.total_followers,
            "new_followers": metrics.audience.new_followers,
            "follower_growth_rate": metrics.audience.follower_growth_rate,
            "audience_age_distribution": metrics.audience.audience_age_distribution,
            "top_countries": metrics.audience.top_countries,
            "gender_split": metrics.audience.gender_split,
        },
        "revenue": {
            "total_revenue": metrics.revenue.total_revenue,
            "revenue_this_period": metrics.revenue.revenue_this_period,
            "avg_revenue_per_post": metrics.revenue.avg_revenue_per_post,
            "brand_deals_count": metrics.revenue.brand_deals_count,
            "brand_deals_revenue": metrics.revenue.brand_deals_revenue,
            "affiliate_revenue": metrics.revenue.affiliate_revenue,
            "subscription_revenue": metrics.revenue.subscription_revenue,
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_creator_metrics(creator_id: str, period: str) -> dict[str, Any]:
    """
    Retrieve comprehensive analytics metrics for a single creator.

    Args:
        creator_id: Unique identifier for the creator (e.g., "CR001").
        period: Time period for the metrics (e.g., "7d", "30d", "90d", "1y").

    Returns:
        A dictionary containing engagement, content, audience, and revenue
        metrics along with an overall composite score and percentile rank.

    Raises:
        ValueError: If creator_id is empty or period is not a supported value.
    """
    if not creator_id or not creator_id.strip():
        raise ValueError("creator_id must be a non-empty string")

    supported_periods = {"7d", "30d", "90d", "1y"}
    if period not in supported_periods:
        raise ValueError(
            f"Unsupported period '{period}'. Must be one of: {supported_periods}"
        )

    rng = _seeded_random(creator_id)

    engagement = _generate_engagement(rng)
    content = _generate_content(rng)
    audience = _generate_audience(rng)
    revenue = _generate_revenue(rng, content.total_posts)
    overall_score = _compute_overall_score(engagement, audience, revenue)
    percentile_rank = _compute_percentile_rank(overall_score)

    creator_name = _MOCK_CREATOR_NAMES.get(creator_id, f"Creator {creator_id}")

    metrics = CreatorMetrics(
        creator_id=creator_id,
        creator_name=creator_name,
        period=period,
        generated_at=datetime.utcnow(),
        engagement=engagement,
        content=content,
        audience=audience,
        revenue=revenue,
        overall_score=overall_score,
        percentile_rank=percentile_rank,
    )

    return _metrics_to_dict(metrics)


def compare_creators(creator_ids: list[str]) -> dict[str, Any]:
    """
    Compare multiple creators across key metrics and return a comparative analysis.

    Args:
        creator_ids: List of creator identifiers to compare (max 10).

    Returns:
        A dictionary containing:
            - individual_metrics: Per-creator metric summaries
            - rankings: Creators ranked by overall score
            - category_leaders: Top creator per content category
            - insights: Auto-generated comparative insights

    Raises:
        ValueError: If creator_ids is empty or contains more than 10 IDs.
    """
    if not creator_ids:
        raise ValueError("creator_ids must contain at least one creator ID")
    if len(creator_ids) > 10:
        raise ValueError("Cannot compare more than 10 creators at once")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_ids = [cid for cid in creator_ids if not (cid in seen or seen.add(cid))]

    # Fetch metrics for each creator (using 30d as default comparison period)
    individual_metrics: list[dict[str, Any]] = []
    for cid in unique_ids:
        metrics = get_creator_metrics(cid, "30d")
        individual_metrics.append(metrics)

    # Rank by overall score
    ranked = sorted(individual_metrics, key=lambda m: m["overall_score"], reverse=True)
    rankings: list[dict[str, Any]] = [
        {
            "rank": i + 1,
            "creator_id": m["creator_id"],
            "creator_name": m["creator_name"],
            "overall_score": m["overall_score"],
            "percentile_rank": m["percentile_rank"],
            "total_followers": m["audience"]["total_followers"],
            "engagement_rate": m["engagement"]["engagement_rate"],
            "total_revenue": m["revenue"]["total_revenue"],
        }
        for i, m in enumerate(ranked)
    ]

    # Determine category leaders
    category_leaders: dict[str, dict[str, Any]] = {}
    for m in individual_metrics:
        for category, count in m["content"]["content_categories"].items():
            if category not in category_leaders or count > category_leaders[category]["post_count"]:
                category_leaders[category] = {
                    "creator_id": m["creator_id"],
                    "creator_name": m["creator_name"],
                    "post_count": count,
                }

    # Generate insights
    insights: list[str] = []
    if len(ranked) >= 2:
        top = ranked[0]
        bottom = ranked[-1]
        score_gap = top["overall_score"] - bottom["overall_score"]
        insights.append(
            f"{top['creator_name']} leads with a score of {top['overall_score']}, "
            f"{score_gap:.1f} points ahead of {bottom['creator_name']}."
        )

        # Engagement comparison
        engagement_sorted = sorted(
            individual_metrics, key=lambda m: m["engagement"]["engagement_rate"], reverse=True
        )
        top_eng = engagement_sorted[0]
        insights.append(
            f"Highest engagement rate: {top_eng['creator_name']} at "
            f"{top_eng['engagement']['engagement_rate']}%."
        )

        # Revenue comparison
        revenue_sorted = sorted(
            individual_metrics, key=lambda m: m["revenue"]["total_revenue"], reverse=True
        )
        top_rev = revenue_sorted[0]
        insights.append(
            f"Top earner: {top_rev['creator_name']} with "
            f"${top_rev['revenue']['total_revenue']:,.2f} total revenue."
        )

        # Follower growth
        growth_sorted = sorted(
            individual_metrics,
            key=lambda m: m["audience"]["follower_growth_rate"],
            reverse=True,
        )
        top_growth = growth_sorted[0]
        insights.append(
            f"Fastest growing: {top_growth['creator_name']} at "
            f"{top_growth['audience']['follower_growth_rate']}% follower growth."
        )

    return {
        "comparison_period": "30d",
        "creators_compared": len(unique_ids),
        "individual_metrics": individual_metrics,
        "rankings": rankings,
        "category_leaders": category_leaders,
        "insights": insights,
    }
