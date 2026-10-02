"""Pricing Engine Agent.

Computes optimal prices using elasticity models, market intelligence,
and business constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field, field_validator

from pricing_optimizer.agents.market_intelligence import MarketIntelligenceReport

logger = structlog.get_logger(__name__)


class OptimizationStrategy(str, Enum):
    """Available pricing optimization strategies."""

    PROFIT_MAXIMIZATION = "profit_maximization"
    REVENUE_MAXIMIZATION = "revenue_maximization"
    MARKET_PENETRATION = "market_penetration"
    COMPETITIVE_PARITY = "competitive_parity"


class ElasticityModel(str, Enum):
    """Available price elasticity models."""

    LOG_LINEAR = "log_linear"
    CONSTANT_ELASTICITY = "constant_elasticity"
    LINEAR = "linear"


class PricingConstraint(BaseModel):
    """Business constraints for pricing decisions."""

    min_price: float = Field(gt=0)
    max_price: float = Field(gt=0)
    min_margin_percent: float = Field(ge=0, le=100)
    max_price_change_percent: float = Field(ge=0, le=100)
    target_margin_percent: float | None = Field(default=None, ge=0, le=100)

    @field_validator("max_price")
    @classmethod
    def max_price_greater_than_min(cls, v: float, info: Any) -> float:
        """Validate max_price > min_price."""
        if "min_price" in info.data and v <= info.data["min_price"]:
            raise ValueError("max_price must be greater than min_price")
        return v


class PriceRecommendation(BaseModel):
    """A pricing recommendation for a single product."""

    product_id: str
    current_price: float
    recommended_price: float
    confidence: float = Field(ge=0.0, le=1.0)
    expected_demand_change_percent: float
    expected_profit_change_percent: float
    strategy: OptimizationStrategy
    reasoning: str
    constraints_applied: list[str] = Field(default_factory=list)
    valid_until: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PricingEngineResult(BaseModel):
    """Result of a pricing optimization run."""

    recommendations: list[PriceRecommendation] = Field(default_factory=list)
    total_products_analyzed: int = 0
    total_expected_profit_change_percent: float = 0.0
    strategy_used: OptimizationStrategy
    generated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class PricingEngineConfig:
    """Configuration for the Pricing Engine Agent."""

    min_margin_percent: float = 10.0
    max_price_change_percent: float = 25.0
    elasticity_model: ElasticityModel = ElasticityModel.LOG_LINEAR
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.PROFIT_MAXIMIZATION
    default_elasticity: float = -1.5
    confidence_threshold: float = 0.7


class PricingEngineAgent:
    """Agent responsible for computing optimal product prices.

    Uses price elasticity models, market intelligence data, and business
    constraints to generate pricing recommendations that maximize
    business objectives.
    """

    def __init__(
        self,
        config: PricingEngineConfig | None = None,
    ) -> None:
        """Initialize the Pricing Engine Agent.

        Args:
            config: Agent configuration. Uses defaults if not provided.
        """
        self.config = config or PricingEngineConfig()
        logger.info(
            "pricing_engine_agent_initialized",
            strategy=self.config.optimization_strategy.value,
            elasticity_model=self.config.elasticity_model.value,
        )

    def _estimate_elasticity(
        self,
        product_id: str,
        market_report: MarketIntelligenceReport | None,
    ) -> float:
        """Estimate price elasticity for a product.

        In production, this would use historical sales data and
        statistical methods. Here we use a simplified approach.

        Args:
            product_id: The product identifier.
            market_report: Optional market intelligence data.

        Returns:
            Estimated price elasticity coefficient (negative value).
        """
        base_elasticity = self.config.default_elasticity

        if market_report and market_report.demand_signals:
            # Adjust elasticity based on demand signal confidence
            avg_confidence = sum(
                s.confidence for s in market_report.demand_signals
            ) / len(market_report.demand_signals)
            # Higher confidence signals suggest more elastic demand
            base_elasticity *= 0.8 + 0.4 * avg_confidence

        logger.debug(
            "elasticity_estimated",
            product_id=product_id,
            elasticity=base_elasticity,
        )
        return base_elasticity

    def _compute_optimal_price(
        self,
        current_price: float,
        cost: float,
        elasticity: float,
        constraints: PricingConstraint,
    ) -> float:
        """Compute the optimal price using the elasticity model.

        Args:
            current_price: Current product price.
            cost: Product cost.
            elasticity: Price elasticity coefficient.
            constraints: Business constraints.

        Returns:
            Optimal price within constraints.
        """
        if elasticity >= -1.0:
            # Inelastic demand: price increase raises revenue
            optimal = current_price * 1.1
        else:
            # Elastic demand: use profit-maximizing formula
            # For constant elasticity: P* = (e / (1+e)) * MC
            # where MC is marginal cost
            if self.config.elasticity_model == ElasticityModel.CONSTANT_ELASTICITY:
                optimal = (elasticity / (1 + elasticity)) * cost
            elif self.config.elasticity_model == ElasticityModel.LINEAR:
                # Simplified linear model
                optimal = current_price * (1 + 0.5 / abs(elasticity))
            else:
                # Log-linear model (default)
                optimal = current_price * (1 + 0.3 / abs(elasticity))

        # Apply constraints
        min_allowed = max(
            constraints.min_price,
            cost * (1 + constraints.min_margin_percent / 100),
        )
        max_allowed = constraints.max_price

        optimal = max(min_allowed, min(optimal, max_allowed))

        # Limit price change
        max_change = constraints.max_price_change_percent / 100
        lower_bound = current_price * (1 - max_change)
        upper_bound = current_price * (1 + max_change)
        optimal = max(lower_bound, min(optimal, upper_bound))

        return round(optimal, 2)

    def _calculate_expected_changes(
        self,
        current_price: float,
        new_price: float,
        elasticity: float,
    ) -> tuple[float, float]:
        """Calculate expected demand and profit changes.

        Args:
            current_price: Current price.
            new_price: Proposed new price.
            elasticity: Price elasticity coefficient.

        Returns:
            Tuple of (demand_change_percent, profit_change_percent).
        """
        price_change_ratio = (new_price - current_price) / current_price
        demand_change = elasticity * price_change_ratio * 100

        # Simplified profit change estimation
        # Profit = (P - C) * Q
        # % change ≈ %ΔP * (1 + elasticity) for small changes
        profit_change = price_change_ratio * (1 + elasticity) * 100

        return round(demand_change, 2), round(profit_change, 2)

    def _compute_confidence(
        self,
        market_report: MarketIntelligenceReport | None,
        constraints: PricingConstraint,
    ) -> float:
        """Compute confidence score for a recommendation.

        Args:
            market_report: Market intelligence data if available.
            constraints: Applied constraints.

        Returns:
            Confidence score between 0 and 1.
        """
        confidence = 0.5  # Base confidence

        if market_report:
            confidence += 0.2
            if market_report.competitor_prices:
                confidence += 0.1
            if market_report.demand_signals:
                confidence += 0.1

        # Reduce confidence if many constraints were binding
        constraint_penalty = len(constraints.__fields_set__) * 0.02
        confidence -= constraint_penalty

        return max(0.0, min(1.0, confidence))

    def generate_recommendation(
        self,
        product_id: str,
        current_price: float,
        cost: float,
        constraints: PricingConstraint,
        market_report: MarketIntelligenceReport | None = None,
    ) -> PriceRecommendation:
        """Generate a pricing recommendation for a single product.

        Args:
            product_id: The product identifier.
            current_price: Current product price.
            cost: Product cost.
            constraints: Business constraints.
            market_report: Optional market intelligence data.

        Returns:
            A price recommendation.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not product_id:
            raise ValueError("product_id is required")
        if current_price <= 0:
            raise ValueError("current_price must be positive")
        if cost < 0:
            raise ValueError("cost must be non-negative")
        if cost >= current_price:
            logger.warning(
                "cost_exceeds_or_equals_price",
                product_id=product_id,
                cost=cost,
                current_price=current_price,
            )

        logger.info(
            "generating_price_recommendation",
            product_id=product_id,
            current_price=current_price,
            cost=cost,
        )

        elasticity = self._estimate_elasticity(product_id, market_report)
        optimal_price = self._compute_optimal_price(
            current_price, cost, elasticity, constraints
        )
        demand_change, profit_change = self._calculate_expected_changes(
            current_price, optimal_price, elasticity
        )
        confidence = self._compute_confidence(market_report, constraints)

        constraints_applied: list[str] = []
        if optimal_price <= constraints.min_price * 1.01:
            constraints_applied.append("min_price_bound")
        if optimal_price >= constraints.max_price * 0.99:
            constraints_applied.append("max_price_bound")
        if abs(optimal_price - current_price) / current_price >= (
            constraints.max_price_change_percent / 100 * 0.99
        ):
            constraints_applied.append("max_change_limit")

        reasoning_parts = [
            f"Elasticity estimate: {elasticity:.2f}",
            f"Strategy: {self.config.optimization_strategy.value}",
        ]
        if market_report and market_report.price_position:
            reasoning_parts.append(f"Market position: {market_report.price_position}")

        recommendation = PriceRecommendation(
            product_id=product_id,
            current_price=current_price,
            recommended_price=optimal_price,
            confidence=confidence,
            expected_demand_change_percent=demand_change,
            expected_profit_change_percent=profit_change,
            strategy=self.config.optimization_strategy,
            reasoning=". ".join(reasoning_parts),
            constraints_applied=constraints_applied,
        )

        logger.info(
            "price_recommendation_generated",
            product_id=product_id,
            current_price=current_price,
            recommended_price=optimal_price,
            confidence=confidence,
        )

        return recommendation

    def optimize_prices(
        self,
        products: list[dict[str, Any]],
        constraints: PricingConstraint,
        market_reports: dict[str, MarketIntelligenceReport] | None = None,
    ) -> PricingEngineResult:
        """Optimize prices for multiple products.

        Args:
            products: List of product dicts with 'product_id', 'current_price', 'cost'.
            constraints: Business constraints to apply.
            market_reports: Optional market reports keyed by product_id.

        Returns:
            Complete pricing optimization result.

        Raises:
            ValueError: If products list is empty or constraints are invalid.
        """
        if not products:
            raise ValueError("products list cannot be empty")

        logger.info(
            "starting_price_optimization",
            product_count=len(products),
            strategy=self.config.optimization_strategy.value,
        )

        recommendations: list[PriceRecommendation] = []
        total_profit_change = 0.0

        for product in products:
            product_id = product["product_id"]
            current_price = float(product["current_price"])
            cost = float(product["cost"])

            market_report = None
            if market_reports and product_id in market_reports:
                market_report = market_reports[product_id]

            try:
                rec = self.generate_recommendation(
                    product_id=product_id,
                    current_price=current_price,
                    cost=cost,
                    constraints=constraints,
                    market_report=market_report,
                )
                recommendations.append(rec)
                total_profit_change += rec.expected_profit_change_percent
            except ValueError as exc:
                logger.error(
                    "product_optimization_failed",
                    product_id=product_id,
                    error=str(exc),
                )

        avg_profit_change = (
            total_profit_change / len(recommendations) if recommendations else 0.0
        )

        result = PricingEngineResult(
            recommendations=recommendations,
            total_products_analyzed=len(products),
            total_expected_profit_change_percent=round(avg_profit_change, 2),
            strategy_used=self.config.optimization_strategy,
        )

        logger.info(
            "price_optimization_complete",
            products_analyzed=len(products),
            recommendations_generated=len(recommendations),
            avg_profit_change=avg_profit_change,
        )

        return result
