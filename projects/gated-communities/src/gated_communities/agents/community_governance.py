"""Community governance agent for gated communities.

Provides governance evaluation and policy recommendation capabilities
using realistic mock data for community health assessment.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GovernanceScore:
    """Result of evaluating a community's governance health."""

    community_id: str
    overall_score: float  # 0.0 – 100.0
    transparency: float
    participation: float
    enforcement: float
    member_satisfaction: float
    risk_level: str  # "low" | "medium" | "high"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyRecommendation:
    """A single policy recommendation for a community."""

    policy_id: str
    title: str
    description: str
    priority: str  # "low" | "medium" | "high" | "critical"
    category: str  # "moderation" | "transparency" | "engagement" | "safety" | "onboarding"
    expected_impact: str
    implementation_effort: str  # "low" | "medium" | "high"


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_COMMUNITY_DB: dict[str, dict[str, Any]] = {
    "comm_001": {
        "name": "Alpha Builders",
        "members": 1240,
        "active_members": 856,
        "moderators": 8,
        "avg_response_hours": 2.3,
        "transparency_index": 82.5,
        "participation_rate": 69.0,
        "enforcement_consistency": 78.0,
        "member_satisfaction": 4.2,  # out of 5
        "open_incidents": 3,
        "policy_coverage": 0.85,
    },
    "comm_002": {
        "name": "Design Circle",
        "members": 340,
        "active_members": 210,
        "moderators": 3,
        "avg_response_hours": 8.7,
        "transparency_index": 55.0,
        "participation_rate": 61.8,
        "enforcement_consistency": 42.0,
        "member_satisfaction": 3.1,
        "open_incidents": 12,
        "policy_coverage": 0.45,
    },
    "comm_003": {
        "name": "Open Source Hub",
        "members": 5600,
        "active_members": 4100,
        "moderators": 22,
        "avg_response_hours": 1.1,
        "transparency_index": 94.0,
        "participation_rate": 73.2,
        "enforcement_consistency": 91.5,
        "member_satisfaction": 4.7,
        "open_incidents": 1,
        "policy_coverage": 0.96,
    },
}

_DEFAULT_COMMUNITY: dict[str, Any] = {
    "name": "Unknown Community",
    "members": 500,
    "active_members": 300,
    "moderators": 4,
    "avg_response_hours": 5.0,
    "transparency_index": 60.0,
    "participation_rate": 55.0,
    "enforcement_consistency": 58.0,
    "member_satisfaction": 3.5,
    "open_incidents": 6,
    "policy_coverage": 0.60,
}

_POLICY_CATALOG: list[dict[str, Any]] = [
    {
        "policy_id": "POL-001",
        "title": "Publish moderation logs quarterly",
        "description": "Release anonymized moderation action summaries every quarter to build trust.",
        "priority": "high",
        "category": "transparency",
        "expected_impact": "Increase transparency index by 10-15 points",
        "implementation_effort": "low",
    },
    {
        "policy_id": "POL-002",
        "title": "Mandatory onboarding guide for new members",
        "description": "Require new members to complete a community guidelines walkthrough before posting.",
        "priority": "medium",
        "category": "onboarding",
        "expected_impact": "Reduce first-week violations by 30%",
        "implementation_effort": "low",
    },
    {
        "policy_id": "POL-003",
        "title": "Escalation path for moderator decisions",
        "description": "Create a formal appeal process with a 48-hour SLA for moderator action reviews.",
        "priority": "critical",
        "category": "moderation",
        "expected_impact": "Improve enforcement consistency and member satisfaction",
        "implementation_effort": "medium",
    },
    {
        "policy_id": "POL-004",
        "title": "Monthly community town halls",
        "description": "Host monthly open forums where members can voice concerns directly to moderators.",
        "priority": "medium",
        "category": "engagement",
        "expected_impact": "Boost participation rate by 8-12%",
        "implementation_effort": "medium",
    },
    {
        "policy_id": "POL-005",
        "title": "Automated toxicity detection",
        "description": "Deploy ML-based content flagging to assist human moderators in real time.",
        "priority": "high",
        "category": "safety",
        "expected_impact": "Reduce harmful content response time by 60%",
        "implementation_effort": "high",
    },
    {
        "policy_id": "POL-006",
        "title": "Transparent rule-change process",
        "description": "Require 7-day public comment period before any community rule changes take effect.",
        "priority": "medium",
        "category": "transparency",
        "expected_impact": "Increase member trust and reduce churn after policy updates",
        "implementation_effort": "low",
    },
    {
        "policy_id": "POL-007",
        "title": "Moderator burnout prevention rotation",
        "description": "Implement a rotation schedule ensuring no moderator handles more than 20 tickets per week.",
        "priority": "high",
        "category": "moderation",
        "expected_impact": "Sustain enforcement quality and reduce moderator attrition",
        "implementation_effort": "medium",
    },
    {
        "policy_id": "POL-008",
        "title": "Recognition program for positive contributors",
        "description": "Monthly badges and shout-outs for members who consistently help others.",
        "priority": "low",
        "category": "engagement",
        "expected_impact": "Increase active member retention by 5-8%",
        "implementation_effort": "low",
    },
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _lookup_community(community_id: str) -> dict[str, Any]:
    """Return mock community data, falling back to a deterministic default."""
    if community_id in _MOCK_COMMUNITY_DB:
        return _MOCK_COMMUNITY_DB[community_id]
    # Deterministic pseudo-data for unknown IDs so results are reproducible.
    digest = hashlib.sha256(community_id.encode()).hexdigest()
    variant = int(digest[:8], 16) % 40 - 20  # -20..+19
    data = dict(_DEFAULT_COMMUNITY)
    data["name"] = f"Community {community_id}"
    data["transparency_index"] = max(0.0, min(100.0, 60.0 + variant))
    data["participation_rate"] = max(0.0, min(100.0, 55.0 + variant))
    data["enforcement_consistency"] = max(0.0, min(100.0, 58.0 + variant))
    return data


def _compute_risk_level(score: float, open_incidents: int) -> str:
    """Derive a risk level from the overall score and open incidents."""
    if score < 50 or open_incidents > 10:
        return "high"
    if score < 70 or open_incidents > 5:
        return "medium"
    return "low"


def _select_policies(community: dict[str, Any]) -> list[PolicyRecommendation]:
    """Choose relevant policy recommendations based on community weaknesses."""
    recommendations: list[PolicyRecommendation] = []

    if community["transparency_index"] < 70:
        recommendations.append(_to_recommendation(_POLICY_CATALOG[0]))
        recommendations.append(_to_recommendation(_POLICY_CATALOG[5]))

    if community["participation_rate"] < 65:
        recommendations.append(_to_recommendation(_POLICY_CATALOG[3]))
        recommendations.append(_to_recommendation(_POLICY_CATALOG[7]))

    if community["enforcement_consistency"] < 60:
        recommendations.append(_to_recommendation(_POLICY_CATALOG[2]))
        recommendations.append(_to_recommendation(_POLICY_CATALOG[6]))

    if community["open_incidents"] > 5:
        recommendations.append(_to_recommendation(_POLICY_CATALOG[4]))

    if community["member_satisfaction"] < 3.5:
        recommendations.append(_to_recommendation(_POLICY_CATALOG[1]))

    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[PolicyRecommendation] = []
    for rec in recommendations:
        if rec.policy_id not in seen:
            seen.add(rec.policy_id)
            unique.append(rec)

    # If nothing triggered, suggest baseline policies.
    if not unique:
        unique = [
            _to_recommendation(_POLICY_CATALOG[0]),
            _to_recommendation(_POLICY_CATALOG[3]),
            _to_recommendation(_POLICY_CATALOG[7]),
        ]

    return unique


def _to_recommendation(raw: dict[str, Any]) -> PolicyRecommendation:
    """Convert a raw catalog entry into a typed PolicyRecommendation."""
    return PolicyRecommendation(
        policy_id=raw["policy_id"],
        title=raw["title"],
        description=raw["description"],
        priority=raw["priority"],
        category=raw["category"],
        expected_impact=raw["expected_impact"],
        implementation_effort=raw["implementation_effort"],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_governance(community_id: str) -> GovernanceScore:
    """Evaluate the governance health of a community.

    Args:
        community_id: Unique identifier for the community to evaluate.

    Returns:
        A GovernanceScore with sub-scores, overall score, risk level, and details.
    """
    community = _lookup_community(community_id)

    transparency = float(community["transparency_index"])
    participation = float(community["participation_rate"])
    enforcement = float(community["enforcement_consistency"])
    satisfaction = float(community["member_satisfaction"]) * 20.0  # scale to 0-100

    overall = (
        transparency * 0.30
        + participation * 0.25
        + enforcement * 0.25
        + satisfaction * 0.20
    )
    overall = round(max(0.0, min(100.0, overall)), 2)

    open_incidents = int(community["open_incidents"])
    risk = _compute_risk_level(overall, open_incidents)

    details: dict[str, Any] = {
        "community_name": community["name"],
        "total_members": int(community["members"]),
        "active_members": int(community["active_members"]),
        "moderator_count": int(community["moderators"]),
        "avg_response_hours": float(community["avg_response_hours"]),
        "open_incidents": open_incidents,
        "policy_coverage": float(community["policy_coverage"]),
    }

    return GovernanceScore(
        community_id=community_id,
        overall_score=overall,
        transparency=round(transparency, 2),
        participation=round(participation, 2),
        enforcement=round(enforcement, 2),
        member_satisfaction=round(satisfaction, 2),
        risk_level=risk,
        details=details,
    )


def recommend_policies(community_id: str) -> list[PolicyRecommendation]:
    """Generate policy recommendations tailored to a community's weaknesses.

    Args:
        community_id: Unique identifier for the community.

    Returns:
        An ordered list of PolicyRecommendation objects, highest priority first.
    """
    community = _lookup_community(community_id)
    recommendations = _select_policies(community)

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

    return recommendations
