"""Pricing Optimizer Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from content_marketplace.models.pricing import (
    Pricing,
    PricingCreate,
    PricingStrategy,
    PricingUpdate,
)

logger = logging.getLogger(__name__)


class PricingOptimizerAgent:
    """Agent responsible for optimizing content pricing.

    Uses LangChain DeepAgents to analyze market conditions,
    competitor pricing, and demand signals to recommend optimal prices.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the PricingOptimizerAgent.

        Args:
            llm: Optional LangChain chat model for AI-powered pricing.
        """
        self.llm = llm
        self._pricing: dict[UUID, Pricing] = {}

    def _compute_final_price(self, pricing: Pricing) -> float:
        """Compute the final price based on strategy and multipliers.

        Args:
            pricing: The pricing entry.

        Returns:
            The computed final price.
        """
        base = pricing.base_price

        if pricing.strategy == PricingStrategy.FIXED:
            return base
        elif pricing.strategy == PricingStrategy.DYNAMIC:
            price = base * pricing.demand_multiplier
            if pricing.competitor_price:
                # Adjust towards competitor price with 20% weight
                price = 0.8 * price + 0.2 * pricing.competitor_price
            return round(price, 2)
        elif pricing.strategy == PricingStrategy.AUCTION:
            # Start at min_price or 70% of base
            start = pricing.min_price or (base * 0.7)
            return round(start, 2)
        elif pricing.strategy == PricingStrategy.SUBSCRIPTION:
            # Monthly subscription pricing
            return round(base * 0.8, 2)  # 20% discount for subscription
        elif pricing.strategy == PricingStrategy.USAGE_BASED:
            return round(base, 2)
        else:
            return base

    async def create_pricing(self, data: PricingCreate) -> Pricing:
        """Create a new pricing entry.

        Args:
            data: Pricing creation data.

        Returns:
            The newly created pricing entry.
        """
        pricing = Pricing(
            listing_id=data.listing_id,
            strategy=data.strategy,
            base_price=data.base_price,
            currency=data.currency,
            min_price=data.min_price,
            max_price=data.max_price,
            demand_multiplier=data.demand_multiplier,
            competitor_price=data.competitor_price,
            final_price=data.base_price,
            metadata=data.metadata,
        )
        pricing.final_price = self._compute_final_price(pricing)
        self._pricing[pricing.id] = pricing
        logger.info("Created pricing %s for listing %s", pricing.id, data.listing_id)
        return pricing

    async def update_pricing(self, pricing_id: UUID, data: PricingUpdate) -> Pricing:
        """Update an existing pricing entry.

        Args:
            pricing_id: The pricing UUID to update.
            data: Update data.

        Returns:
            The updated pricing entry.

        Raises:
            KeyError: If pricing entry not found.
        """
        if pricing_id not in self._pricing:
            raise KeyError(f"Pricing {pricing_id} not found")

        pricing = self._pricing[pricing_id]
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                setattr(pricing, field, value)

        pricing.final_price = self._compute_final_price(pricing)

        from datetime import UTC, datetime
        pricing.updated_at = datetime.now(tz=UTC)
        logger.info("Updated pricing %s", pricing_id)
        return pricing

    async def get_pricing(self, pricing_id: UUID) -> Pricing:
        """Retrieve a pricing entry by ID.

        Args:
            pricing_id: The pricing UUID.

        Returns:
            The pricing entry.

        Raises:
            KeyError: If pricing entry not found.
        """
        if pricing_id not in self._pricing:
            raise KeyError(f"Pricing {pricing_id} not found")
        return self._pricing[pricing_id]

    async def optimize_price(self, pricing_id: UUID) -> Pricing:
        """Use AI to optimize the price for a listing.

        Args:
            pricing_id: The pricing UUID to optimize.

        Returns:
            The optimized pricing entry.
        """
        pricing = await self.get_pricing(pricing_id)

        if self.llm is None:
            # Fallback: simple demand-based adjustment
            pricing.demand_multiplier = min(pricing.demand_multiplier * 1.05, 2.0)
            pricing.final_price = self._compute_final_price(pricing)
            return pricing

        prompt = (
            f"Analyze and optimize this pricing strategy:\n"
            f"Current price: {pricing.base_price} {pricing.currency}\n"
            f"Strategy: {pricing.strategy}\n"
            f"Demand multiplier: {pricing.demand_multiplier}\n"
            f"Competitor price: {pricing.competitor_price}\n"
            f"Recommend a new base_price and demand_multiplier.\n"
            f"Respond with JSON: {{\"base_price\": ..., \"demand_multiplier\": ...}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            if "base_price" in result:
                pricing.base_price = float(result["base_price"])
            if "demand_multiplier" in result:
                pricing.demand_multiplier = float(result["demand_multiplier"])
            pricing.final_price = self._compute_final_price(pricing)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("AI pricing optimization failed, using fallback")
            pricing.demand_multiplier = min(pricing.demand_multiplier * 1.05, 2.0)
            pricing.final_price = self._compute_final_price(pricing)

        from datetime import UTC, datetime
        pricing.updated_at = datetime.now(tz=UTC)
        return pricing

    async def get_pricing_for_listing(self, listing_id: UUID) -> Pricing | None:
        """Get the pricing entry for a specific listing.

        Args:
            listing_id: The listing UUID.

        Returns:
            The pricing entry or None if not found.
        """
        for pricing in self._pricing.values():
            if pricing.listing_id == listing_id:
                return pricing
        return None

    async def bulk_optimize(self, category: str | None = None) -> list[Pricing]:
        """Optimize prices for multiple listings.

        Args:
            category: Optional category filter.

        Returns:
            List of optimized pricing entries.
        """
        results = []
        for pricing in self._pricing.values():
            optimized = await self.optimize_price(pricing.id)
            results.append(optimized)
        return results
