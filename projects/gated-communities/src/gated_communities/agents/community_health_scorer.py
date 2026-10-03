"""Community Health Scorer Agent for gated communities.

Evaluates community health using engagement, retention, moderation,
and growth metrics. Returns structured scores and risk assessments.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class HealthScoreBreakdown:
    """Detailed breakdown of a community health score."""

    overall_score: float
    engagement_score: float
    retention_score: float
    moderation_score: float
    growth_score: float
    member_count: int
    active_members: int
    posts_last_30d: int
    comments_last_30d: int
    avg_response_time_hours: float
    churn_rate: float
    toxicity_incidents: int
    new_members_30d: int
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RiskFactor:
    """A single identified risk factor for a community."""

    category: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    metric_value: float
    threshold: float
    recommendation: str


# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

_MOCK_COMMUNITIES: dict[str, dict[str, Any]] = {
    "comm_alpha": {
        "member_count": 1520,
        "active_members": 890,
        "posts_last_30d": 342,
        "comments_last_30d": 1876,
        "avg_response_time_hours": 2.3,
        "churn_rate": 0.04,
        "toxicity_incidents": 3,
        "new_members_30d": 120,
    },
    "comm_beta": {
        "member_count": 480,
        "active_members": 120,
        "posts_last_30d": 45,
        "comments_last_30d": 210,
        "avg_response_time_hours": 18.7,
        "churn_rate": 0.22,
        "toxicity_incidents": 12,
        "new_members_30d": 8,
    },
    "comm_gamma": {
        "member_count": 3200,
        "active_members": 2100,
        "posts_last_30d": 890,
        "comments_last_30d": 5400,
        "avg_response_time_hours": 0.8,
        "churn_rate": 0.015,
        "toxicity_incidents": 1,
        "new_members_30d": 310,
    },
    "comm_delta": {
        "member_count": 95,
        "active_members": 12,
        "posts_last_30d": 3,
        "comments_last_30d": 15,
        "avg_response_time_hours": 72.0,
        "churn_rate": 0.45,
        "toxicity_incidents": 5,
        "new_members_30d": 0,
    },
}


def _get_mock_data(community_id: str) -> dict[str, Any]:
    """Retrieve mock data for a community, generating deterministic data for unknown IDs."""
    if community_id in _MOCK_COMMUNITIES:
        return _MOCK_COMMUNITIES[community_id]

    # Deterministic pseudo-random data for unknown community IDs
    rng = random.Random(community_id)
    member_count = rng.randint(50, 5000)
    active_ratio = rng.uniform(0.05, 0.8)
    return {
        "member_count": member_count,
        "active_members": int(member_count * active_ratio),
        "posts_last_30d": rng.randint(0, int(member_count * 0.5)),
        "comments_last_30d": rng.randint(0, int(member_count * 3)),
        "avg_response_time_hours": round(rng.uniform(0.5, 96.0), 1),
        "churn_rate": round(rng.uniform(0.01, 0.5), 3),
        "toxicity_incidents": rng.randint(0, 20),
        "new_members_30d": rng.randint(0, int(member_count * 0.2)),
    }


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_engagement(data: dict[str, Any]) -> float:
    """Score engagement (0-100) based on posts, comments, and response time."""
    member_count = max(data["member_count"], 1)
    posts_per_member = data["posts_last_30d"] / member_count
    comments_per_member = data["comments_last_30d"] / member_count

    # Posts: ideal is ~0.3 posts/member/month
    post_score = min(posts_per_member / 0.3, 1.0) * 40

    # Comments: ideal is ~2 comments/member/month
    comment_score = min(comments_per_member / 2.0, 1.0) * 40

    # Response time: <1h ideal, >48h poor
    response_time = data["avg_response_time_hours"]
    if response_time <= 1.0:
        response_score = 20
    elif response_time >= 48.0:
        response_score = 0
    else:
        response_score = (1 - (response_time - 1) / 47) * 20

    return round(post_score + comment_score + response_score, 2)


def _score_retention(data: dict[str, Any]) -> float:
    """Score retention (0-100) based on churn rate and active member ratio."""
    churn = data["churn_rate"]
    # Churn: <2% excellent, >30% critical
    if churn <= 0.02:
        churn_score = 60
    elif churn >= 0.30:
        churn_score = 0
    else:
        churn_score = (1 - (churn - 0.02) / 0.28) * 60

    member_count = max(data["member_count"], 1)
    active_ratio = data["active_members"] / member_count
    # Active ratio: >50% excellent, <10% poor
    if active_ratio >= 0.5:
        activity_score = 40
    elif active_ratio <= 0.1:
        activity_score = 0
    else:
        activity_score = (active_ratio - 0.1) / 0.4 * 40

    return round(churn_score + activity_score, 2)


def _score_moderation(data: dict[str, Any]) -> float:
    """Score moderation health (0-100) based on toxicity incidents."""
    incidents = data["toxicity_incidents"]
    member_count = max(data["member_count"], 1)
    incident_rate = incidents / member_count

    # Incident rate: 0% ideal, >2% critical
    if incident_rate == 0:
        return 100.0
    elif incident_rate >= 0.02:
        return 0.0
    else:
        return round((1 - incident_rate / 0.02) * 100, 2)


def _score_growth(data: dict[str, Any]) -> float:
    """Score growth (0-100) based on new member acquisition."""
    member_count = max(data["member_count"], 1)
    new_ratio = data["new_members_30d"] / member_count

    # New member ratio: >10% excellent, 0% poor
    if new_ratio >= 0.10:
        return 100.0
    else:
        return round((new_ratio / 0.10) * 100, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_health_score(community_id: str) -> HealthScoreBreakdown:
    """Calculate the overall health score for a community.

    Args:
        community_id: Unique identifier for the community.

    Returns:
        HealthScoreBreakdown with overall score (0-100) and component scores.
    """
    data = _get_mock_data(community_id)

    engagement = _score_engagement(data)
    retention = _score_retention(data)
    moderation = _score_moderation(data)
    growth = _score_growth(data)

    # Weighted overall score
    overall = round(
        engagement * 0.30
        + retention * 0.30
        + moderation * 0.20
        + growth * 0.20,
        2,
    )

    return HealthScoreBreakdown(
        overall_score=overall,
        engagement_score=engagement,
        retention_score=retention,
        moderation_score=moderation,
        growth_score=growth,
        member_count=data["member_count"],
        active_members=data["active_members"],
        posts_last_30d=data["posts_last_30d"],
        comments_last_30d=data["comments_last_30d"],
        avg_response_time_hours=data["avg_response_time_hours"],
        churn_rate=data["churn_rate"],
        toxicity_incidents=data["toxicity_incidents"],
        new_members_30d=data["new_members_30d"],
    )


def identify_risks(community_id: str) -> list[RiskFactor]:
    """Identify risk factors for a community.

    Args:
        community_id: Unique identifier for the community.

    Returns:
        List of RiskFactor objects describing identified risks.
    """
    data = _get_mock_data(community_id)
    risks: list[RiskFactor] = []

    # Churn risk
    churn = data["churn_rate"]
    if churn >= 0.30:
        risks.append(RiskFactor(
            category="retention",
            severity="critical",
            description="Extremely high member churn rate",
            metric_value=churn,
            threshold=0.30,
            recommendation="Conduct exit surveys and implement re-engagement campaigns immediately",
        ))
    elif churn >= 0.15:
        risks.append(RiskFactor(
            category="retention",
            severity="high",
            description="Elevated member churn rate",
            metric_value=churn,
            threshold=0.15,
            recommendation="Analyze churn patterns and improve onboarding experience",
        ))
    elif churn >= 0.08:
        risks.append(RiskFactor(
            category="retention",
            severity="medium",
            description="Moderate member churn rate",
            metric_value=churn,
            threshold=0.08,
            recommendation="Monitor churn trends and enhance community value proposition",
        ))

    # Engagement risk
    member_count = max(data["member_count"], 1)
    active_ratio = data["active_members"] / member_count
    if active_ratio < 0.10:
        risks.append(RiskFactor(
            category="engagement",
            severity="critical",
            description="Critically low active member ratio",
            metric_value=round(active_ratio, 3),
            threshold=0.10,
            recommendation="Launch targeted re-engagement initiatives and content programs",
        ))
    elif active_ratio < 0.25:
        risks.append(RiskFactor(
            category="engagement",
            severity="high",
            description="Low active member ratio",
            metric_value=round(active_ratio, 3),
            threshold=0.25,
            recommendation="Increase interactive content and community events",
        ))

    # Response time risk
    response_time = data["avg_response_time_hours"]
    if response_time >= 48.0:
        risks.append(RiskFactor(
            category="engagement",
            severity="high",
            description="Very slow average response time",
            metric_value=response_time,
            threshold=48.0,
            recommendation="Recruit more moderators and set response time SLAs",
        ))
    elif response_time >= 12.0:
        risks.append(RiskFactor(
            category="engagement",
            severity="medium",
            description="Slow average response time",
            metric_value=response_time,
            threshold=12.0,
            recommendation="Improve moderator coverage during peak hours",
        ))

    # Toxicity risk
    incident_rate = data["toxicity_incidents"] / member_count
    if incident_rate >= 0.02:
        risks.append(RiskFactor(
            category="moderation",
            severity="critical",
            description="High toxicity incident rate",
            metric_value=round(incident_rate, 4),
            threshold=0.02,
            recommendation="Implement stricter moderation policies and automated toxicity detection",
        ))
    elif incident_rate >= 0.005:
        risks.append(RiskFactor(
            category="moderation",
            severity="medium",
            description="Elevated toxicity incident rate",
            metric_value=round(incident_rate, 4),
            threshold=0.005,
            recommendation="Review moderation guidelines and increase moderator presence",
        ))

    # Growth risk
    new_ratio = data["new_members_30d"] / member_count
    if new_ratio == 0:
        risks.append(RiskFactor(
            category="growth",
            severity="high",
            description="No new member acquisition in last 30 days",
            metric_value=0.0,
            threshold=0.01,
            recommendation="Launch referral program and increase community visibility",
        ))
    elif new_ratio < 0.02:
        risks.append(RiskFactor(
            category="growth",
            severity="medium",
            description="Stagnant new member growth",
            metric_value=round(new_ratio, 4),
            threshold=0.02,
            recommendation="Promote community through partnerships and social channels",
        ))

    return risks
