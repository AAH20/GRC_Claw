"""Creator Monetization Agent for UGC Marketplace.

Provides earnings calculation and pricing optimization for content creators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class ContentType(str, Enum):
    """Supported content types in the marketplace."""
    VIDEO = "video"
    PHOTO = "photo"
    AUDIO = "audio"
    TEXT = "text"
    LIVE_STREAM = "live_stream"
    TUTORIAL = "tutorial"


class Period(str, Enum):
    """Supported earnings periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class EarningsBreakdown:
    """Detailed earnings breakdown for a creator over a period."""
    creator_id: str
    period: Period
    start_date: date
    end_date: date
    gross_earnings: float
    platform_fee: float
    taxes_withheld: float
    net_earnings: float
    by_content_type: Dict[ContentType, float] = field(default_factory=dict)
    by_source: Dict[str, float] = field(default_factory=dict)
    transaction_count: int = 0
    currency: str = "USD"


@dataclass
class PricingRecommendation:
    """A single pricing recommendation for a content type."""
    content_type: ContentType
    current_avg_price: float
    recommended_price: float
    price_change_pct: float
    confidence: float  # 0.0 - 1.0
    reasoning: str
    competitor_avg: float
    demand_score: float  # 0.0 - 1.0


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

# Simulated creator profiles with historical data
_MOCK_CREATORS: Dict[str, Dict] = {
    "creator_001": {
        "name": "Alice Chen",
        "followers": 125_000,
        "engagement_rate": 0.085,
        "content_types": [ContentType.VIDEO, ContentType.TUTORIAL],
        "base_prices": {
            ContentType.VIDEO: 25.0,
            ContentType.TUTORIAL: 45.0,
        },
        "monthly_views": 2_500_000,
        "conversion_rate": 0.032,
    },
    "creator_002": {
        "name": "Marcus Rivera",
        "followers": 45_000,
        "engagement_rate": 0.12,
        "content_types": [ContentType.PHOTO, ContentType.TEXT],
        "base_prices": {
            ContentType.PHOTO: 12.0,
            ContentType.TEXT: 8.0,
        },
        "monthly_views": 800_000,
        "conversion_rate": 0.045,
    },
    "creator_003": {
        "name": "Sofia Andersson",
        "followers": 310_000,
        "engagement_rate": 0.065,
        "content_types": [ContentType.AUDIO, ContentType.LIVE_STREAM],
        "base_prices": {
            ContentType.AUDIO: 18.0,
            ContentType.LIVE_STREAM: 35.0,
        },
        "monthly_views": 4_200_000,
        "conversion_rate": 0.028,
    },
    "creator_004": {
        "name": "James Okafor",
        "followers": 78_000,
        "engagement_rate": 0.095,
        "content_types": [ContentType.VIDEO, ContentType.PHOTO, ContentType.TEXT],
        "base_prices": {
            ContentType.VIDEO: 20.0,
            ContentType.PHOTO: 10.0,
            ContentType.TEXT: 6.0,
        },
        "monthly_views": 1_500_000,
        "conversion_rate": 0.038,
    },
    "creator_005": {
        "name": "Yuki Tanaka",
        "followers": 520_000,
        "engagement_rate": 0.072,
        "content_types": [ContentType.TUTORIAL, ContentType.LIVE_STREAM],
        "base_prices": {
            ContentType.TUTORIAL: 55.0,
            ContentType.LIVE_STREAM: 40.0,
        },
        "monthly_views": 6_800_000,
        "conversion_rate": 0.022,
    },
}

# Platform fee structure (percentage)
_PLATFORM_FEE_PCT = 0.15
_TAX_RATE = 0.20

# Market demand multipliers by content type (simulated market data)
_MARKET_DEMAND: Dict[ContentType, float] = {
    ContentType.VIDEO: 1.15,
    ContentType.PHOTO: 0.95,
    ContentType.AUDIO: 1.08,
    ContentType.TEXT: 0.88,
    ContentType.LIVE_STREAM: 1.25,
    ContentType.TUTORIAL: 1.35,
}

# Competitor average prices by content type
_COMPETITOR_AVG: Dict[ContentType, float] = {
    ContentType.VIDEO: 22.50,
    ContentType.PHOTO: 11.00,
    ContentType.AUDIO: 16.50,
    ContentType.TEXT: 7.50,
    ContentType.LIVE_STREAM: 32.00,
    ContentType.TUTORIAL: 48.00,
}


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _get_period_dates(period: Period, end: Optional[date] = None) -> tuple[date, date]:
    """Calculate start and end dates for a given period."""
    end = end or date.today()
    if period == Period.DAILY:
        start = end - timedelta(days=1)
    elif period == Period.WEEKLY:
        start = end - timedelta(weeks=1)
    elif period == Period.MONTHLY:
        start = end - timedelta(days=30)
    elif period == Period.QUARTERLY:
        start = end - timedelta(days=90)
    elif period == Period.YEARLY:
        start = end - timedelta(days=365)
    else:
        start = end - timedelta(days=30)
    return start, end


def _generate_mock_transactions(
    creator_id: str,
    period: Period,
    start: date,
    end: date,
) -> List[Dict]:
    """Generate realistic mock transaction data for a creator."""
    import random

    random.seed(hash(f"{creator_id}_{period.value}_{start.isoformat()}"))

    creator = _MOCK_CREATORS.get(creator_id)
    if not creator:
        return []

    num_days = (end - start).days
    base_daily = creator["monthly_views"] / 30.0 * creator["conversion_rate"]

    transactions: List[Dict] = []
    content_types = creator["content_types"]

    for day_offset in range(num_days):
        current_date = start + timedelta(days=day_offset)
        # Add some variance
        daily_transactions = max(0, int(random.gauss(base_daily, base_daily * 0.3)))

        for _ in range(daily_transactions):
            ct = random.choice(content_types)
            base_price = creator["base_prices"].get(ct, 15.0)
            # Price variance ±20%
            price = round(base_price * random.uniform(0.8, 1.2), 2)
            transactions.append({
                "date": current_date.isoformat(),
                "content_type": ct.value,
                "amount": price,
                "source": random.choice(["direct_sale", "subscription", "tip", "licensing"]),
            })

    return transactions


def _aggregate_by_content_type(transactions: List[Dict]) -> Dict[ContentType, float]:
    """Aggregate transaction amounts by content type."""
    result: Dict[ContentType, float] = {}
    for tx in transactions:
        ct = ContentType(tx["content_type"])
        result[ct] = result.get(ct, 0.0) + tx["amount"]
    return {k: round(v, 2) for k, v in result.items()}


def _aggregate_by_source(transactions: List[Dict]) -> Dict[str, float]:
    """Aggregate transaction amounts by revenue source."""
    result: Dict[str, float] = {}
    for tx in transactions:
        src = tx["source"]
        result[src] = result.get(src, 0.0) + tx["amount"]
    return {k: round(v, 2) for k, v in result.items()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_earnings(creator_id: str, period: Period | str) -> EarningsBreakdown:
    """Calculate detailed earnings breakdown for a creator over a period.

    Args:
        creator_id: Unique identifier for the creator.
        period: Earnings period (daily, weekly, monthly, quarterly, yearly).

    Returns:
        EarningsBreakdown with full financial breakdown.

    Raises:
        ValueError: If creator_id is not found or period is invalid.
    """
    if isinstance(period, str):
        try:
            period = Period(period.lower())
        except ValueError:
            valid = ", ".join(p.value for p in Period)
            raise ValueError(f"Invalid period '{period}'. Valid: {valid}")

    if creator_id not in _MOCK_CREATORS:
        raise ValueError(
            f"Creator '{creator_id}' not found. "
            f"Available: {list(_MOCK_CREATORS.keys())}"
        )

    start, end = _get_period_dates(period)
    transactions = _generate_mock_transactions(creator_id, period, start, end)

    gross = sum(tx["amount"] for tx in transactions)
    platform_fee = round(gross * _PLATFORM_FEE_PCT, 2)
    taxes = round((gross - platform_fee) * _TAX_RATE, 2)
    net = round(gross - platform_fee - taxes, 2)

    return EarningsBreakdown(
        creator_id=creator_id,
        period=period,
        start_date=start,
        end_date=end,
        gross_earnings=round(gross, 2),
        platform_fee=platform_fee,
        taxes_withheld=taxes,
        net_earnings=net,
        by_content_type=_aggregate_by_content_type(transactions),
        by_source=_aggregate_by_source(transactions),
        transaction_count=len(transactions),
        currency="USD",
    )


def optimize_pricing(creator_id: str, content_type: ContentType | str) -> PricingRecommendation:
    """Generate pricing optimization recommendation for a creator.

    Analyzes market demand, competitor pricing, and creator engagement
    to recommend an optimal price point.

    Args:
        creator_id: Unique identifier for the creator.
        content_type: The content type to optimize pricing for.

    Returns:
        PricingRecommendation with recommended price and reasoning.

    Raises:
        ValueError: If creator_id or content_type is invalid.
    """
    if isinstance(content_type, str):
        try:
            content_type = ContentType(content_type.lower())
        except ValueError:
            valid = ", ".join(ct.value for ct in ContentType)
            raise ValueError(f"Invalid content_type '{content_type}'. Valid: {valid}")

    if creator_id not in _MOCK_CREATORS:
        raise ValueError(
            f"Creator '{creator_id}' not found. "
            f"Available: {list(_MOCK_CREATORS.keys())}"
        )

    creator = _MOCK_CREATORS[creator_id]
    current_price = creator["base_prices"].get(content_type, 15.0)
    competitor_avg = _COMPETITOR_AVG.get(content_type, current_price)
    demand_mult = _MARKET_DEMAND.get(content_type, 1.0)

    # Engagement bonus: higher engagement → can charge more
    engagement_bonus = creator["engagement_rate"] * 2.0  # up to ~0.24 multiplier

    # Follower scale factor (logarithmic to avoid extreme values)
    import math
    scale_factor = 1.0 + math.log10(max(creator["followers"], 10)) * 0.05

    # Calculate recommended price
    market_anchor = (current_price + competitor_avg) / 2.0
    recommended = market_anchor * demand_mult * (1.0 + engagement_bonus) * scale_factor

    # Clamp to reasonable bounds (±40% of current)
    max_price = current_price * 1.4
    min_price = current_price * 0.6
    recommended = max(min_price, min(max_price, recommended))
    recommended = round(recommended, 2)

    price_change_pct = round(((recommended - current_price) / current_price) * 100, 1)

    # Confidence based on data availability and creator history
    confidence = min(0.95, 0.6 + creator["engagement_rate"] * 2 + 0.1)

    # Demand score
    demand_score = min(1.0, demand_mult * 0.7 + creator["conversion_rate"] * 3)

    # Build reasoning
    reasons: List[str] = []
    if demand_mult > 1.1:
        reasons.append(f"High market demand for {content_type.value} (×{demand_mult:.2f})")
    elif demand_mult < 0.95:
        reasons.append(f"Soft market demand for {content_type.value} (×{demand_mult:.2f})")

    if competitor_avg > current_price * 1.1:
        reasons.append("Competitor pricing suggests room to increase")
    elif competitor_avg < current_price * 0.9:
        reasons.append("Pricing above market average — risk of churn")

    if creator["engagement_rate"] > 0.08:
        reasons.append(f"Strong engagement ({creator['engagement_rate']:.1%}) supports premium pricing")

    if not reasons:
        reasons.append("Pricing aligned with market conditions")

    reasoning = "; ".join(reasons)

    return PricingRecommendation(
        content_type=content_type,
        current_avg_price=current_price,
        recommended_price=recommended,
        price_change_pct=price_change_pct,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        competitor_avg=competitor_avg,
        demand_score=round(demand_score, 2),
    )
