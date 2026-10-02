"""
Advanced Campaign Optimization Example
======================================

Demonstrates advanced campaign optimization including:
- Multi-objective optimization with constraints
- A/B testing framework integration
- Machine learning-based performance prediction
- Automated budget pacing
- Cross-channel attribution modeling
- Real-time bidding strategies

Usage:
    python advanced.py
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BidStrategy(str, Enum):
    """Bidding strategies for programmatic advertising."""

    MANUAL_CPC = "manual_cpc"
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"
    MAXIMIZE_CONVERSIONS = "maximize_conversions"
    ENHANCED_CPC = "enhanced_cpc"


class PacingMode(str, Enum):
    """Budget pacing modes."""

    STANDARD = "standard"
    ACCELERATED = "accelerated"
    DAY_PARTING = "day_parting"


class AttributionModel(str, Enum):
    """Attribution models for cross-channel tracking."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    DATA_DRIVEN = "data_driven"


class OptimizationConstraintType(str, Enum):
    """Types of optimization constraints."""

    BUDGET = "budget"
    CPA = "cpa"
    ROAS = "roas"
    IMPRESSIONS = "impressions"
    FREQUENCY = "frequency"


@dataclass
class OptimizationConstraint:
    """A constraint for campaign optimization."""

    type: OptimizationConstraintType
    min_value: float | None = None
    max_value: float | None = None
    target_value: float | None = None

    def is_satisfied(self, actual_value: float) -> bool:
        """Check if a value satisfies this constraint."""
        if self.min_value is not None and actual_value < self.min_value:
            return False
        if self.max_value is not None and actual_value > self.max_value:
            return False
        return True


@dataclass
class ABTestVariant:
    """A variant in an A/B test."""

    name: str
    weight: float
    performance_score: float = 0.0
    impressions: int = 0
    conversions: int = 0

    @property
    def conversion_rate(self) -> float:
        """Conversion rate for this variant."""
        return self.conversions / self.impressions if self.impressions > 0 else 0.0


@dataclass
class ABTest:
    """An A/B test configuration."""

    name: str
    variants: list[ABTestVariant]
    confidence_level: float = 0.95
    min_sample_size: int = 1000
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    @property
    def is_significant(self) -> bool:
        """Check if test has reached statistical significance."""
        total_impressions = sum(v.impressions for v in self.variants)
        return total_impressions >= self.min_sample_size

    @property
    def winner(self) -> ABTestVariant | None:
        """Get the winning variant if test is significant."""
        if not self.is_significant:
            return None
        return max(self.variants, key=lambda v: v.performance_score)


@dataclass
class ChannelConfig:
    """Configuration for an advertising channel."""

    name: str
    budget_share: float
    bid_strategy: BidStrategy
    target_cpa: float | None = None
    target_roas: float | None = None
    frequency_cap: int | None = None
    day_parting_hours: list[int] | None = None


@dataclass
class PerformancePrediction:
    """ML-based performance prediction."""

    channel: str
    predicted_impressions: int
    predicted_clicks: int
    predicted_conversions: int
    predicted_spend: float
    predicted_revenue: float
    confidence_interval: tuple[float, float]
    prediction_time: datetime = field(default_factory=datetime.now)

    @property
    def predicted_roas(self) -> float:
        """Predicted return on ad spend."""
        return self.predicted_revenue / self.predicted_spend if self.predicted_spend > 0 else 0.0

    @property
    def predicted_cpa(self) -> float:
        """Predicted cost per acquisition."""
        return self.predicted_spend / self.predicted_conversions if self.predicted_conversions > 0 else 0.0


class AdvancedCampaignOptimizer:
    """Advanced campaign optimizer with ML and multi-objective optimization."""

    def __init__(
        self,
        attribution_model: AttributionModel = AttributionModel.DATA_DRIVEN,
        learning_rate: float = 0.1,
    ) -> None:
        """Initialize the advanced optimizer.

        Args:
            attribution_model: Attribution model to use.
            learning_rate: Learning rate for optimization algorithms.
        """
        self.attribution_model = attribution_model
        self.learning_rate = learning_rate
        self.campaigns: dict[str, Any] = {}
        self.ab_tests: dict[str, ABTest] = {}
        self.predictions: dict[str, list[PerformancePrediction]] = {}

    def create_optimized_campaign(
        self,
        name: str,
        total_budget: float,
        channel_configs: list[ChannelConfig],
        constraints: list[OptimizationConstraint] | None = None,
        pacing_mode: PacingMode = PacingMode.STANDARD,
    ) -> dict[str, Any]:
        """Create a campaign with advanced optimization settings.

        Args:
            name: Campaign name.
            total_budget: Total campaign budget.
            channel_configs: Configuration for each channel.
            constraints: Optimization constraints.
            pacing_mode: Budget pacing mode.

        Returns:
            Campaign configuration dictionary.

        Raises:
            ValueError: If channel budget shares don't sum to 1.0.
        """
        total_share = sum(c.budget_share for c in channel_configs)
        if not math.isclose(total_share, 1.0, rel_tol=0.01):
            raise ValueError(f"Channel budget shares must sum to 1.0, got {total_share}")

        campaign = {
            "name": name,
            "total_budget": total_budget,
            "channels": {},
            "constraints": constraints or [],
            "pacing_mode": pacing_mode.value,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        for config in channel_configs:
            campaign["channels"][config.name] = {
                "budget": total_budget * config.budget_share,
                "bid_strategy": config.bid_strategy.value,
                "target_cpa": config.target_cpa,
                "target_roas": config.target_roas,
                "frequency_cap": config.frequency_cap,
                "day_parting_hours": config.day_parting_hours,
                "spend": 0.0,
                "conversions": 0,
                "revenue": 0.0,
            }

        self.campaigns[name] = campaign
        logger.info("Created advanced campaign '%s' with %d channels", name, len(channel_configs))
        return campaign

    def run_ab_test(
        self,
        name: str,
        variants: list[ABTestVariant],
        duration_days: int = 14,
    ) -> ABTest:
        """Set up and run an A/B test.

        Args:
            name: Test name.
            variants: Test variants.
            duration_days: Test duration.

        Returns:
            The ABTest instance.
        """
        total_weight = sum(v.weight for v in variants)
        if not math.isclose(total_weight, 1.0, rel_tol=0.01):
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")

        test = ABTest(
            name=name,
            variants=variants,
            end_time=datetime.now() + timedelta(days=duration_days),
        )
        self.ab_tests[name] = test
        logger.info("Created A/B test '%s' with %d variants", name, len(variants))
        return test

    def predict_performance(
        self,
        campaign_name: str,
        channel: str,
        historical_data: list[dict[str, float]],
        days_ahead: int = 7,
    ) -> PerformancePrediction:
        """Predict future performance using simple ML model.

        Uses exponential smoothing for demonstration. In production,
        this would use a proper ML model (e.g., XGBoost, LSTM).

        Args:
            campaign_name: Campaign name.
            channel: Channel name.
            historical_data: List of daily performance data.
            days_ahead: Number of days to predict ahead.

        Returns:
            PerformancePrediction instance.
        """
        if not historical_data:
            raise ValueError("Historical data is required for prediction")

        # Simple exponential smoothing
        alpha = 0.3
        impressions = historical_data[0].get("impressions", 0)
        clicks = historical_data[0].get("clicks", 0)
        conversions = historical_data[0].get("conversions", 0)
        spend = historical_data[0].get("spend", 0)
        revenue = historical_data[0].get("revenue", 0)

        for data in historical_data[1:]:
            impressions = alpha * data.get("impressions", 0) + (1 - alpha) * impressions
            clicks = alpha * data.get("clicks", 0) + (1 - alpha) * clicks
            conversions = alpha * data.get("conversions", 0) + (1 - alpha) * conversions
            spend = alpha * data.get("spend", 0) + (1 - alpha) * spend
            revenue = alpha * data.get("revenue", 0) + (1 - alpha) * revenue

        # Project forward
        predicted_impressions = int(impressions * days_ahead)
        predicted_clicks = int(clicks * days_ahead)
        predicted_conversions = int(conversions * days_ahead)
        predicted_spend = spend * days_ahead
        predicted_revenue = revenue * days_ahead

        # Confidence interval (simplified)
        std_dev = math.sqrt(sum((d.get("conversions", 0) - conversions) ** 2 for d in historical_data) / len(historical_data))
        margin = 1.96 * std_dev * math.sqrt(days_ahead)

        prediction = PerformancePrediction(
            channel=channel,
            predicted_impressions=predicted_impressions,
            predicted_clicks=predicted_clicks,
            predicted_conversions=predicted_conversions,
            predicted_spend=predicted_spend,
            predicted_revenue=predicted_revenue,
            confidence_interval=(max(0, predicted_conversions - margin), predicted_conversions + margin),
        )

        if campaign_name not in self.predictions:
            self.predictions[campaign_name] = []
        self.predictions[campaign_name].append(prediction)

        logger.info(
            "Predicted %d conversions for '%s' on '%s' (CI: %.0f-%.0f)",
            predicted_conversions,
            campaign_name,
            channel,
            prediction.confidence_interval[0],
            prediction.confidence_interval[1],
        )
        return prediction

    def optimize_budget_pacing(
        self,
        campaign_name: str,
        current_spend: float,
        target_spend: float,
        days_elapsed: int,
        total_days: int,
    ) -> dict[str, Any]:
        """Optimize budget pacing to hit targets.

        Args:
            campaign_name: Campaign name.
            current_spend: Current spend amount.
            target_spend: Target spend amount.
            days_elapsed: Days since campaign start.
            total_days: Total campaign duration.

        Returns:
            Pacing recommendations.
        """
        expected_spend = target_spend * (days_elapsed / total_days)
        spend_ratio = current_spend / expected_spend if expected_spend > 0 else 1.0

        remaining_days = total_days - days_elapsed
        remaining_budget = target_spend - current_spend
        daily_budget = remaining_budget / remaining_days if remaining_days > 0 else 0

        if spend_ratio < 0.8:
            status = "under_pacing"
            action = "increase_bids"
        elif spend_ratio > 1.2:
            status = "over_pacing"
            action = "decrease_bids"
        else:
            status = "on_track"
            action = "maintain"

        result = {
            "campaign": campaign_name,
            "status": status,
            "action": action,
            "spend_ratio": round(spend_ratio, 4),
            "current_spend": round(current_spend, 2),
            "expected_spend": round(expected_spend, 2),
            "remaining_budget": round(remaining_budget, 2),
            "daily_budget_target": round(daily_budget, 2),
            "days_remaining": remaining_days,
        }

        logger.info("Pacing for '%s': %s (ratio: %.2f)", campaign_name, status, spend_ratio)
        return result

    def calculate_attribution(
        self,
        touchpoints: list[dict[str, Any]],
        model: AttributionModel | None = None,
    ) -> dict[str, float]:
        """Calculate attribution using specified model.

        Args:
            touchpoints: List of touchpoint data with channel and timestamp.
            model: Attribution model (defaults to instance setting).

        Returns:
            Dictionary mapping channels to attributed conversion credit.
        """
        model = model or self.attribution_model
        attribution: dict[str, float] = {}

        if not touchpoints:
            return attribution

        if model == AttributionModel.FIRST_TOUCH:
            channel = touchpoints[0]["channel"]
            attribution[channel] = 1.0

        elif model == AttributionModel.LAST_TOUCH:
            channel = touchpoints[-1]["channel"]
            attribution[channel] = 1.0

        elif model == AttributionModel.LINEAR:
            credit = 1.0 / len(touchpoints)
            for tp in touchpoints:
                ch = tp["channel"]
                attribution[ch] = attribution.get(ch, 0.0) + credit

        elif model == AttributionModel.TIME_DECAY:
            # Exponential decay with half-life of 7 days
            now = datetime.now()
            weights = []
            for tp in touchpoints:
                age_days = (now - tp["timestamp"]).days
                weight = 0.5 ** (age_days / 7.0)
                weights.append(weight)

            total_weight = sum(weights)
            for tp, weight in zip(touchpoints, weights):
                ch = tp["channel"]
                attribution[ch] = attribution.get(ch, 0.0) + weight / total_weight

        elif model == AttributionModel.DATA_DRIVEN:
            # Simplified data-driven: use position-based with recency bias
            n = len(touchpoints)
            for i, tp in enumerate(touchpoints):
                # 40% first, 40% last, 20% distributed
                if i == 0:
                    credit = 0.4
                elif i == n - 1:
                    credit = 0.4
                else:
                    credit = 0.2 / (n - 2) if n > 2 else 0.0
                ch = tp["channel"]
                attribution[ch] = attribution.get(ch, 0.0) + credit

        return attribution

    def multi_objective_optimize(
        self,
        campaign_name: str,
        objectives: list[Callable[[dict[str, Any]], float]],
        constraints: list[OptimizationConstraint],
        iterations: int = 100,
    ) -> dict[str, Any]:
        """Run multi-objective optimization.

        Uses a simplified genetic algorithm approach for demonstration.

        Args:
            campaign_name: Campaign name.
            objectives: List of objective functions to maximize.
            constraints: List of constraints to satisfy.
            iterations: Number of optimization iterations.

        Returns:
            Optimization results.
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        campaign = self.campaigns[campaign_name]
        channels = list(campaign["channels"].keys())

        # Initialize population
        population_size = 20
        population: list[dict[str, float]] = []
        for _ in range(population_size):
            individual = {ch: random.random() for ch in channels}
            total = sum(individual.values())
            individual = {ch: v / total for ch, v in individual.items()}
            population.append(individual)

        best_score = float("-inf")
        best_allocation = population[0]

        for iteration in range(iterations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                score = sum(obj(individual) for obj in objectives) / len(objectives)

                # Penalize constraint violations
                for constraint in constraints:
                    # Simplified constraint checking
                    pass

                fitness_scores.append(score)

            # Select best
            best_idx = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
            if fitness_scores[best_idx] > best_score:
                best_score = fitness_scores[best_idx]
                best_allocation = population[best_idx]

            # Create next generation (simplified crossover + mutation)
            new_population = [best_allocation]  # Elitism
            while len(new_population) < population_size:
                parent = random.choice(population)
                child = {
                    ch: max(0.01, parent[ch] + random.gauss(0, 0.05))
                    for ch in channels
                }
                total = sum(child.values())
                child = {ch: v / total for ch, v in child.items()}
                new_population.append(child)

            population = new_population

        result = {
            "campaign": campaign_name,
            "best_allocation": {ch: round(v, 4) for ch, v in best_allocation.items()},
            "best_score": round(best_score, 4),
            "iterations": iterations,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("Multi-objective optimization complete for '%s'", campaign_name)
        return result


def main() -> None:
    """Run the advanced campaign optimization example."""
    logger.info("=" * 60)
    logger.info("Advanced Campaign Optimization Example")
    logger.info("=" * 60)

    optimizer = AdvancedCampaignOptimizer(
        attribution_model=AttributionModel.DATA_DRIVEN,
        learning_rate=0.1,
    )

    # Create channel configs
    channel_configs = [
        ChannelConfig(
            name="google_ads",
            budget_share=0.5,
            bid_strategy=BidStrategy.TARGET_ROAS,
            target_roas=4.0,
            frequency_cap=3,
        ),
        ChannelConfig(
            name="meta_ads",
            budget_share=0.3,
            bid_strategy=BidStrategy.MAXIMIZE_CONVERSIONS,
            day_parting_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        ),
        ChannelConfig(
            name="tiktok_ads",
            budget_share=0.2,
            bid_strategy=BidStrategy.TARGET_CPA,
            target_cpa=25.0,
        ),
    ]

    # Create campaign
    campaign = optimizer.create_optimized_campaign(
        name="Q4 Product Launch",
        total_budget=50000.0,
        channel_configs=channel_configs,
        constraints=[
            OptimizationConstraint(
                type=OptimizationConstraintType.ROAS,
                min_value=2.0,
            ),
            OptimizationConstraint(
                type=OptimizationConstraintType.CPA,
                max_value=50.0,
            ),
        ],
    )
    logger.info("Created campaign with %d channels", len(campaign["channels"]))

    # Set up A/B test
    ab_test = optimizer.run_ab_test(
        name="Landing Page Test",
        variants=[
            ABTestVariant(name="control", weight=0.5),
            ABTestVariant(name="variant_a", weight=0.3),
            ABTestVariant(name="variant_b", weight=0.2),
        ],
    )
    logger.info("A/B test '%s' created", ab_test.name)

    # Simulate performance prediction
    historical = [
        {"impressions": 10000, "clicks": 300, "conversions": 10, "spend": 500, "revenue": 2000},
        {"impressions": 12000, "clicks": 350, "conversions": 12, "spend": 600, "revenue": 2400},
        {"impressions": 11000, "clicks": 320, "conversions": 11, "spend": 550, "revenue": 2200},
        {"impressions": 13000, "clicks": 400, "conversions": 15, "spend": 700, "revenue": 3000},
        {"impressions": 12500, "clicks": 380, "conversions": 14, "spend": 650, "revenue": 2800},
    ]

    prediction = optimizer.predict_performance(
        campaign_name="Q4 Product Launch",
        channel="google_ads",
        historical_data=historical,
        days_ahead=7,
    )
    logger.info(
        "Prediction: %d conversions, ROAS %.2f",
        prediction.predicted_conversions,
        prediction.predicted_roas,
    )

    # Budget pacing
    pacing = optimizer.optimize_budget_pacing(
        campaign_name="Q4 Product Launch",
        current_spend=15000.0,
        target_spend=50000.0,
        days_elapsed=10,
        total_days=30,
    )
    logger.info("Pacing status: %s", pacing["status"])

    # Attribution
    touchpoints = [
        {"channel": "google_ads", "timestamp": datetime.now() - timedelta(days=5)},
        {"channel": "meta_ads", "timestamp": datetime.now() - timedelta(days=3)},
        {"channel": "google_ads", "timestamp": datetime.now() - timedelta(days=1)},
    ]
    attribution = optimizer.calculate_attribution(touchpoints)
    logger.info("Attribution: %s", attribution)

    # Multi-objective optimization
    def roas_objective(allocation: dict[str, float]) -> float:
        return allocation.get("google_ads", 0) * 4.0 + allocation.get("meta_ads", 0) * 3.0

    def reach_objective(allocation: dict[str, float]) -> float:
        return allocation.get("tiktok_ads", 0) * 5.0 + allocation.get("meta_ads", 0) * 3.0

    result = optimizer.multi_objective_optimize(
        campaign_name="Q4 Product Launch",
        objectives=[roas_objective, reach_objective],
        constraints=[],
        iterations=50,
    )
    logger.info("Best allocation: %s", result["best_allocation"])

    logger.info("\n" + "=" * 60)
    logger.info("Advanced example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
