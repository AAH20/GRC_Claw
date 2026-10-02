"""Cross-Sell Agent - Identifies complementary product opportunities and bundle suggestions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from product_recommendations.agents.data_collection import Order, Product

logger = structlog.get_logger(__name__)


class CrossSellSuggestion(BaseModel):
    """A cross-sell suggestion."""

    source_product_id: str
    suggested_product_id: str
    confidence: float
    relationship_type: str  # complementary, upgrade, bundle
    reason: str


class BundleSuggestion(BaseModel):
    """A product bundle suggestion."""

    name: str
    product_ids: list[str]
    total_price: float
    discount_percent: float
    confidence: float
    reason: str


class CrossSellResult(BaseModel):
    """Cross-sell analysis result."""

    suggestions: list[CrossSellSuggestion] = Field(default_factory=list)
    bundles: list[BundleSuggestion] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class CrossSellAgent:
    """Agent that identifies cross-sell and upsell opportunities.

    Analyzes purchase patterns to find complementary products, suggest
    bundles, and identify upgrade opportunities.
    """

    def __init__(
        self,
        max_suggestions: int = 5,
        min_association_confidence: float = 0.5,
        bundle_discount_threshold: float = 0.1,
    ) -> None:
        """Initialize the Cross-Sell Agent.

        Args:
            max_suggestions: Maximum number of cross-sell suggestions.
            min_association_confidence: Minimum confidence for associations.
            bundle_discount_threshold: Minimum discount for bundle suggestions.
        """
        self._max_suggestions = max_suggestions
        self._min_association_confidence = min_association_confidence
        self._bundle_discount_threshold = bundle_discount_threshold

    def find_cross_sell(
        self,
        product_id: str,
        products: list[Product],
        orders: list[Order],
        cart_items: list[str] | None = None,
    ) -> CrossSellResult:
        """Find cross-sell opportunities for a given product.

        Args:
            product_id: The source product ID.
            products: Product catalog.
            orders: Order history.
            cart_items: Optional current cart items.

        Returns:
            CrossSellResult with suggestions and bundles.
        """
        logger.info("Finding cross-sell opportunities", product_id=product_id)

        product_map = {p.id: p for p in products}
        source_product = product_map.get(product_id)
        if not source_product:
            return CrossSellResult(context={"error": "Product not found"})

        # Build association matrix from orders
        associations = self._build_association_matrix(orders)

        suggestions: list[CrossSellSuggestion] = []

        # Direct associations
        if product_id in associations:
            for associated_id, confidence in associations[product_id]:
                associated_product = product_map.get(associated_id)
                if not associated_product:
                    continue
                if confidence < self._min_association_confidence:
                    continue

                relationship = self._classify_relationship(
                    source_product, associated_product
                )
                suggestions.append(
                    CrossSellSuggestion(
                        source_product_id=product_id,
                        suggested_product_id=associated_id,
                        confidence=round(confidence, 4),
                        relationship_type=relationship,
                        reason=self._generate_reason(
                            source_product, associated_product, relationship
                        ),
                    )
                )

        # Category-based suggestions
        category_suggestions = self._find_category_cross_sell(
            source_product, products, orders
        )
        suggestions.extend(category_suggestions)

        # Sort by confidence and limit
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        suggestions = suggestions[: self._max_suggestions]

        # Generate bundle suggestions
        bundles = self._suggest_bundles(source_product, suggestions, products)

        return CrossSellResult(
            suggestions=suggestions,
            bundles=bundles,
            context={
                "source_product": source_product.title,
                "cart_items": cart_items or [],
            },
        )

    def find_upsell(
        self,
        product_id: str,
        products: list[Product],
    ) -> list[CrossSellSuggestion]:
        """Find upsell opportunities (higher-value alternatives).

        Args:
            product_id: The source product ID.
            products: Product catalog.

        Returns:
            List of upsell suggestions.
        """
        product_map = {p.id: p for p in products}
        source = product_map.get(product_id)
        if not source:
            return []

        upsells: list[CrossSellSuggestion] = []
        for product in products:
            if product.id == product_id:
                continue
            if product.category == source.category and product.price > source.price * 1.2:
                price_diff = (product.price - source.price) / source.price
                confidence = min(price_diff, 1.0)
                upsells.append(
                    CrossSellSuggestion(
                        source_product_id=product_id,
                        suggested_product_id=product.id,
                        confidence=round(confidence, 4),
                        relationship_type="upgrade",
                        reason=(
                            f"Upgrade to {product.title} for "
                            f"${product.price - source.price:.2f} more"
                        ),
                    )
                )

        upsells.sort(key=lambda s: s.confidence, reverse=True)
        return upsells[: self._max_suggestions]

    def _build_association_matrix(
        self,
        orders: list[Order],
    ) -> dict[str, list[tuple[str, float]]]:
        """Build product association matrix from order data.

        Args:
            orders: Order history.

        Returns:
            Mapping of product_id to list of (associated_id, confidence).
        """
        pair_counts: Counter[tuple[str, str]] = Counter()
        product_counts: Counter[str] = Counter()

        for order in orders:
            product_ids = list(
                {item.get("product_id", "") for item in order.items if item.get("product_id")}
            )
            for pid in product_ids:
                product_counts[pid] += 1
            for i in range(len(product_ids)):
                for j in range(i + 1, len(product_ids)):
                    pair = tuple(sorted([product_ids[i], product_ids[j]]))
                    pair_counts[pair] += 1

        associations: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for (p1, p2), count in pair_counts.items():
            # Confidence = co-occurrence / occurrences of the less frequent product
            min_count = min(product_counts[p1], product_counts[p2])
            if min_count > 0:
                confidence = count / min_count
                associations[p1].append((p2, confidence))
                associations[p2].append((p1, confidence))

        # Sort by confidence
        for pid in associations:
            associations[pid].sort(key=lambda x: x[1], reverse=True)

        return dict(associations)

    def _classify_relationship(
        self,
        source: Product,
        target: Product,
    ) -> str:
        """Classify the relationship between two products.

        Args:
            source: Source product.
            target: Target product.

        Returns:
            Relationship type string.
        """
        if source.category == target.category:
            if target.price > source.price * 1.2:
                return "upgrade"
            return "complementary"
        return "complementary"

    def _generate_reason(
        self,
        source: Product,
        target: Product,
        relationship: str,
    ) -> str:
        """Generate a human-readable reason for the suggestion.

        Args:
            source: Source product.
            target: Target product.
            relationship: Relationship type.

        Returns:
            Reason string.
        """
        if relationship == "upgrade":
            return f"Upgrade from {source.title} to {target.title}"
        return f"Customers who bought {source.title} also bought {target.title}"

    def _find_category_cross_sell(
        self,
        source: Product,
        products: list[Product],
        orders: list[Order],
    ) -> list[CrossSellSuggestion]:
        """Find cross-sell opportunities from category affinities.

        Args:
            source: Source product.
            products: Product catalog.
            orders: Order history.

        Returns:
            List of cross-sell suggestions.
        """
        if not source.category:
            return []

        # Find categories frequently bought with source category
        category_pairs: Counter[tuple[str, str]] = Counter()
        for order in orders:
            categories_in_order: set[str] = set()
            for item in order.items:
                pid = item.get("product_id", "")
                product = next((p for p in products if p.id == pid), None)
                if product and product.category:
                    categories_in_order.add(product.category)

            if source.category in categories_in_order:
                for cat in categories_in_order:
                    if cat != source.category:
                        pair = tuple(sorted([source.category, cat]))
                        category_pairs[pair] += 1

        suggestions: list[CrossSellSuggestion] = []
        for (cat1, cat2), count in category_pairs.most_common(3):
            target_cat = cat2 if cat1 == source.category else cat1
            # Find top products in target category
            target_products = [p for p in products if p.category == target_cat]
            for product in target_products[:2]:
                confidence = min(count / 10, 1.0)
                if confidence >= self._min_association_confidence:
                    suggestions.append(
                        CrossSellSuggestion(
                            source_product_id=source.id,
                            suggested_product_id=product.id,
                            confidence=round(confidence, 4),
                            relationship_type="complementary",
                            reason=f"Frequently bought with {source.category} items",
                        )
                    )

        return suggestions

    def _suggest_bundles(
        self,
        source: Product,
        suggestions: list[CrossSellSuggestion],
        products: list[Product],
    ) -> list[BundleSuggestion]:
        """Generate bundle suggestions from cross-sell opportunities.

        Args:
            source: Source product.
            suggestions: Cross-sell suggestions.
            products: Product catalog.

        Returns:
            List of bundle suggestions.
        """
        if len(suggestions) < 2:
            return []

        product_map = {p.id: p for p in products}
        bundles: list[BundleSuggestion] = []

        # Create bundles from top suggestions
        for i in range(min(3, len(suggestions) - 1)):
            s1 = suggestions[i]
            s2 = suggestions[i + 1]
            p1 = product_map.get(s1.suggested_product_id)
            p2 = product_map.get(s2.suggested_product_id)
            if not p1 or not p2:
                continue

            total = source.price + p1.price + p2.price
            discount = self._bundle_discount_threshold
            bundle_price = total * (1 - discount)

            bundles.append(
                BundleSuggestion(
                    name=f"{source.title} Bundle",
                    product_ids=[source.id, p1.id, p2.id],
                    total_price=round(bundle_price, 2),
                    discount_percent=round(discount * 100, 1),
                    confidence=round((s1.confidence + s2.confidence) / 2, 4),
                    reason=f"Save {discount * 100:.0f}% when you buy these together",
                )
            )

        return bundles
