"""Creative Optimizer Agent — A/B testing and optimization for ad creatives."""
from __future__ import annotations

import random
from datetime import datetime
from typing import Any

import structlog

from campaign_agents.models.optimization import (
    ABTestConfig,
    ABTestResult,
    CreativeOptimizationResult,
    CreativeVariant,
)

logger = structlog.get_logger(__name__)


class CreativeOptimizer:
    """A/B testing optimizer for ad creatives.

    Manages creative variants, runs statistical tests, identifies winners,
    and provides optimization recommendations for creative performance.
    """

    def __init__(self, config: ABTestConfig) -> None:
        """Initialize the creative optimizer.

        Args:
            config: A/B test configuration.

        Raises:
            ValueError: If config is invalid.
        """
        self._validate_config(config)
        self.config = config
        self._variants: dict[str, CreativeVariant] = {
            v.variant_id: v for v in config.variants
        }
        self._test_history: list[ABTestResult] = []
        self._start_time = datetime.now()

        logger.info(
            "Creative optimizer initialized",
            test_id=config.test_id,
            num_variants=len(config.variants),
        )

    def _validate_config(self, config: ABTestConfig) -> None:
        """Validate A/B test configuration.

        Args:
            config: Configuration to validate.

        Raises:
            ValueError: If configuration is invalid.
        """
        if len(config.variants) < 2:
            raise ValueError("At least 2 variants required for A/B testing")
        variant_ids = [v.variant_id for v in config.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("Variant IDs must be unique")
        if not (0 < config.confidence_level < 1):
            raise ValueError("Confidence level must be between 0 and 1")
        if config.min_sample_size < 100:
            raise ValueError("Minimum sample size must be at least 100")

    def get_variant_performance(self, variant_id: str) -> dict[str, float]:
        """Get performance metrics for a variant.

        Args:
            variant_id: The variant identifier.

        Returns:
            Dictionary of performance metrics.

        Raises:
            ValueError: If variant not found.
        """
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")

        v = self._variants[variant_id]
        ctr = v.clicks / v.impressions if v.impressions > 0 else 0.0
        conversion_rate = v.conversions / v.clicks if v.clicks > 0 else 0.0
        cpa = v.spend / v.conversions if v.conversions > 0 else 0.0
        roas = (v.conversions * 50) / v.spend if v.spend > 0 else 0.0  # Assume $50 avg order

        return {
            "impressions": float(v.impressions),
            "clicks": float(v.clicks),
            "conversions": float(v.conversions),
            "spend": v.spend,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
            "cpa": cpa,
            "roas": roas,
        }

    def allocate_traffic(self) -> dict[str, float]:
        """Allocate traffic across variants using Thompson Sampling.

        Returns:
            Dictionary mapping variant IDs to traffic allocation percentages.
        """
        allocations = {}
        total_weight = sum(v.weight for v in self._variants.values())

        for variant_id, variant in self._variants.items():
            # Thompson sampling-inspired allocation
            successes = variant.conversions + 1
            failures = max(1, variant.clicks - variant.conversions)
            sample = random.betavariate(successes, failures)
            allocations[variant_id] = (sample * variant.weight) / total_weight

        # Normalize to sum to 1
        total = sum(allocations.values())
        if total > 0:
            allocations = {k: v / total for k, v in allocations.items()}

        return allocations

    def update_variant_metrics(
        self,
        variant_id: str,
        impressions: int = 0,
        clicks: int = 0,
        conversions: int = 0,
        spend: float = 0.0,
    ) -> None:
        """Update metrics for a variant.

        Args:
            variant_id: The variant identifier.
            impressions: Number of new impressions.
            clicks: Number of new clicks.
            conversions: Number of new conversions.
            spend: Amount of new spend.

        Raises:
            ValueError: If variant not found.
        """
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")

        v = self._variants[variant_id]
        v.impressions += impressions
        v.clicks += clicks
        v.conversions += conversions
        v.spend += spend

    def run_significance_test(self) -> ABTestResult:
        """Run statistical significance test across variants.

        Returns:
            ABTestResult with test outcome.
        """
        variant_results = []
        for variant_id in self._variants:
            metrics = self.get_variant_performance(variant_id)
            variant_results.append({"variant_id": variant_id, **metrics})

        # Calculate primary metric for each variant
        primary_metric = self.config.primary_metric
        metric_values = [vr.get(primary_metric, 0.0) for vr in variant_results]

        # Find best variant
        best_idx = metric_values.index(max(metric_values))
        winner_id = variant_results[best_idx]["variant_id"]

        # Chi-squared test for significance
        is_significant, p_value = self._chi_squared_test(variant_results, primary_metric)

        # Check minimum sample size
        total_impressions = sum(v.impressions for v in self._variants.values())
        has_enough_data = total_impressions >= self.config.min_sample_size

        # Check test duration
        test_duration = (datetime.now() - self._start_time).days

        # Determine winner
        final_winner = winner_id if (is_significant and has_enough_data) else None

        if final_winner and self.config.auto_winner_selection:
            recommendation = f"Variant {final_winner} is the winner. Allocate 100% traffic."
        elif not has_enough_data:
            recommendation = (
                f"Need more data. Current: {total_impressions}, "
                f"Required: {self.config.min_sample_size}"
            )
        elif not is_significant:
            recommendation = "No significant difference detected. Continue testing."
        else:
            recommendation = "Test duration reached. Review results manually."

        result = ABTestResult(
            test_id=self.config.test_id,
            campaign_id=self.config.campaign_id,
            winner_variant_id=final_winner,
            is_significant=is_significant and has_enough_data,
            p_value=p_value,
            confidence_level=self.config.confidence_level,
            variant_results=variant_results,
            recommendation=recommendation,
            test_duration_days=test_duration,
            total_impressions=total_impressions,
            total_conversions=sum(v.conversions for v in self._variants.values()),
        )

        self._test_history.append(result)
        logger.info(
            "A/B test completed",
            test_id=self.config.test_id,
            winner=final_winner,
            significant=result.is_significant,
        )
        return result

    def _chi_squared_test(
        self, variant_results: list[dict[str, Any]], metric: str
    ) -> tuple[bool, float | None]:
        """Run chi-squared test for statistical significance.

        Args:
            variant_results: List of variant performance dictionaries.
            metric: Primary metric to test.

        Returns:
            Tuple of (is_significant, p_value).
        """
        # Simplified chi-squared test using conversion counts
        conversions = [vr.get("conversions", 0) for vr in variant_results]
        clicks = [vr.get("clicks", 0) for vr in variant_results]

        if len(conversions) < 2:
            return False, None

        total_conversions = sum(conversions)
        total_clicks = sum(clicks)

        if total_clicks == 0 or total_conversions == 0:
            return False, None

        # Expected conversion rate
        expected_rate = total_conversions / total_clicks

        # Chi-squared statistic
        chi2 = 0.0
        for c, cl in zip(conversions, clicks, strict=True):
            expected_conversions = cl * expected_rate
            expected_non_conversions = cl * (1 - expected_rate)

            if expected_conversions > 0:
                chi2 += (c - expected_conversions) ** 2 / expected_conversions
            if expected_non_conversions > 0:
                non_conversions = cl - c
                chi2 += (non_conversions - expected_non_conversions) ** 2 / expected_non_conversions

        # Degrees of freedom
        df = len(conversions) - 1

        # Critical value for 95% confidence
        critical_values = {1: 3.841, 2: 5.991, 3: 7.815, 4: 9.488, 5: 11.070}
        critical = critical_values.get(df, 3.841)

        is_significant = chi2 > critical

        # Approximate p-value (simplified)
        p_value = 0.01 if chi2 > critical else 0.5

        return is_significant, p_value

    def optimize(self, campaign_id: str) -> CreativeOptimizationResult:
        """Run a complete creative optimization cycle.

        Args:
            campaign_id: Campaign identifier.

        Returns:
            CreativeOptimizationResult with test results and recommendations.
        """
        ab_result = self.run_significance_test()
        insights = self._generate_insights(ab_result)
        next_tests = self._recommend_next_tests(ab_result)

        winning_variants = []
        if ab_result.winner_variant_id:
            winning_variants.append(ab_result.winner_variant_id)

        result = CreativeOptimizationResult(
            campaign_id=campaign_id,
            ab_test=ab_result,
            winning_variants=winning_variants,
            insights=insights,
            next_test_recommendations=next_tests,
        )

        logger.info(
            "Creative optimization completed",
            campaign_id=campaign_id,
            winner=ab_result.winner_variant_id,
        )
        return result

    def _generate_insights(self, ab_result: ABTestResult) -> list[str]:
        """Generate insights from A/B test results.

        Args:
            ab_result: The A/B test result.

        Returns:
            List of insight strings.
        """
        insights = []

        if not ab_result.variant_results:
            return insights

        # Find best and worst performers
        metric = self.config.primary_metric
        sorted_variants = sorted(
            ab_result.variant_results, key=lambda x: x.get(metric, 0), reverse=True
        )

        best = sorted_variants[0]
        worst = sorted_variants[-1]

        best_val = best.get(metric, 0)
        worst_val = worst.get(metric, 0)

        if worst_val > 0:
            improvement = ((best_val - worst_val) / worst_val) * 100
            insights.append(
                f"Best variant ({best['variant_id']}) outperforms worst ({worst['variant_id']}) "
                f"by {improvement:.1f}% on {metric}"
            )

        # CTR insights
        ctrs = [vr.get("ctr", 0) for vr in ab_result.variant_results]
        if ctrs:
            avg_ctr = sum(ctrs) / len(ctrs)
            insights.append(f"Average CTR across variants: {avg_ctr:.4f}")

        # Conversion rate insights
        conv_rates = [vr.get("conversion_rate", 0) for vr in ab_result.variant_results]
        if conv_rates:
            avg_conv = sum(conv_rates) / len(conv_rates)
            insights.append(f"Average conversion rate: {avg_conv:.4f}")

        # Spend efficiency
        cpas = [vr.get("cpa", 0) for vr in ab_result.variant_results if vr.get("cpa", 0) > 0]
        if cpas:
            best_cpa = min(cpas)
            insights.append(f"Best CPA: ${best_cpa:.2f}")

        return insights

    def _recommend_next_tests(self, ab_result: ABTestResult) -> list[dict[str, Any]]:
        """Recommend next A/B tests to run.

        Args:
            ab_result: The current A/B test result.

        Returns:
            List of test recommendation dictionaries.
        """
        recommendations = []

        if not ab_result.is_significant:
            recommendations.append(
                {
                    "test_type": "increase_sample_size",
                    "reason": "Current test not statistically significant",
                    "action": "Continue test with more traffic",
                }
            )

        # Recommend testing different creative elements
        recommendations.append(
            {
                "test_type": "creative_element",
                "element": "headline",
                "reason": "Test different headline variations",
                "action": "Create variants with different headlines",
            }
        )

        recommendations.append(
            {
                "test_type": "creative_element",
                "element": "image",
                "reason": "Visual creatives significantly impact CTR",
                "action": "Test different image styles and formats",
            }
        )

        if ab_result.winner_variant_id:
            recommendations.append(
                {
                    "test_type": "iteration",
                    "base_variant": ab_result.winner_variant_id,
                    "reason": "Iterate on winning variant",
                    "action": "Create variations of the winning creative",
                }
            )

        return recommendations

    def get_variant_allocations(self) -> dict[str, float]:
        """Get current traffic allocations for all variants.

        Returns:
            Dictionary mapping variant IDs to allocation percentages.
        """
        return self.allocate_traffic()

    def get_test_history(self) -> list[ABTestResult]:
        """Get test history.

        Returns:
            List of ABTestResult objects.
        """
        return list(self._test_history)

    def reset_test(self) -> None:
        """Reset the current test state."""
        self._variants = {
            v.variant_id: CreativeVariant(
                variant_id=v.variant_id,
                name=v.name,
                creative_type=v.creative_type,
                content=v.content,
                weight=v.weight,
            )
            for v in self.config.variants
        }
        self._start_time = datetime.now()
        logger.info("Creative test reset", test_id=self.config.test_id)
