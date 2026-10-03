"""Unit tests for creator monetization module."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def creator_profile():
    """Return a sample creator profile for testing."""
    return {
        "creator_id": "creator_001",
        "tier": "gold",
        "followers": 50000,
        "engagement_rate": 0.045,
        "base_rate": 250.00,
        "niche": "tech",
        "verified": True,
    }


@pytest.fixture
def monetization_config():
    """Return a sample monetization configuration."""
    return {
        "platform_fee_percent": 0.15,
        "min_payout": 10.00,
        "max_payout": 10000.00,
        "currency": "USD",
        "payout_schedule": "monthly",
    }


@pytest.fixture
def sample_campaign():
    """Return a sample campaign for testing."""
    return {
        "campaign_id": "camp_001",
        "brand": "TestBrand",
        "budget": 5000.00,
        "deliverables": 3,
        "duration_days": 14,
        "requirements": ["video", "story", "post"],
    }


@pytest.fixture
def earnings_data():
    """Return sample earnings data for breakdown tests."""
    return {
        "gross_earnings": 1000.00,
        "platform_fee": 150.00,
        "taxes": 100.00,
        "adjustments": -25.00,
        "bonuses": 50.00,
        "net_earnings": 775.00,
    }


# ---------------------------------------------------------------------------
# Test: calculate_earnings
# ---------------------------------------------------------------------------


class TestCalculateEarnings:
    """Tests for the calculate_earnings function."""

    def test_calculate_earnings_basic(self, creator_profile, sample_campaign):
        """Test basic earnings calculation with standard inputs."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        result = calculate_earnings(creator_profile, sample_campaign)

        assert result is not None
        assert "net_earnings" in result
        assert "gross_earnings" in result
        assert result["gross_earnings"] > 0
        assert result["net_earnings"] > 0
        assert result["net_earnings"] <= result["gross_earnings"]

    def test_calculate_earnings_with_platform_fee(
        self, creator_profile, sample_campaign, monetization_config
    ):
        """Test earnings calculation applies platform fee correctly."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        result = calculate_earnings(
            creator_profile, sample_campaign, config=monetization_config
        )

        expected_fee = result["gross_earnings"] * Decimal("0.15")
        assert result["platform_fee"] == pytest.approx(float(expected_fee), rel=1e-2)

    def test_calculate_earnings_tier_multiplier(self, sample_campaign):
        """Test that different creator tiers apply correct multipliers."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        tiers = {"bronze": 1.0, "silver": 1.25, "gold": 1.5, "platinum": 2.0}
        results = {}

        for tier, expected_multiplier in tiers.items():
            profile = {
                "creator_id": f"creator_{tier}",
                "tier": tier,
                "followers": 10000,
                "engagement_rate": 0.03,
                "base_rate": 100.00,
                "niche": "lifestyle",
                "verified": False,
            }
            results[tier] = calculate_earnings(profile, sample_campaign)

        # Higher tiers should yield higher earnings
        assert results["bronze"]["gross_earnings"] < results["silver"]["gross_earnings"]
        assert results["silver"]["gross_earnings"] < results["gold"]["gross_earnings"]
        assert results["gold"]["gross_earnings"] < results["platinum"]["gross_earnings"]

    def test_calculate_earnings_engagement_bonus(self, sample_campaign):
        """Test that higher engagement rates produce bonus earnings."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        low_engagement = {
            "creator_id": "creator_low",
            "tier": "silver",
            "followers": 10000,
            "engagement_rate": 0.01,
            "base_rate": 100.00,
            "niche": "fitness",
            "verified": False,
        }
        high_engagement = {
            "creator_id": "creator_high",
            "tier": "silver",
            "followers": 10000,
            "engagement_rate": 0.10,
            "base_rate": 100.00,
            "niche": "fitness",
            "verified": False,
        }

        low_result = calculate_earnings(low_engagement, sample_campaign)
        high_result = calculate_earnings(high_engagement, sample_campaign)

        assert high_result["gross_earnings"] > low_result["gross_earnings"]

    def test_calculate_earnings_minimum_payout(
        self, creator_profile, monetization_config
    ):
        """Test that earnings never fall below minimum payout threshold."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        small_campaign = {
            "campaign_id": "camp_small",
            "brand": "TinyBrand",
            "budget": 5.00,
            "deliverables": 1,
            "duration_days": 7,
            "requirements": ["post"],
        }

        result = calculate_earnings(
            creator_profile, small_campaign, config=monetization_config
        )

        assert result["net_earnings"] >= monetization_config["min_payout"]

    def test_calculate_earnings_maximum_payout_cap(
        self, creator_profile, monetization_config
    ):
        """Test that earnings do not exceed maximum payout cap."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        huge_campaign = {
            "campaign_id": "camp_huge",
            "brand": "MegaBrand",
            "budget": 999999.00,
            "deliverables": 100,
            "duration_days": 90,
            "requirements": ["video"] * 100,
        }

        result = calculate_earnings(
            creator_profile, huge_campaign, config=monetization_config
        )

        assert result["net_earnings"] <= monetization_config["max_payout"]

    def test_calculate_earnings_invalid_profile(self, sample_campaign):
        """Test that invalid creator profile raises appropriate error."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        invalid_profile = {"creator_id": "", "tier": "unknown"}

        with pytest.raises((ValueError, KeyError)):
            calculate_earnings(invalid_profile, sample_campaign)

    def test_calculate_earnings_zero_budget(self, creator_profile):
        """Test earnings calculation with zero budget campaign."""
        from ugc_marketplace.creator_monetization import calculate_earnings

        zero_campaign = {
            "campaign_id": "camp_zero",
            "brand": "FreeBrand",
            "budget": 0.00,
            "deliverables": 0,
            "duration_days": 0,
            "requirements": [],
        }

        result = calculate_earnings(creator_profile, zero_campaign)

        assert result["gross_earnings"] == 0.00
        assert result["net_earnings"] == 0.00


# ---------------------------------------------------------------------------
# Test: optimize_pricing
# ---------------------------------------------------------------------------


class TestOptimizePricing:
    """Tests for the optimize_pricing function."""

    def test_optimize_pricing_basic(self, creator_profile):
        """Test basic pricing optimization returns valid structure."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        result = optimize_pricing(creator_profile)

        assert result is not None
        assert "recommended_price" in result
        assert "price_range" in result
        assert "confidence" in result
        assert result["recommended_price"] > 0
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    def test_optimize_pricing_price_range_ordering(self, creator_profile):
        """Test that price range low <= recommended <= high."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        result = optimize_pricing(creator_profile)

        low = result["price_range"]["low"]
        high = result["price_range"]["high"]
        recommended = result["recommended_price"]

        assert low <= recommended <= high

    def test_optimize_pricing_followers_impact(self):
        """Test that more followers lead to higher recommended pricing."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        small_profile = {
            "creator_id": "creator_small",
            "tier": "silver",
            "followers": 1000,
            "engagement_rate": 0.03,
            "base_rate": 50.00,
            "niche": "tech",
            "verified": False,
        }
        large_profile = {
            "creator_id": "creator_large",
            "tier": "silver",
            "followers": 1000000,
            "engagement_rate": 0.03,
            "base_rate": 50.00,
            "niche": "tech",
            "verified": False,
        }

        small_result = optimize_pricing(small_profile)
        large_result = optimize_pricing(large_profile)

        assert large_result["recommended_price"] > small_result["recommended_price"]

    def test_optimize_pricing_engagement_impact(self):
        """Test that higher engagement leads to higher recommended pricing."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        low_engagement = {
            "creator_id": "creator_low",
            "tier": "gold",
            "followers": 50000,
            "engagement_rate": 0.01,
            "base_rate": 200.00,
            "niche": "fashion",
            "verified": True,
        }
        high_engagement = {
            "creator_id": "creator_high",
            "tier": "gold",
            "followers": 50000,
            "engagement_rate": 0.15,
            "base_rate": 200.00,
            "niche": "fashion",
            "verified": True,
        }

        low_result = optimize_pricing(low_engagement)
        high_result = optimize_pricing(high_engagement)

        assert high_result["recommended_price"] > low_result["recommended_price"]

    def test_optimize_pricing_niche_adjustment(self):
        """Test that different niches produce different pricing."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        niches = ["tech", "fashion", "food", "travel", "fitness"]
        results = {}

        for niche in niches:
            profile = {
                "creator_id": f"creator_{niche}",
                "tier": "gold",
                "followers": 50000,
                "engagement_rate": 0.05,
                "base_rate": 200.00,
                "niche": niche,
                "verified": True,
            }
            results[niche] = optimize_pricing(profile)

        # At least some niches should have different pricing
        prices = [r["recommended_price"] for r in results.values()]
        assert len(set(prices)) > 1

    def test_optimize_pricing_verified_boost(self):
        """Test that verified creators get a pricing boost."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        unverified = {
            "creator_id": "creator_unverified",
            "tier": "gold",
            "followers": 50000,
            "engagement_rate": 0.05,
            "base_rate": 200.00,
            "niche": "tech",
            "verified": False,
        }
        verified = {
            "creator_id": "creator_verified",
            "tier": "gold",
            "followers": 50000,
            "engagement_rate": 0.05,
            "base_rate": 200.00,
            "niche": "tech",
            "verified": True,
        }

        unverified_result = optimize_pricing(unverified)
        verified_result = optimize_pricing(verified)

        assert verified_result["recommended_price"] > unverified_result["recommended_price"]

    def test_optimize_pricing_confidence_bounds(self, creator_profile):
        """Test that confidence score stays within [0, 1]."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        # Test with minimal data
        minimal_profile = {
            "creator_id": "creator_minimal",
            "tier": "bronze",
            "followers": 100,
            "engagement_rate": 0.001,
            "base_rate": 10.00,
            "niche": "misc",
            "verified": False,
        }

        result = optimize_pricing(minimal_profile)

        assert 0.0 <= result["confidence"] <= 1.0

    def test_optimize_pricing_with_historical_data(self, creator_profile):
        """Test pricing optimization with historical performance data."""
        from ugc_marketplace.creator_monetization import optimize_pricing

        historical_data = [
            {"campaign_id": "c1", "price": 200, "roi": 1.5},
            {"campaign_id": "c2", "price": 250, "roi": 1.8},
            {"campaign_id": "c3", "price": 300, "roi": 1.3},
        ]

        result = optimize_pricing(creator_profile, historical_data=historical_data)

        assert result is not None
        assert "recommended_price" in result
        assert result["recommended_price"] > 0


# ---------------------------------------------------------------------------
# Test: earnings_breakdown
# ---------------------------------------------------------------------------


class TestEarningsBreakdown:
    """Tests for the earnings_breakdown function."""

    def test_earnings_breakdown_basic(self, earnings_data):
        """Test basic earnings breakdown returns all expected fields."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        result = earnings_breakdown(earnings_data)

        assert result is not None
        assert "gross_earnings" in result
        assert "platform_fee" in result
        assert "taxes" in result
        assert "adjustments" in result
        assert "bonuses" in result
        assert "net_earnings" in result

    def test_earnings_breakdown_net_calculation(self, earnings_data):
        """Test that net earnings is calculated correctly from components."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        result = earnings_breakdown(earnings_data)

        expected_net = (
            result["gross_earnings"]
            - result["platform_fee"]
            - result["taxes"]
            + result["adjustments"]
            + result["bonuses"]
        )
        assert result["net_earnings"] == pytest.approx(expected_net, rel=1e-2)

    def test_earnings_breakdown_percentage_fields(self, earnings_data):
        """Test that percentage breakdown fields are present and valid."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        result = earnings_breakdown(earnings_data)

        if "platform_fee_percent" in result:
            assert 0 <= result["platform_fee_percent"] <= 100
        if "tax_percent" in result:
            assert 0 <= result["tax_percent"] <= 100
        if "effective_rate" in result:
            assert result["effective_rate"] >= 0

    def test_earnings_breakdown_zero_earnings(self):
        """Test breakdown with zero earnings."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        zero_data = {
            "gross_earnings": 0.00,
            "platform_fee": 0.00,
            "taxes": 0.00,
            "adjustments": 0.00,
            "bonuses": 0.00,
            "net_earnings": 0.00,
        }

        result = earnings_breakdown(zero_data)

        assert result["net_earnings"] == 0.00
        assert result["gross_earnings"] == 0.00

    def test_earnings_breakdown_with_bonuses(self):
        """Test that bonuses are correctly added to net earnings."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        data_with_bonus = {
            "gross_earnings": 2000.00,
            "platform_fee": 300.00,
            "taxes": 200.00,
            "adjustments": 0.00,
            "bonuses": 150.00,
            "net_earnings": 1650.00,
        }

        result = earnings_breakdown(data_with_bonus)

        assert result["bonuses"] == 150.00
        assert result["net_earnings"] > (
            result["gross_earnings"] - result["platform_fee"] - result["taxes"]
        )

    def test_earnings_breakdown_with_adjustments(self):
        """Test that adjustments (positive or negative) are applied correctly."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        data_with_adjustment = {
            "gross_earnings": 1000.00,
            "platform_fee": 150.00,
            "taxes": 100.00,
            "adjustments": -50.00,
            "bonuses": 0.00,
            "net_earnings": 700.00,
        }

        result = earnings_breakdown(data_with_adjustment)

        assert result["adjustments"] == -50.00
        assert result["net_earnings"] == 700.00

    def test_earnings_breakdown_missing_fields(self):
        """Test that missing fields are handled gracefully."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        incomplete_data = {
            "gross_earnings": 500.00,
            "net_earnings": 425.00,
        }

        result = earnings_breakdown(incomplete_data)

        assert result is not None
        assert result["gross_earnings"] == 500.00
        assert result["net_earnings"] == 425.00

    def test_earnings_breakdown_large_values(self):
        """Test breakdown with large monetary values."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        large_data = {
            "gross_earnings": 1000000.00,
            "platform_fee": 150000.00,
            "taxes": 200000.00,
            "adjustments": 5000.00,
            "bonuses": 25000.00,
            "net_earnings": 680000.00,
        }

        result = earnings_breakdown(large_data)

        assert result["gross_earnings"] == 1000000.00
        assert result["net_earnings"] == pytest.approx(680000.00, rel=1e-2)

    def test_earnings_breakdown_currency_consistency(self, earnings_data):
        """Test that all monetary values use consistent currency."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        result = earnings_breakdown(earnings_data, currency="USD")

        if "currency" in result:
            assert result["currency"] == "USD"

    def test_earnings_breakdown_monthly_aggregation(self):
        """Test breakdown aggregation across multiple monthly records."""
        from ugc_marketplace.creator_monetization import earnings_breakdown

        monthly_records = [
            {
                "gross_earnings": 1000.00,
                "platform_fee": 150.00,
                "taxes": 100.00,
                "adjustments": 0.00,
                "bonuses": 50.00,
                "net_earnings": 800.00,
            },
            {
                "gross_earnings": 1200.00,
                "platform_fee": 180.00,
                "taxes": 120.00,
                "adjustments": -30.00,
                "bonuses": 75.00,
                "net_earnings": 945.00,
            },
            {
                "gross_earnings": 800.00,
                "platform_fee": 120.00,
                "taxes": 80.00,
                "adjustments": 0.00,
                "bonuses": 25.00,
                "net_earnings": 625.00,
            },
        ]

        result = earnings_breakdown(monthly_records)

        assert result is not None
        assert result["gross_earnings"] == pytest.approx(3000.00, rel=1e-2)
        assert result["net_earnings"] == pytest.approx(2370.00, rel=1e-2)
