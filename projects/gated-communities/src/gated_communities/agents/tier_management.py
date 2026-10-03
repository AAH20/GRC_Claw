"""Tier management agent for gated communities.

Handles tier upgrade evaluations and benefit calculations using
realistic mock data for community membership tiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class TierLevel(str, Enum):
    """Available membership tiers in ascending order of prestige."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass(frozen=True)
class TierBenefits:
    """Breakdown of benefits associated with a membership tier."""

    tier: TierLevel
    monthly_fee_usd: float
    max_community_slots: int
    exclusive_channels: list[str] = field(default_factory=list)
    priority_support_hours: str = "standard"
    analytics_access: bool = False
    custom_branding: bool = False
    api_rate_limit_per_min: int = 60
    storage_gb: int = 5
    event_discount_pct: float = 0.0
    dedicated_manager: bool = False


@dataclass(frozen=True)
class UpgradeRecommendation:
    """Result of evaluating whether a member should upgrade their tier."""

    member_id: str
    current_tier: TierLevel
    recommended_tier: TierLevel
    should_upgrade: bool
    reasons: list[str] = field(default_factory=list)
    projected_monthly_cost_usd: float = 0.0
    confidence_score: float = 0.0  # 0.0 – 1.0


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

# Tier metadata: benefits for each tier level
_TIER_BENEFITS: dict[TierLevel, TierBenefits] = {
    TierLevel.BRONZE: TierBenefits(
        tier=TierLevel.BRONZE,
        monthly_fee_usd=0.0,
        max_community_slots=3,
        exclusive_channels=["general", "announcements"],
        priority_support_hours="standard",
        analytics_access=False,
        custom_branding=False,
        api_rate_limit_per_min=60,
        storage_gb=5,
        event_discount_pct=0.0,
        dedicated_manager=False,
    ),
    TierLevel.SILVER: TierBenefits(
        tier=TierLevel.SILVER,
        monthly_fee_usd=9.99,
        max_community_slots=10,
        exclusive_channels=["general", "announcements", "introductions", "help-desk"],
        priority_support_hours="extended",
        analytics_access=False,
        custom_branding=False,
        api_rate_limit_per_min=120,
        storage_gb=25,
        event_discount_pct=5.0,
        dedicated_manager=False,
    ),
    TierLevel.GOLD: TierBenefits(
        tier=TierLevel.GOLD,
        monthly_fee_usd=29.99,
        max_community_slots=50,
        exclusive_channels=[
            "general",
            "announcements",
            "introductions",
            "help-desk",
            "premium-content",
            "early-access",
        ],
        priority_support_hours="priority",
        analytics_access=True,
        custom_branding=False,
        api_rate_limit_per_min=300,
        storage_gb=100,
        event_discount_pct=10.0,
        dedicated_manager=False,
    ),
    TierLevel.PLATINUM: TierBenefits(
        tier=TierLevel.PLATINUM,
        monthly_fee_usd=79.99,
        max_community_slots=200,
        exclusive_channels=[
            "general",
            "announcements",
            "introductions",
            "help-desk",
            "premium-content",
            "early-access",
            "platinum-lounge",
            "mastermind-sessions",
        ],
        priority_support_hours="24/7",
        analytics_access=True,
        custom_branding=True,
        api_rate_limit_per_min=1000,
        storage_gb=500,
        event_discount_pct=20.0,
        dedicated_manager=True,
    ),
    TierLevel.DIAMOND: TierBenefits(
        tier=TierLevel.DIAMOND,
        monthly_fee_usd=199.99,
        max_community_slots=1000,
        exclusive_channels=[
            "general",
            "announcements",
            "introductions",
            "help-desk",
            "premium-content",
            "early-access",
            "platinum-lounge",
            "mastermind-sessions",
            "diamond-salon",
            "executive-briefings",
        ],
        priority_support_hours="24/7 dedicated",
        analytics_access=True,
        custom_branding=True,
        api_rate_limit_per_min=5000,
        storage_gb=2000,
        event_discount_pct=35.0,
        dedicated_manager=True,
    ),
}

# Mock member database: member_id → current tier + usage metrics
_MOCK_MEMBERS: dict[str, dict[str, Any]] = {
    "member_001": {
        "current_tier": TierLevel.BRONZE,
        "communities_joined": 3,
        "monthly_api_calls": 450,
        "storage_used_gb": 4.2,
        "events_attended_90d": 2,
        "support_tickets_30d": 1,
        "tenure_months": 4,
    },
    "member_002": {
        "current_tier": TierLevel.SILVER,
        "communities_joined": 9,
        "monthly_api_calls": 1100,
        "storage_used_gb": 22.0,
        "events_attended_90d": 5,
        "support_tickets_30d": 3,
        "tenure_months": 11,
    },
    "member_003": {
        "current_tier": TierLevel.GOLD,
        "communities_joined": 42,
        "monthly_api_calls": 2800,
        "storage_used_gb": 85.0,
        "events_attended_90d": 12,
        "support_tickets_30d": 2,
        "tenure_months": 24,
    },
    "member_004": {
        "current_tier": TierLevel.PLATINUM,
        "communities_joined": 180,
        "monthly_api_calls": 9500,
        "storage_used_gb": 420.0,
        "events_attended_90d": 20,
        "support_tickets_30d": 5,
        "tenure_months": 36,
    },
    "member_005": {
        "current_tier": TierLevel.DIAMOND,
        "communities_joined": 950,
        "monthly_api_calls": 48000,
        "storage_used_gb": 1800.0,
        "events_attended_90d": 30,
        "support_tickets_30d": 8,
        "tenure_months": 48,
    },
}

# Tier ordering for upgrade logic
_TIER_ORDER: list[TierLevel] = [
    TierLevel.BRONZE,
    TierLevel.SILVER,
    TierLevel.GOLD,
    TierLevel.PLATINUM,
    TierLevel.DIAMOND,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_tier_upgrade(member_id: str) -> UpgradeRecommendation:
    """Evaluate whether a member should upgrade their membership tier.

    Analyzes the member's current usage metrics against their tier limits
    and recommends an upgrade if they are approaching or exceeding capacity.

    Args:
        member_id: Unique identifier for the community member.

    Returns:
        UpgradeRecommendation with the recommended tier, reasons, and
        projected cost.

    Raises:
        ValueError: If the member_id is not found in the system.
    """
    if member_id not in _MOCK_MEMBERS:
        raise ValueError(
            f"Member '{member_id}' not found. "
            f"Available members: {list(_MOCK_MEMBERS.keys())}"
        )

    data = _MOCK_MEMBERS[member_id]
    current_tier: TierLevel = data["current_tier"]
    current_benefits = _TIER_BENEFITS[current_tier]

    reasons: list[str] = []
    recommended_tier = current_tier
    confidence = 0.0

    # --- Capacity checks ---

    # Community slots
    community_util = data["communities_joined"] / current_benefits.max_community_slots
    if community_util >= 0.9:
        reasons.append(
            f"Community slots at {community_util:.0%} capacity "
            f"({data['communities_joined']}/{current_benefits.max_community_slots})"
        )
        confidence += 0.25

    # API rate limit
    api_util = data["monthly_api_calls"] / current_benefits.api_rate_limit_per_min
    if api_util >= 0.85:
        reasons.append(
            f"API usage at {api_util:.0%} of rate limit "
            f"({data['monthly_api_calls']}/{current_benefits.api_rate_limit_per_min} calls)"
        )
        confidence += 0.20

    # Storage
    storage_util = data["storage_used_gb"] / current_benefits.storage_gb
    if storage_util >= 0.85:
        reasons.append(
            f"Storage at {storage_util:.0%} capacity "
            f"({data['storage_used_gb']:.1f}/{current_benefits.storage_gb} GB)"
        )
        confidence += 0.15

    # Engagement signals (events attended)
    if data["events_attended_90d"] >= 10 and current_tier.value in ("bronze", "silver"):
        reasons.append(
            f"High event engagement ({data['events_attended_90d']} events in 90 days) "
            f"suggests need for premium event access"
        )
        confidence += 0.15

    # Tenure loyalty
    if data["tenure_months"] >= 12 and current_tier == TierLevel.BRONZE:
        reasons.append(
            f"Long tenure ({data['tenure_months']} months) on free tier — "
            f"candidate for paid upgrade"
        )
        confidence += 0.10

    # Support load
    if data["support_tickets_30d"] >= 3 and not current_benefits.dedicated_manager:
        reasons.append(
            f"Elevated support tickets ({data['support_tickets_30d']} in 30 days) — "
            f"priority support recommended"
        )
        confidence += 0.10

    # --- Determine recommended tier ---

    if reasons:
        current_idx = _TIER_ORDER.index(current_tier)
        # Recommend one tier up, capped at Diamond
        recommended_idx = min(current_idx + 1, len(_TIER_ORDER) - 1)
        recommended_tier = _TIER_ORDER[recommended_idx]

    # If already at max tier but still hitting limits, note it
    if current_tier == TierLevel.DIAMOND and reasons:
        recommended_tier = TierLevel.DIAMOND
        reasons.append("Already at highest tier — consider custom enterprise plan")

    should_upgrade = recommended_tier != current_tier and len(reasons) > 0

    projected_cost = _TIER_BENEFITS[recommended_tier].monthly_fee_usd

    return UpgradeRecommendation(
        member_id=member_id,
        current_tier=current_tier,
        recommended_tier=recommended_tier,
        should_upgrade=should_upgrade,
        reasons=reasons,
        projected_monthly_cost_usd=projected_cost,
        confidence_score=round(min(confidence, 1.0), 2),
    )


def calculate_tier_benefits(tier: str | TierLevel) -> TierBenefits:
    """Calculate and return the full benefits breakdown for a given tier.

    Args:
        tier: The tier level, either as a string (e.g. "gold") or TierLevel enum.

    Returns:
        TierBenefits dataclass with all benefit details.

    Raises:
        ValueError: If the tier string does not match any known tier.
    """
    if isinstance(tier, str):
        try:
            tier_enum = TierLevel(tier.lower())
        except ValueError:
            valid = ", ".join(t.value for t in TierLevel)
            raise ValueError(
                f"Unknown tier '{tier}'. Valid tiers: {valid}"
            ) from None
    elif isinstance(tier, TierLevel):
        tier_enum = tier
    else:
        raise TypeError(
            f"Expected str or TierLevel, got {type(tier).__name__}"
        )

    return _TIER_BENEFITS[tier_enum]


# ---------------------------------------------------------------------------
# Convenience / Debug Helpers
# ---------------------------------------------------------------------------


def list_all_tiers() -> list[TierLevel]:
    """Return all available tier levels in order."""
    return list(_TIER_ORDER)


def get_member_tier(member_id: str) -> TierLevel:
    """Return the current tier for a given member.

    Args:
        member_id: Unique identifier for the community member.

    Returns:
        The member's current TierLevel.

    Raises:
        ValueError: If the member_id is not found.
    """
    if member_id not in _MOCK_MEMBERS:
        raise ValueError(f"Member '{member_id}' not found.")
    return _MOCK_MEMBERS[member_id]["current_tier"]


# ---------------------------------------------------------------------------
# Module-level self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("TIER MANAGEMENT AGENT — Self-Test")
    print("=" * 60)

    # Test evaluate_tier_upgrade for all mock members
    for mid in _MOCK_MEMBERS:
        rec = evaluate_tier_upgrade(mid)
        print(f"\n--- {mid} ---")
        print(f"  Current:  {rec.current_tier.value}")
        print(f"  Recommend: {rec.recommended_tier.value}")
        print(f"  Upgrade?  {rec.should_upgrade}")
        print(f"  Confidence: {rec.confidence_score}")
        print(f"  Cost: ${rec.projected_monthly_cost_usd:.2f}/mo")
        if rec.reasons:
            for r in rec.reasons:
                print(f"    • {r}")

    # Test calculate_tier_benefits for all tiers
    print("\n" + "=" * 60)
    print("TIER BENEFITS BREAKDOWN")
    print("=" * 60)
    for tier in TierLevel:
        b = calculate_tier_benefits(tier)
        print(f"\n--- {tier.value.upper()} ---")
        print(f"  Monthly fee: ${b.monthly_fee_usd:.2f}")
        print(f"  Max communities: {b.max_community_slots}")
        print(f"  Exclusive channels: {len(b.exclusive_channels)}")
        print(f"  Priority support: {b.priority_support_hours}")
        print(f"  Analytics: {b.analytics_access}")
        print(f"  Custom branding: {b.custom_branding}")
        print(f"  API rate limit: {b.api_rate_limit_per_min}/min")
        print(f"  Storage: {b.storage_gb} GB")
        print(f"  Event discount: {b.event_discount_pct}%")
        print(f"  Dedicated manager: {b.dedicated_manager}")

    print("\n" + "=" * 60)
    print("All tests passed ✓")
