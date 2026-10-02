"""Tests for creative optimizer agent with A/B testing."""
from __future__ import annotations

import pytest

from campaign_agents.agents.creative_optimizer import CreativeOptimizer
from campaign_agents.models.optimization import (
    ABTestConfig,
    ABTestResult,
    CreativeOptimizationResult,
    CreativeVariant,
)


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def basic_ab_config() -> ABTestConfig:
    """Create a basic A/B test configuration."""
    return ABTestConfig(
        test_id="test_001",
        campaign_id="campaign_123",
        variants=[
            CreativeVariant(
                variant_id="variant_a",
                name="Control",
                creative_type="image",
                content={"headline": "Buy Now", "image": "product_1.jpg"},
                impressions=1000,
                clicks=50,
                conversions=5,
                spend=100.0,
            ),
            CreativeVariant(
                variant_id="variant_b",
                name="Treatment",
                creative_type="image",
                content={"headline": "Special Offer", "image": "product_2.jpg"},
                impressions=1000,
                clicks=70,
                conversions=8,
                spend=120.0,
            ),
        ],
        primary_metric="ctr",
        min_sample_size=100,
    )


@pytest.fixture
def creative_optimizer(basic_ab_config: ABTestConfig) -> CreativeOptimizer:
    """Create a creative optimizer with basic config."""
    return CreativeOptimizer(basic_ab_config)


@pytest.fixture
def winning_variant_config() -> ABTestConfig:
    """Create A/B test config with a clear winner."""
    return ABTestConfig(
        test_id="test_002",
        campaign_id="campaign_456",
        variants=[
            CreativeVariant(
                variant_id="variant_a",
                name="Control",
                creative_type="image",
                content={"headline": "Buy Now"},
                impressions=5000,
                clicks=100,
                conversions=10,
                spend=500.0,
            ),
            CreativeVariant(
                variant_id="variant_b",
                name="Treatment",
                creative_type="video",
                content={"headline": "Watch Demo"},
                impressions=5000,
                clicks=300,
                conversions=45,
                spend=600.0,
            ),
        ],
        primary_metric="ctr",
        min_sample_size=1000,
    )


# ─── Initialization Tests ───────────────────────────────────────────


class TestCreativeOptimizerInit:
    """Tests for creative optimizer initialization."""

    def test_init_with_basic_config(self, basic_ab_config: ABTestConfig) -> None:
        """Test initialization with basic config."""
        optimizer = CreativeOptimizer(basic_ab_config)
        assert optimizer.config.test_id == "test_001"
        assert optimizer.config.campaign_id == "campaign_123"
        assert len(optimizer._variants) == 2

    def test_init_single_variant_raises(self) -> None:
        """Test that single variant raises ValueError."""
        with pytest.raises(ValueError, match="At least 2 variants"):
            CreativeOptimizer(
                ABTestConfig(
                    test_id="test_001",
                    campaign_id="campaign_123",
                    variants=[
                        CreativeVariant(
                            variant_id="variant_a",
                            name="Only Variant",
                            creative_type="image",
                        ),
                    ],
                )
            )

    def test_init_duplicate_variant_ids_raises(self) -> None:
        """Test that duplicate variant IDs raise ValueError."""
        with pytest.raises(ValueError, match="Variant IDs must be unique"):
            CreativeOptimizer(
                ABTestConfig(
                    test_id="test_001",
                    campaign_id="campaign_123",
                    variants=[
                        CreativeVariant(
                            variant_id="variant_a",
                            name="Variant A",
                            creative_type="image",
                        ),
                        CreativeVariant(
                            variant_id="variant_a",
                            name="Variant A Duplicate",
                            creative_type="video",
                        ),
                    ],
                )
            )

    def test_init_invalid_confidence_raises(self) -> None:
        """Test that invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Confidence level must be between 0 and 1"):
            CreativeOptimizer(
                ABTestConfig(
                    test_id="test_001",
                    campaign_id="campaign_123",
                    variants=[
                        CreativeVariant(variant_id="a", name="A", creative_type="image"),
                        CreativeVariant(variant_id="b", name="B", creative_type="video"),
                    ],
                    confidence_level=1.5,
                )
            )

    def test_init_min_sample_size_raises(self) -> None:
        """Test that minimum sample size below 100 raises ValueError."""
        with pytest.raises(ValueError, match="Minimum sample size must be at least 100"):
            CreativeOptimizer(
                ABTestConfig(
                    test_id="test_001",
                    campaign_id="campaign_123",
                    variants=[
                        CreativeVariant(variant_id="a", name="A", creative_type="image"),
                        CreativeVariant(variant_id="b", name="B", creative_type="video"),
                    ],
                    min_sample_size=50,
                )
            )


# ─── Performance Metrics Tests ──────────────────────────────────────


class TestVariantPerformance:
    """Tests for variant performance metrics."""

    def test_get_variant_performance(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test getting performance metrics for a variant."""
        metrics = creative_optimizer.get_variant_performance("variant_a")
        assert metrics["impressions"] == 1000.0
        assert metrics["clicks"] == 50.0
        assert metrics["conversions"] == 5.0
        assert metrics["spend"] == 100.0
        assert metrics["ctr"] == pytest.approx(0.05)
        assert metrics["conversion_rate"] == pytest.approx(0.1)

    def test_get_variant_performance_invalid_id(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that invalid variant ID raises ValueError."""
        with pytest.raises(ValueError, match="Unknown variant"):
            creative_optimizer.get_variant_performance("nonexistent")

    def test_ctr_calculation(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test CTR calculation."""
        metrics = creative_optimizer.get_variant_performance("variant_b")
        assert metrics["ctr"] == pytest.approx(0.07)

    def test_cpa_calculation(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test CPA calculation."""
        metrics = creative_optimizer.get_variant_performance("variant_a")
        assert metrics["cpa"] == pytest.approx(20.0)

    def test_zero_impressions_ctr(self, basic_ab_config: ABTestConfig) -> None:
        """Test CTR with zero impressions."""
        config = ABTestConfig(
            test_id="test_003",
            campaign_id="campaign_789",
            variants=[
                CreativeVariant(variant_id="a", name="A", creative_type="image"),
                CreativeVariant(variant_id="b", name="B", creative_type="video"),
            ],
        )
        optimizer = CreativeOptimizer(config)
        metrics = optimizer.get_variant_performance("variant_a")
        assert metrics["ctr"] == 0.0


# ─── Traffic Allocation Tests ───────────────────────────────────────


class TestTrafficAllocation:
    """Tests for traffic allocation."""

    def test_allocate_traffic_returns_percentages(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that traffic allocation returns valid percentages."""
        allocations = creative_optimizer.allocate_traffic()
        assert len(allocations) == 2
        assert all(0 <= v <= 1 for v in allocations.values())
        assert sum(allocations.values()) == pytest.approx(1.0)

    def test_allocate_traffic_favors_better_performers(self, winning_variant_config: ABTestConfig) -> None:
        """Test that allocation favors better performing variants."""
        optimizer = CreativeOptimizer(winning_variant_config)
        allocations = optimizer.allocate_traffic()
        # variant_b has better CTR, should get more traffic
        assert allocations["variant_b"] > allocations["variant_a"]

    def test_allocate_traffic_with_zero_performance(self, basic_ab_config: ABTestConfig) -> None:
        """Test allocation with zero performance variants."""
        config = ABTestConfig(
            test_id="test_004",
            campaign_id="campaign_000",
            variants=[
                CreativeVariant(variant_id="a", name="A", creative_type="image"),
                CreativeVariant(variant_id="b", name="B", creative_type="video"),
            ],
        )
        optimizer = CreativeOptimizer(config)
        allocations = optimizer.allocate_traffic()
        assert len(allocations) == 2
        assert sum(allocations.values()) == pytest.approx(1.0)


# ─── Metrics Update Tests ───────────────────────────────────────────


class TestMetricsUpdate:
    """Tests for updating variant metrics."""

    def test_update_variant_metrics(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test updating variant metrics."""
        creative_optimizer.update_variant_metrics(
            "variant_a", impressions=100, clicks=10, conversions=2, spend=20.0
        )
        metrics = creative_optimizer.get_variant_performance("variant_a")
        assert metrics["impressions"] == 1100.0
        assert metrics["clicks"] == 60.0
        assert metrics["conversions"] == 7.0

    def test_update_invalid_variant_raises(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that updating invalid variant raises ValueError."""
        with pytest.raises(ValueError, match="Unknown variant"):
            creative_optimizer.update_variant_metrics("nonexistent", impressions=100)

    def test_update_with_zero_values(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test updating with zero values."""
        creative_optimizer.update_variant_metrics("variant_a", impressions=0, clicks=0)
        metrics = creative_optimizer.get_variant_performance("variant_a")
        assert metrics["impressions"] == 1000.0  # Unchanged


# ─── A/B Test Significance Tests ────────────────────────────────────


class TestSignificanceTest:
    """Tests for A/B test significance testing."""

    def test_run_significance_test_returns_result(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that significance test returns a result."""
        result = creative_optimizer.run_significance_test()
        assert isinstance(result, ABTestResult)
        assert result.test_id == "test_001"
        assert result.campaign_id == "campaign_123"

    def test_significance_test_with_clear_winner(self, winning_variant_config: ABTestConfig) -> None:
        """Test significance test with a clear winner."""
        optimizer = CreativeOptimizer(winning_variant_config)
        result = optimizer.run_significance_test()
        assert result.winner_variant_id == "variant_b"
        assert result.is_significant is True

    def test_significance_test_without_enough_data(self, basic_ab_config: ABTestConfig) -> None:
        """Test significance test without enough data."""
        config = ABTestConfig(
            test_id="test_005",
            campaign_id="campaign_111",
            variants=[
                CreativeVariant(variant_id="a", name="A", creative_type="image", impressions=10),
                CreativeVariant(variant_id="b", name="B", creative_type="video", impressions=10),
            ],
            min_sample_size=10000,
        )
        optimizer = CreativeOptimizer(config)
        result = optimizer.run_significance_test()
        assert result.is_significant is False
        assert result.winner_variant_id is None

    def test_significance_test_includes_variant_results(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that significance test includes variant results."""
        result = creative_optimizer.run_significance_test()
        assert len(result.variant_results) == 2
        assert all("variant_id" in vr for vr in result.variant_results)

    def test_significance_test_recommendation(self, winning_variant_config: ABTestConfig) -> None:
        """Test that significance test provides recommendation."""
        optimizer = CreativeOptimizer(winning_variant_config)
        result = optimizer.run_significance_test()
        assert result.recommendation != ""
        assert "winner" in result.recommendation.lower() or "variant" in result.recommendation.lower()


# ─── Full Optimization Tests ────────────────────────────────────────


class TestCreativeOptimization:
    """Tests for full creative optimization cycles."""

    def test_optimize_returns_result(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that optimize returns a CreativeOptimizationResult."""
        result = creative_optimizer.optimize("campaign_123")
        assert isinstance(result, CreativeOptimizationResult)
        assert result.campaign_id == "campaign_123"

    def test_optimize_includes_ab_test(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that optimize includes A/B test result."""
        result = creative_optimizer.optimize("campaign_123")
        assert result.ab_test is not None
        assert isinstance(result.ab_test, ABTestResult)

    def test_optimize_generates_insights(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that optimize generates insights."""
        result = creative_optimizer.optimize("campaign_123")
        assert isinstance(result.insights, list)
        assert len(result.insights) > 0

    def test_optimize_recommends_next_tests(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that optimize recommends next tests."""
        result = creative_optimizer.optimize("campaign_123")
        assert isinstance(result.next_test_recommendations, list)
        assert len(result.next_test_recommendations) > 0

    def test_optimize_with_winner(self, winning_variant_config: ABTestConfig) -> None:
        """Test optimization with a clear winner."""
        optimizer = CreativeOptimizer(winning_variant_config)
        result = optimizer.optimize("campaign_456")
        assert "variant_b" in result.winning_variants


# ─── Insight Generation Tests ───────────────────────────────────────


class TestInsightGeneration:
    """Tests for insight generation."""

    def test_insights_include_ctr_comparison(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that insights include CTR comparison."""
        result = creative_optimizer.optimize("campaign_123")
        ctr_insights = [i for i in result.insights if "ctr" in i.lower()]
        assert len(ctr_insights) > 0

    def test_insights_include_conversion_rate(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that insights include conversion rate."""
        result = creative_optimizer.optimize("campaign_123")
        conv_insights = [i for i in result.insights if "conversion" in i.lower()]
        assert len(conv_insights) > 0

    def test_insights_include_cpa(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that insights include CPA."""
        result = creative_optimizer.optimize("campaign_123")
        cpa_insights = [i for i in result.insights if "cpa" in i.lower()]
        assert len(cpa_insights) > 0


# ─── Reset Tests ────────────────────────────────────────────────────


class TestReset:
    """Tests for test reset."""

    def test_reset_clears_metrics(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that reset clears all metrics."""
        creative_optimizer.update_variant_metrics("variant_a", impressions=500, clicks=50)
        creative_optimizer.reset_test()
        metrics = creative_optimizer.get_variant_performance("variant_a")
        assert metrics["impressions"] == 0.0
        assert metrics["clicks"] == 0.0

    def test_reset_preserves_variant_config(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that reset preserves variant configuration."""
        creative_optimizer.reset_test()
        assert len(creative_optimizer._variants) == 2
        assert "variant_a" in creative_optimizer._variants
        assert "variant_b" in creative_optimizer._variants


# ─── Edge Cases ─────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases."""

    def test_zero_conversions(self, basic_ab_config: ABTestConfig) -> None:
        """Test with zero conversions."""
        config = ABTestConfig(
            test_id="test_006",
            campaign_id="campaign_222",
            variants=[
                CreativeVariant(
                    variant_id="a", name="A", creative_type="image",
                    impressions=1000, clicks=50, conversions=0, spend=100.0,
                ),
                CreativeVariant(
                    variant_id="b", name="B", creative_type="video",
                    impressions=1000, clicks=60, conversions=0, spend=120.0,
                ),
            ],
        )
        optimizer = CreativeOptimizer(config)
        result = optimizer.run_significance_test()
        assert isinstance(result, ABTestResult)

    def test_very_large_numbers(self, basic_ab_config: ABTestConfig) -> None:
        """Test with very large numbers."""
        config = ABTestConfig(
            test_id="test_007",
            campaign_id="campaign_333",
            variants=[
                CreativeVariant(
                    variant_id="a", name="A", creative_type="image",
                    impressions=10000000, clicks=500000, conversions=50000, spend=1000000.0,
                ),
                CreativeVariant(
                    variant_id="b", name="B", creative_type="video",
                    impressions=10000000, clicks=600000, conversions=60000, spend=1200000.0,
                ),
            ],
        )
        optimizer = CreativeOptimizer(config)
        result = optimizer.run_significance_test()
        assert isinstance(result, ABTestResult)

    def test_test_history_tracked(self, creative_optimizer: CreativeOptimizer) -> None:
        """Test that test history is tracked."""
        assert len(creative_optimizer.get_test_history()) == 0
        creative_optimizer.run_significance_test()
        assert len(creative_optimizer.get_test_history()) == 1
        creative_optimizer.run_significance_test()
        assert len(creative_optimizer.get_test_history()) == 2
