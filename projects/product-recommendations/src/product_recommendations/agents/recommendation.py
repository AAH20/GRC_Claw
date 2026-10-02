"""Recommendation Agent - Personalized product recommendations using collaborative +
content-based filtering."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from product_recommendations.agents.analysis import AnalysisResult
    from product_recommendations.agents.data_collection import (
        CustomerBehavior,
        Order,
        Product,
    )

logger = structlog.get_logger(__name__)


class ScoredProduct(BaseModel):
    """A product with its recommendation score."""

    product: Product
    score: float
    reason: str
    algorithm: str  # collaborative, content_based, trending, hybrid


class RecommendationResult(BaseModel):
    """Recommendation result for a customer."""

    customer_id: str
    recommendations: list[ScoredProduct]
    context: dict[str, Any] = Field(default_factory=dict)
    generated_at: str = Field(
        default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat()
    )


@dataclass
class _UserProfile:
    """Internal user profile for recommendation scoring."""

    viewed_products: Counter[str] = field(default_factory=Counter)
    purchased_products: Counter[str] = field(default_factory=Counter)
    cart_products: Counter[str] = field(default_factory=Counter)
    preferred_categories: Counter[str] = field(default_factory=Counter)
    preferred_tags: Counter[str] = field(default_factory=Counter)


class RecommendationAgent:
    """Agent that generates personalized product recommendations.

    Uses a hybrid approach combining collaborative filtering (user-item
    interactions) and content-based filtering (product attributes).
    """

    def __init__(
        self,
        max_recommendations: int = 10,
        min_score: float = 0.3,
        diversity_factor: float = 0.2,
    ) -> None:
        """Initialize the Recommendation Agent.

        Args:
            max_recommendations: Maximum number of recommendations to return.
            min_score: Minimum score threshold for recommendations.
            diversity_factor: Factor to promote result diversity (0-1).
        """
        self._max_recommendations = max_recommendations
        self._min_score = min_score
        self._diversity_factor = diversity_factor

    def recommend(
        self,
        customer_id: str,
        products: list[Product],
        behaviors: list[CustomerBehavior],
        orders: list[Order],
        analysis: AnalysisResult | None = None,
        context: dict[str, Any] | None = None,
    ) -> RecommendationResult:
        """Generate personalized recommendations for a customer.

        Args:
            customer_id: The customer to generate recommendations for.
            products: Available product catalog.
            behaviors: Customer behavior events.
            orders: Order history.
            analysis: Optional pre-computed analysis result.
            context: Optional additional context (e.g., current cart items).

        Returns:
            RecommendationResult with scored and ranked products.
        """
        logger.info("Generating recommendations", customer_id=customer_id)

        user_profile = self._build_user_profile(customer_id, behaviors, orders)
        candidate_scores: dict[str, tuple[float, str, str]] = {}

        # Content-based scoring
        for product in products:
            score, reason = self._score_content_based(product, user_profile)
            if score >= self._min_score:
                candidate_scores[product.id] = (score, reason, "content_based")

        # Collaborative filtering scoring
        collab_scores = self._score_collaborative(customer_id, products, behaviors, orders)
        for pid, (score, reason) in collab_scores.items():
            if pid in candidate_scores:
                existing_score = candidate_scores[pid][0]
                candidate_scores[pid] = (
                    existing_score * 0.5 + score * 0.5,
                    f"{candidate_scores[pid][1]}; {reason}",
                    "hybrid",
                )
            elif score >= self._min_score:
                candidate_scores[pid] = (score, reason, "collaborative")

        # Apply diversity re-ranking
        ranked = self._apply_diversity(candidate_scores, products)

        scored_products: list[ScoredProduct] = []
        for pid, (score, reason, algorithm) in ranked[: self._max_recommendations]:
            product = next((p for p in products if p.id == pid), None)
            if product:
                scored_products.append(
                    ScoredProduct(
                        product=product,
                        score=round(score, 4),
                        reason=reason,
                        algorithm=algorithm,
                    )
                )

        result = RecommendationResult(
            customer_id=customer_id,
            recommendations=scored_products,
            context=context or {},
        )

        logger.info(
            "Recommendations generated",
            customer_id=customer_id,
            count=len(scored_products),
        )
        return result

    def _build_user_profile(
        self,
        customer_id: str,
        behaviors: list[CustomerBehavior],
        orders: list[Order],
    ) -> _UserProfile:
        """Build a user profile from behavior and order data.

        Args:
            customer_id: The customer ID.
            behaviors: All behavior events.
            orders: All orders.

        Returns:
            UserProfile with aggregated preferences.
        """
        profile = _UserProfile()

        for behavior in behaviors:
            if behavior.customer_id != customer_id:
                continue
            if behavior.event_type == "view":
                profile.viewed_products[behavior.product_id] += 1
            elif behavior.event_type == "add_to_cart":
                profile.cart_products[behavior.product_id] += 1
            elif behavior.event_type == "purchase":
                profile.purchased_products[behavior.product_id] += 1

        for order in orders:
            if order.customer_id != customer_id:
                continue
            for item in order.items:
                pid = item.get("product_id", "")
                if pid:
                    profile.purchased_products[pid] += 1

        return profile

    def _score_content_based(
        self,
        product: Product,
        profile: _UserProfile,
    ) -> tuple[float, str]:
        """Score a product based on content similarity to user profile.

        Args:
            product: The product to score.
            profile: The user's profile.

        Returns:
            Tuple of (score, reason).
        """
        score = 0.0
        reasons: list[str] = []

        # Category affinity
        if product.category and profile.preferred_categories:
            cat_score = profile.preferred_categories.get(product.category, 0)
            max_cat = (
                max(profile.preferred_categories.values())
                if profile.preferred_categories
                else 1
            )
            if max_cat > 0:
                score += (cat_score / max_cat) * 0.4
                if cat_score > 0:
                    reasons.append(f"preferred category: {product.category}")

        # Tag overlap
        if product.tags and profile.preferred_tags:
            tag_overlap = sum(profile.preferred_tags.get(tag, 0) for tag in product.tags)
            max_tag = max(profile.preferred_tags.values()) if profile.preferred_tags else 1
            if max_tag > 0:
                score += (tag_overlap / max_tag) * 0.3
                if tag_overlap > 0:
                    reasons.append("matching tags")

        # Price affinity (prefer products in similar price range)
        if profile.purchased_products:
            # This is simplified; real implementation would use price history
            score += 0.1

        # Don't recommend already purchased items
        if product.id in profile.purchased_products:
            score *= 0.1
            reasons.append("previously purchased")

        reason = ", ".join(reasons) if reasons else "content match"
        return min(score, 1.0), reason

    def _score_collaborative(
        self,
        customer_id: str,
        products: list[Product],
        behaviors: list[CustomerBehavior],
        orders: list[Order],
    ) -> dict[str, tuple[float, str]]:
        """Score products using collaborative filtering.

        Args:
            customer_id: The target customer.
            products: Product catalog.
            behaviors: All behavior events.
            orders: All orders.

        Returns:
            Dict mapping product_id to (score, reason).
        """
        # Build user-item interaction matrix
        user_items: dict[str, set[str]] = defaultdict(set)
        for behavior in behaviors:
            if behavior.event_type in ("view", "add_to_cart", "purchase"):
                user_items[behavior.customer_id].add(behavior.product_id)

        for order in orders:
            for item in order.items:
                pid = item.get("product_id", "")
                if pid:
                    user_items[order.customer_id].add(pid)

        target_items = user_items.get(customer_id, set())
        if not target_items:
            return {}

        # Find similar users (Jaccard similarity)
        user_similarities: list[tuple[str, float]] = []
        for other_id, other_items in user_items.items():
            if other_id == customer_id:
                continue
            intersection = len(target_items & other_items)
            union = len(target_items | other_items)
            if union > 0:
                similarity = intersection / union
                if similarity > 0:
                    user_similarities.append((other_id, similarity))

        # Score products from similar users
        product_scores: dict[str, tuple[float, str]] = {}
        for other_id, similarity in sorted(
            user_similarities, key=lambda x: x[1], reverse=True
        )[:20]:
            for pid in user_items[other_id]:
                if pid not in target_items:
                    if pid in product_scores:
                        existing_score, reason = product_scores[pid]
                        product_scores[pid] = (
                            existing_score + similarity * 0.5,
                            f"similar users also viewed this (score: {similarity:.2f})",
                        )
                    else:
                        product_scores[pid] = (
                            similarity * 0.5,
                            f"similar users also viewed this (score: {similarity:.2f})",
                        )

        return product_scores

    def _apply_diversity(
        self,
        candidate_scores: dict[str, tuple[float, str, str]],
        products: list[Product],
    ) -> list[tuple[str, tuple[float, str, str]]]:
        """Apply diversity re-ranking to candidate products.

        Args:
            candidate_scores: Mapping of product_id to (score, reason, algorithm).
            products: Product catalog for category lookup.

        Returns:
            Re-ranked list of (product_id, score_info) tuples.
        """
        product_map = {p.id: p for p in products}
        ranked: list[tuple[str, tuple[float, str, str]]] = []
        category_counts: Counter[str] = Counter()

        # Sort by score descending
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1][0],
            reverse=True,
        )

        for pid, score_info in sorted_candidates:
            product = product_map.get(pid)
            category = product.category if product else ""

            # Penalize over-represented categories
            diversity_penalty = category_counts.get(category, 0) * self._diversity_factor * 0.1
            adjusted_score = score_info[0] - diversity_penalty

            ranked.append((pid, (adjusted_score, score_info[1], score_info[2])))
            category_counts[category] += 1

        return ranked
