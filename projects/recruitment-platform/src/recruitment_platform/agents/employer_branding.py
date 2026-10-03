"""Employer Branding Agent for the Recruitment Platform.

Provides brand health analysis and content strategy generation
for employers using the recruitment platform.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class BrandHealthTier(Enum):
    """Classification of overall brand health."""

    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


class ContentChannel(Enum):
    """Recommended content distribution channels."""

    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    GLASSDOOR = "glassdoor"
    COMPANY_BLOG = "company_blog"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    PODCAST = "podcast"


class ContentFormat(Enum):
    """Recommended content formats."""

    VIDEO = "video"
    ARTICLE = "article"
    INFOGRAPHIC = "infographic"
    PODCAST_EPISODE = "podcast_episode"
    EMPLOYEE_SPOTLIGHT = "employee_spotlight"
    BEHIND_THE_SCENES = "behind_the_scenes"
    TESTIMONIAL = "testimonial"
    CASE_STUDY = "case_study"


@dataclass
class BrandMetrics:
    """Raw metrics used to compute brand health."""

    glassdoor_rating: float  # 1.0 – 5.0
    review_count: int
    response_rate: float  # 0.0 – 1.0 (employer response rate to reviews)
    social_followers: int
    engagement_rate: float  # 0.0 – 1.0
    career_page_views: int
    application_completion_rate: float  # 0.0 – 1.0
    offer_acceptance_rate: float  # 0.0 – 1.0
    employee_advocacy_score: float  # 0.0 – 1.0
    time_to_fill_days: float
    diversity_index: float  # 0.0 – 1.0


@dataclass
class BrandHealthScore:
    """Result of a brand health analysis."""

    employer_id: str
    overall_score: float  # 0 – 100
    tier: BrandHealthTier
    metrics: BrandMetrics
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    benchmark_percentile: float = 0.0  # vs industry peers


@dataclass
class ContentRecommendation:
    """A single content strategy recommendation."""

    title: str
    description: str
    channel: ContentChannel
    format: ContentFormat
    priority: int  # 1 (highest) – 5 (lowest)
    expected_impact: str
    suggested_cadence: str  # e.g. "weekly", "bi-weekly", "monthly"


@dataclass
class ContentStrategy:
    """Full content strategy derived from a brand analysis."""

    employer_id: str
    brand_score: BrandHealthScore
    recommendations: list[ContentRecommendation] = field(default_factory=list)
    content_pillars: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    estimated_reach_increase: str = ""


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

_MOCK_EMPLOYER_PROFILES: dict[str, dict[str, Any]] = {
    "emp_001": {
        "name": "TechNova Solutions",
        "industry": "Software Development",
        "size": "500-1000",
        "metrics": BrandMetrics(
            glassdoor_rating=4.2,
            review_count=187,
            response_rate=0.85,
            social_followers=45000,
            engagement_rate=0.038,
            career_page_views=12400,
            application_completion_rate=0.72,
            offer_acceptance_rate=0.68,
            employee_advocacy_score=0.71,
            time_to_fill_days=32.0,
            diversity_index=0.64,
        ),
    },
    "emp_002": {
        "name": "GreenLeaf Analytics",
        "industry": "Data & Analytics",
        "size": "50-200",
        "metrics": BrandMetrics(
            glassdoor_rating=3.6,
            review_count=42,
            response_rate=0.45,
            social_followers=8200,
            engagement_rate=0.021,
            career_page_views=3100,
            application_completion_rate=0.55,
            offer_acceptance_rate=0.52,
            employee_advocacy_score=0.48,
            time_to_fill_days=58.0,
            diversity_index=0.41,
        ),
    },
    "emp_003": {
        "name": "HealthBridge Medical",
        "industry": "Healthcare",
        "size": "1000-5000",
        "metrics": BrandMetrics(
            glassdoor_rating=4.6,
            review_count=523,
            response_rate=0.92,
            social_followers=120000,
            engagement_rate=0.055,
            career_page_views=28900,
            application_completion_rate=0.81,
            offer_acceptance_rate=0.79,
            employee_advocacy_score=0.83,
            time_to_fill_days=24.0,
            diversity_index=0.78,
        ),
    },
}

_INDUSTRY_BENCHMARKS: dict[str, dict[str, float]] = {
    "Software Development": {
        "glassdoor_rating": 3.8,
        "response_rate": 0.65,
        "engagement_rate": 0.030,
        "application_completion_rate": 0.65,
        "offer_acceptance_rate": 0.60,
        "time_to_fill_days": 40.0,
    },
    "Data & Analytics": {
        "glassdoor_rating": 3.9,
        "response_rate": 0.60,
        "engagement_rate": 0.028,
        "application_completion_rate": 0.62,
        "offer_acceptance_rate": 0.58,
        "time_to_fill_days": 45.0,
    },
    "Healthcare": {
        "glassdoor_rating": 3.7,
        "response_rate": 0.55,
        "engagement_rate": 0.025,
        "application_completion_rate": 0.60,
        "offer_acceptance_rate": 0.55,
        "time_to_fill_days": 50.0,
    },
}


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _get_employer_profile(employer_id: str) -> dict[str, Any]:
    """Retrieve employer profile from mock data or generate a synthetic one."""
    if employer_id in _MOCK_EMPLOYER_PROFILES:
        return _MOCK_EMPLOYER_PROFILES[employer_id]

    # Generate a deterministic synthetic profile for unknown IDs
    rng = random.Random(employer_id)
    industries = list(_INDUSTRY_BENCHMARKS.keys())
    industry = industries[rng.randrange(len(industries))]
    return {
        "name": f"Employer {employer_id}",
        "industry": industry,
        "size": "200-500",
        "metrics": BrandMetrics(
            glassdoor_rating=round(rng.uniform(2.8, 4.8), 1),
            review_count=rng.randint(10, 600),
            response_rate=round(rng.uniform(0.2, 0.95), 2),
            social_followers=rng.randint(1000, 150000),
            engagement_rate=round(rng.uniform(0.01, 0.07), 3),
            career_page_views=rng.randint(500, 30000),
            application_completion_rate=round(rng.uniform(0.4, 0.9), 2),
            offer_acceptance_rate=round(rng.uniform(0.35, 0.85), 2),
            employee_advocacy_score=round(rng.uniform(0.3, 0.9), 2),
            time_to_fill_days=round(rng.uniform(15, 70), 1),
            diversity_index=round(rng.uniform(0.3, 0.85), 2),
        ),
    }


def _compute_overall_score(metrics: BrandMetrics) -> float:
    """Compute a 0-100 brand health score from raw metrics."""
    # Weighted scoring model
    score = 0.0

    # Glassdoor rating (weight: 20%) — normalize 1-5 to 0-100
    score += (metrics.glassdoor_rating / 5.0) * 20

    # Response rate (weight: 10%)
    score += metrics.response_rate * 10

    # Engagement rate (weight: 15%) — normalize assuming 8% is excellent
    score += min(metrics.engagement_rate / 0.08, 1.0) * 15

    # Application completion rate (weight: 15%)
    score += metrics.application_completion_rate * 15

    # Offer acceptance rate (weight: 15%)
    score += metrics.offer_acceptance_rate * 15

    # Employee advocacy (weight: 10%)
    score += metrics.employee_advocacy_score * 10

    # Time to fill (weight: 10%) — lower is better; 15 days = perfect, 70+ = 0
    ttf_score = max(0.0, 1.0 - (metrics.time_to_fill_days - 15) / 55)
    score += ttf_score * 10

    # Diversity index (weight: 5%)
    score += metrics.diversity_index * 5

    return round(min(max(score, 0.0), 100.0), 1)


def _classify_tier(score: float) -> BrandHealthTier:
    """Map a numeric score to a health tier."""
    if score >= 85:
        return BrandHealthTier.EXCELLENT
    if score >= 70:
        return BrandHealthTier.GOOD
    if score >= 55:
        return BrandHealthTier.MODERATE
    if score >= 40:
        return BrandHealthTier.NEEDS_IMPROVEMENT
    return BrandHealthTier.CRITICAL


def _identify_strengths(metrics: BrandMetrics) -> list[str]:
    """Identify brand strengths from metrics."""
    strengths: list[str] = []
    if metrics.glassdoor_rating >= 4.0:
        strengths.append(f"Strong Glassdoor rating ({metrics.glassdoor_rating}/5.0)")
    if metrics.response_rate >= 0.75:
        strengths.append(f"High review response rate ({metrics.response_rate:.0%})")
    if metrics.engagement_rate >= 0.04:
        strengths.append(f"Above-average social engagement ({metrics.engagement_rate:.1%})")
    if metrics.application_completion_rate >= 0.70:
        strengths.append(f"High application completion ({metrics.application_completion_rate:.0%})")
    if metrics.offer_acceptance_rate >= 0.70:
        strengths.append(f"Strong offer acceptance rate ({metrics.offer_acceptance_rate:.0%})")
    if metrics.employee_advocacy_score >= 0.70:
        strengths.append("Strong employee advocacy program")
    if metrics.time_to_fill_days <= 30:
        strengths.append(f"Fast time-to-fill ({metrics.time_to_fill_days:.0f} days)")
    if metrics.diversity_index >= 0.65:
        strengths.append("Above-average diversity metrics")
    return strengths


def _identify_weaknesses(metrics: BrandMetrics) -> list[str]:
    """Identify brand weaknesses from metrics."""
    weaknesses: list[str] = []
    if metrics.glassdoor_rating < 3.5:
        weaknesses.append(f"Low Glassdoor rating ({metrics.glassdoor_rating}/5.0)")
    if metrics.response_rate < 0.50:
        weaknesses.append(f"Low review response rate ({metrics.response_rate:.0%})")
    if metrics.engagement_rate < 0.025:
        weaknesses.append(f"Below-average social engagement ({metrics.engagement_rate:.1%})")
    if metrics.application_completion_rate < 0.55:
        weaknesses.append(f"Low application completion ({metrics.application_completion_rate:.0%})")
    if metrics.offer_acceptance_rate < 0.50:
        weaknesses.append(f"Low offer acceptance rate ({metrics.offer_acceptance_rate:.0%})")
    if metrics.employee_advocacy_score < 0.50:
        weaknesses.append("Weak employee advocacy")
    if metrics.time_to_fill_days > 50:
        weaknesses.append(f"Slow time-to-fill ({metrics.time_to_fill_days:.0f} days)")
    if metrics.diversity_index < 0.45:
        weaknesses.append("Below-average diversity metrics")
    return weaknesses


def _compute_benchmark_percentile(
    metrics: BrandMetrics, industry: str
) -> float:
    """Compute percentile vs industry peers (simulated)."""
    benchmarks = _INDUSTRY_BENCHMARKS.get(industry)
    if benchmarks is None:
        return 50.0

    # Simple comparison: count how many metrics beat the benchmark
    wins = 0
    total = 0

    total += 1
    if metrics.glassdoor_rating >= benchmarks["glassdoor_rating"]:
        wins += 1

    total += 1
    if metrics.response_rate >= benchmarks["response_rate"]:
        wins += 1

    total += 1
    if metrics.engagement_rate >= benchmarks["engagement_rate"]:
        wins += 1

    total += 1
    if metrics.application_completion_rate >= benchmarks["application_completion_rate"]:
        wins += 1

    total += 1
    if metrics.offer_acceptance_rate >= benchmarks["offer_acceptance_rate"]:
        wins += 1

    total += 1
    if metrics.time_to_fill_days <= benchmarks["time_to_fill_days"]:
        wins += 1

    return round((wins / total) * 100, 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_brand(employer_id: str) -> BrandHealthScore:
    """Analyze employer brand health and return a comprehensive score.

    Args:
        employer_id: Unique identifier for the employer.

    Returns:
        BrandHealthScore containing overall score, tier, metrics,
        strengths, weaknesses, and benchmark percentile.
    """
    profile = _get_employer_profile(employer_id)
    metrics: BrandMetrics = profile["metrics"]
    industry: str = profile["industry"]

    overall_score = _compute_overall_score(metrics)
    tier = _classify_tier(overall_score)
    strengths = _identify_strengths(metrics)
    weaknesses = _identify_weaknesses(metrics)
    percentile = _compute_benchmark_percentile(metrics, industry)

    return BrandHealthScore(
        employer_id=employer_id,
        overall_score=overall_score,
        tier=tier,
        metrics=metrics,
        strengths=strengths,
        weaknesses=weaknesses,
        benchmark_percentile=percentile,
    )


def generate_content_strategy(
    brand_analysis: BrandHealthScore,
) -> ContentStrategy:
    """Generate a content strategy based on brand health analysis.

    Args:
        brand_analysis: The BrandHealthScore returned by analyze_brand().

    Returns:
        ContentStrategy with prioritized recommendations, content pillars,
        target audience, and estimated reach increase.
    """
    metrics = brand_analysis.metrics
    score = brand_analysis.overall_score
    tier = brand_analysis.tier

    recommendations: list[ContentRecommendation] = []
    content_pillars: list[str] = []
    target_audience: list[str] = []

    # --- Strategy based on tier and weaknesses ---

    if metrics.glassdoor_rating < 3.5 or metrics.response_rate < 0.50:
        recommendations.append(
            ContentRecommendation(
                title="Review Response Campaign",
                description=(
                    "Launch a campaign showcasing how the company responds to "
                    "candidate and employee feedback. Highlight specific changes "
                    "made based on reviews."
                ),
                channel=ContentChannel.GLASSDOOR,
                format=ContentFormat.ARTICLE,
                priority=1,
                expected_impact="Improve Glassdoor rating by 0.3-0.5 stars within 6 months",
                suggested_cadence="weekly",
            )
        )
        content_pillars.append("Transparency & Responsiveness")

    if metrics.employee_advocacy_score < 0.60:
        recommendations.append(
            ContentRecommendation(
                title="Employee Spotlight Series",
                description=(
                    "Create a weekly employee spotlight series featuring team "
                    "members sharing their growth stories, day-in-the-life "
                    "experiences, and career milestones."
                ),
                channel=ContentChannel.LINKEDIN,
                format=ContentFormat.EMPLOYEE_SPOTLIGHT,
                priority=1,
                expected_impact="Increase employee advocacy score by 15-20%",
                suggested_cadence="weekly",
            )
        )
        content_pillars.append("Employee Voices & Stories")

    if metrics.engagement_rate < 0.030:
        recommendations.append(
            ContentRecommendation(
                title="Behind-the-Scenes Content",
                description=(
                    "Produce behind-the-scenes videos showing office culture, "
                    "team events, and the real day-to-day at the company."
                ),
                channel=ContentChannel.INSTAGRAM,
                format=ContentFormat.BEHIND_THE_SCENES,
                priority=2,
                expected_impact="Boost social engagement rate by 30-50%",
                suggested_cadence="bi-weekly",
            )
        )
        content_pillars.append("Authentic Culture")

    if metrics.diversity_index < 0.50:
        recommendations.append(
            ContentRecommendation(
                title="Diversity & Inclusion Spotlight",
                description=(
                    "Feature D&I initiatives, employee resource groups, and "
                    "commitment stories through video testimonials and articles."
                ),
                channel=ContentChannel.LINKEDIN,
                format=ContentFormat.VIDEO,
                priority=2,
                expected_impact="Improve diversity perception among candidates by 25%",
                suggested_cadence="monthly",
            )
        )
        content_pillars.append("Diversity, Equity & Inclusion")

    if metrics.offer_acceptance_rate < 0.60:
        recommendations.append(
            ContentRecommendation(
                title="Compensation & Benefits Transparency",
                description=(
                    "Create content explaining compensation philosophy, total "
                    "rewards packages, and unique benefits that differentiate "
                    "the employer."
                ),
                channel=ContentChannel.COMPANY_BLOG,
                format=ContentFormat.INFOGRAPHIC,
                priority=2,
                expected_impact="Increase offer acceptance rate by 10-15%",
                suggested_cadence="quarterly",
            )
        )
        content_pillars.append("Total Rewards & Benefits")

    if metrics.application_completion_rate < 0.60:
        recommendations.append(
            ContentRecommendation(
                title="Day-in-the-Life Video Series",
                description=(
                    "Produce short-form videos showing what a typical day looks "
                    "like for different roles, reducing uncertainty for candidates."
                ),
                channel=ContentChannel.TIKTOK,
                format=ContentFormat.VIDEO,
                priority=3,
                expected_impact="Increase application completion rate by 15-20%",
                suggested_cadence="bi-weekly",
            )
        )
        content_pillars.append("Role Clarity & Expectations")

    if metrics.time_to_fill_days > 45:
        recommendations.append(
            ContentRecommendation(
                title="Hiring Process Transparency",
                description=(
                    "Create content explaining the interview process, timeline, "
                    "and what candidates can expect at each stage."
                ),
                channel=ContentChannel.COMPANY_BLOG,
                format=ContentFormat.ARTICLE,
                priority=3,
                expected_impact="Reduce candidate drop-off by 20%",
                suggested_cadence="monthly",
            )
        )
        content_pillars.append("Candidate Experience")

    # Always add a thought leadership piece for strong brands
    if tier in (BrandHealthTier.EXCELLENT, BrandHealthTier.GOOD):
        recommendations.append(
            ContentRecommendation(
                title="Industry Thought Leadership",
                description=(
                    "Publish articles and insights from leadership on industry "
                    "trends, innovation, and the company's vision for the future."
                ),
                channel=ContentChannel.LINKEDIN,
                format=ContentFormat.ARTICLE,
                priority=3,
                expected_impact="Strengthen employer brand as industry leader",
                suggested_cadence="bi-weekly",
            )
        )
        content_pillars.append("Innovation & Vision")

    # Ensure we have at least some pillars
    if not content_pillars:
        content_pillars = [
            "Company Culture",
            "Career Growth",
            "Employee Stories",
            "Industry Insights",
        ]

    # Target audience based on metrics
    target_audience = _derive_target_audience(metrics, tier)

    # Estimated reach increase
    estimated_reach = _estimate_reach_increase(score, len(recommendations))

    return ContentStrategy(
        employer_id=brand_analysis.employer_id,
        brand_score=brand_analysis,
        recommendations=recommendations,
        content_pillars=content_pillars,
        target_audience=target_audience,
        estimated_reach_increase=estimated_reach,
    )


def _derive_target_audience(
    metrics: BrandMetrics, tier: BrandHealthTier
) -> list[str]:
    """Derive target audience segments from brand metrics."""
    audience: list[str] = ["Active job seekers", "Passive candidates"]

    if metrics.diversity_index < 0.55:
        audience.append("Diverse talent communities")
    if metrics.employee_advocacy_score >= 0.65:
        audience.append("Employee referrals")
    if tier in (BrandHealthTier.EXCELLENT, BrandHealthTier.GOOD):
        audience.append("Industry thought leaders")
    if metrics.time_to_fill_days > 40:
        audience.append("Hard-to-fill specialty roles")

    return audience


def _estimate_reach_increase(score: float, num_recommendations: int) -> str:
    """Estimate potential reach increase from implementing strategy."""
    if score >= 80:
        base = "15-25%"
    elif score >= 65:
        base = "25-40%"
    elif score >= 50:
        base = "40-60%"
    else:
        base = "60-100%"

    # More recommendations = more potential reach
    multiplier = min(num_recommendations / 5, 2.0)
    if multiplier > 1.0:
        return f"{base} (up to {int(multiplier * 100)}% with full implementation)"
    return base


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

__all__ = [
    "analyze_brand",
    "generate_content_strategy",
    "BrandHealthScore",
    "BrandHealthTier",
    "BrandMetrics",
    "ContentRecommendation",
    "ContentStrategy",
    "ContentChannel",
    "ContentFormat",
]
