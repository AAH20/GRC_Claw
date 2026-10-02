"""Analysis Agent - Customer segmentation, trend detection, and purchase pattern analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from product_recommendations.agents.data_collection import (
        CustomerBehavior,
        Order,
        Product,
    )

logger = structlog.get_logger(__name__)


class CustomerSegment(BaseModel):
    """Customer segment model."""

    id: str
    name: str
    size: int
    avg_order_value: float
    purchase_frequency: float
    characteristics: dict[str, Any] = Field(default_factory=dict)


class Trend(BaseModel):
    """Trend detection result."""

    product_id: str
    product_title: str
    direction: str  # rising, falling, stable
    confidence: float
    change_percent: float
    period_days: int


class PurchasePattern(BaseModel):
    """Purchase pattern analysis result."""

    pattern_type: str  # frequent_pair, seasonal, category_affinity
    description: str
    confidence: float
    supporting_data: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    segments: list[CustomerSegment] = Field(default_factory=list)
    trends: list[Trend] = Field(default_factory=list)
    patterns: list[PurchasePattern] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class _CustomerStats:
    """Internal customer statistics accumulator."""

    total_spent: float = 0.0
    order_count: int = 0
    behaviors: list[CustomerBehavior] = field(default_factory=list)
    categories: Counter[str] = field(default_factory=Counter)
    products_viewed: Counter[str] = field(default_factory=Counter)
    last_purchase: datetime | None = None


class AnalysisAgent:
    """Agent responsible for analyzing customer data and product performance.

    Performs customer segmentation, trend detection, and purchase pattern
    analysis to feed into the recommendation engine.
    """

    def __init__(
        self,
        min_confidence: float = 0.7,
        max_segments: int = 10,
        trend_lookback_days: int = 30,
    ) -> None:
        """Initialize the Analysis Agent.

        Args:
            min_confidence: Minimum confidence threshold for analysis results.
            max_segments: Maximum number of customer segments to generate.
            trend_lookback_days: Number of days to look back for trend analysis.
        """
        self._min_confidence = min_confidence
        self._max_segments = max_segments
        self._trend_lookback_days = trend_lookback_days

    def analyze(
        self,
        products: list[Product],
        behaviors: list[CustomerBehavior],
        orders: list[Order],
    ) -> AnalysisResult:
        """Run full analysis on collected data.

        Args:
            products: List of products in the catalog.
            behaviors: List of customer behavior events.
            orders: List of orders.

        Returns:
            AnalysisResult with segments, trends, and patterns.
        """
        logger.info(
            "Starting analysis",
            products=len(products),
            behaviors=len(behaviors),
            orders=len(orders),
        )

        segments = self._segment_customers(behaviors, orders)
        trends = self._detect_trends(products, behaviors)
        patterns = self._find_purchase_patterns(orders, products)

        result = AnalysisResult(
            segments=segments,
            trends=trends,
            patterns=patterns,
            summary={
                "total_products": len(products),
                "total_behaviors": len(behaviors),
                "total_orders": len(orders),
                "segments_count": len(segments),
                "trends_detected": len(trends),
                "patterns_found": len(patterns),
            },
        )

        logger.info("Analysis complete", summary=result.summary)
        return result

    def segment_customers(
        self,
        behaviors: list[CustomerBehavior],
        orders: list[Order],
    ) -> list[CustomerSegment]:
        """Segment customers based on behavior and purchase history.

        Args:
            behaviors: Customer behavior events.
            orders: Order history.

        Returns:
            List of customer segments.
        """
        return self._segment_customers(behaviors, orders)

    def detect_trends(
        self,
        products: list[Product],
        behaviors: list[CustomerBehavior],
    ) -> list[Trend]:
        """Detect product trends from behavior data.

        Args:
            products: Product catalog.
            behaviors: Customer behavior events.

        Returns:
            List of detected trends.
        """
        return self._detect_trends(products, behaviors)

    def find_purchase_patterns(
        self,
        orders: list[Order],
        products: list[Product],
    ) -> list[PurchasePattern]:
        """Find patterns in purchase history.

        Args:
            orders: Order history.
            products: Product catalog.

        Returns:
            List of purchase patterns.
        """
        return self._find_purchase_patterns(orders, products)

    def _segment_customers(
        self,
        behaviors: list[CustomerBehavior],
        orders: list[Order],
    ) -> list[CustomerSegment]:
        """Segment customers using RFM-like analysis.

        Args:
            behaviors: Customer behavior events.
            orders: Order history.

        Returns:
            List of customer segments.
        """
        stats: dict[str, _CustomerStats] = defaultdict(_CustomerStats)

        for behavior in behaviors:
            customer_id = behavior.customer_id
            stats[customer_id].behaviors.append(behavior)
            if behavior.event_type == "view":
                stats[customer_id].products_viewed[behavior.product_id] += 1

        for order in orders:
            customer_id = order.customer_id
            stats[customer_id].total_spent += order.total
            stats[customer_id].order_count += 1
            if (
                stats[customer_id].last_purchase is None
                or order.created_at > stats[customer_id].last_purchase
            ):
                stats[customer_id].last_purchase = order.created_at

        if not stats:
            return []

        # Simple segmentation by spend and frequency
        segments: list[CustomerSegment] = []
        high_value: list[str] = []
        frequent: list[str] = []
        at_risk: list[str] = []
        new_customers: list[str] = []

        now = datetime.utcnow()
        for customer_id, s in stats.items():
            avg_order = s.total_spent / s.order_count if s.order_count > 0 else 0
            days_since_last = (
                (now - s.last_purchase).days if s.last_purchase else 999
            )

            if avg_order > 200 and s.order_count >= 3:
                high_value.append(customer_id)
            elif s.order_count >= 5:
                frequent.append(customer_id)
            elif days_since_last > 60 and s.order_count > 0:
                at_risk.append(customer_id)
            elif s.order_count <= 1:
                new_customers.append(customer_id)

        segment_definitions = [
            ("high_value", high_value, "High Value Customers"),
            ("frequent", frequent, "Frequent Buyers"),
            ("at_risk", at_risk, "At Risk Customers"),
            ("new", new_customers, "New Customers"),
        ]

        for seg_id, customer_ids, name in segment_definitions:
            if not customer_ids:
                continue
            total_spent = sum(stats[cid].total_spent for cid in customer_ids)
            total_orders = sum(stats[cid].order_count for cid in customer_ids)
            avg_order = total_spent / total_orders if total_orders > 0 else 0
            frequency = total_orders / len(customer_ids) if customer_ids else 0

            segments.append(
                CustomerSegment(
                    id=seg_id,
                    name=name,
                    size=len(customer_ids),
                    avg_order_value=round(avg_order, 2),
                    purchase_frequency=round(frequency, 2),
                    characteristics={
                        "customer_ids_sample": customer_ids[:10],
                        "total_revenue": round(total_spent, 2),
                    },
                )
            )

        return segments[: self._max_segments]

    def _detect_trends(
        self,
        products: list[Product],
        behaviors: list[CustomerBehavior],
    ) -> list[Trend]:
        """Detect rising/falling product trends.

        Args:
            products: Product catalog.
            behaviors: Customer behavior events.

        Returns:
            List of detected trends.
        """
        cutoff = datetime.utcnow() - timedelta(days=self._trend_lookback_days)
        product_map = {p.id: p for p in products}

        # Count views per product in the lookback period
        view_counts: Counter[str] = Counter()
        for behavior in behaviors:
            if behavior.event_type == "view" and behavior.timestamp >= cutoff:
                view_counts[behavior.product_id] += 1

        if not view_counts:
            return []

        # Calculate trend direction based on view velocity
        avg_views = sum(view_counts.values()) / len(view_counts) if view_counts else 0
        trends: list[Trend] = []

        for product_id, count in view_counts.most_common(20):
            product = product_map.get(product_id)
            if not product:
                continue

            change = ((count - avg_views) / avg_views * 100) if avg_views > 0 else 0
            if abs(change) < 10:
                direction = "stable"
            elif change > 0:
                direction = "rising"
            else:
                direction = "falling"

            confidence = min(abs(change) / 100, 1.0)
            if confidence < self._min_confidence:
                continue

            trends.append(
                Trend(
                    product_id=product_id,
                    product_title=product.title,
                    direction=direction,
                    confidence=round(confidence, 2),
                    change_percent=round(change, 2),
                    period_days=self._trend_lookback_days,
                )
            )

        return trends

    def _find_purchase_patterns(
        self,
        orders: list[Order],
        products: list[Product],
    ) -> list[PurchasePattern]:
        """Find frequent product pairs and category affinities.

        Args:
            orders: Order history.
            products: Product catalog.

        Returns:
            List of purchase patterns.
        """
        product_map = {p.id: p for p in products}
        pair_counts: Counter[tuple[str, str]] = Counter()
        category_pairs: Counter[tuple[str, str]] = Counter()

        for order in orders:
            product_ids = [item.get("product_id", "") for item in order.items]
            product_ids = [pid for pid in product_ids if pid]

            # Count pairs within same order
            for i in range(len(product_ids)):
                for j in range(i + 1, len(product_ids)):
                    pair = tuple(sorted([product_ids[i], product_ids[j]]))
                    pair_counts[pair] += 1

                    p1 = product_map.get(pair[0])
                    p2 = product_map.get(pair[1])
                    if p1 and p2 and p1.category and p2.category:
                        cat_pair = tuple(sorted([p1.category, p2.category]))
                        category_pairs[cat_pair] += 1

        patterns: list[PurchasePattern] = []

        # Frequent product pairs
        for pair, count in pair_counts.most_common(5):
            if count < 2:
                continue
            p1 = product_map.get(pair[0])
            p2 = product_map.get(pair[1])
            patterns.append(
                PurchasePattern(
                    pattern_type="frequent_pair",
                    description=(
                        f"Customers often buy '{p1.title if p1 else pair[0]}' "
                        f"and '{p2.title if p2 else pair[1]}' together"
                    ),
                    confidence=min(count / 10, 1.0),
                    supporting_data={
                        "product_ids": list(pair),
                        "co_occurrence_count": count,
                    },
                )
            )

        # Category affinities
        for cat_pair, count in category_pairs.most_common(3):
            if count < 2:
                continue
            patterns.append(
                PurchasePattern(
                    pattern_type="category_affinity",
                    description=(
                        f"Categories '{cat_pair[0]}' and '{cat_pair[1]}' "
                        "are frequently purchased together"
                    ),
                    confidence=min(count / 10, 1.0),
                    supporting_data={
                        "categories": list(cat_pair),
                        "co_occurrence_count": count,
                    },
                )
            )

        return patterns
