"""Unit tests for tier management in gated-communities."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tier_config():
    """Return a sample tier configuration."""
    return {
        "free": {
            "level": 0,
            "max_communities": 3,
            "max_members_per_community": 50,
            "features": ["basic_chat", "public_posts"],
            "support_level": "community",
        },
        "basic": {
            "level": 1,
            "max_communities": 10,
            "max_members_per_community": 200,
            "features": ["basic_chat", "public_posts", "private_groups", "file_sharing"],
            "support_level": "email",
        },
        "premium": {
            "level": 2,
            "max_communities": 50,
            "max_members_per_community": 1000,
            "features": [
                "basic_chat",
                "public_posts",
                "private_groups",
                "file_sharing",
                "analytics",
                "custom_branding",
                "api_access",
            ],
            "support_level": "priority",
        },
        "enterprise": {
            "level": 3,
            "max_communities": -1,  # unlimited
            "max_members_per_community": -1,  # unlimited
            "features": [
                "basic_chat",
                "public_posts",
                "private_groups",
                "file_sharing",
                "analytics",
                "custom_branding",
                "api_access",
                "sso",
                "audit_logs",
                "dedicated_support",
            ],
            "support_level": "dedicated",
        },
    }


@pytest.fixture
def user_subscription():
    """Return a sample user subscription."""
    return {
        "user_id": "user-123",
        "current_tier": "free",
        "started_at": datetime(2025, 1, 1),
        "expires_at": datetime(2025, 12, 31),
        "auto_renew": True,
        "payment_method": "card_ending_4242",
    }


@pytest.fixture
def community_usage():
    """Return sample community usage data."""
    return {
        "user_id": "user-123",
        "total_communities": 2,
        "total_members_across_communities": 35,
        "storage_used_mb": 150,
        "api_calls_this_month": 500,
        "active_moderators": 1,
    }


@pytest.fixture
def tier_manager(tier_config):
    """Return a TierManager instance with the given config."""
    from src.agents.gated_communities.tier_management import TierManager

    return TierManager(config=tier_config)


# ---------------------------------------------------------------------------
# Tests: evaluate_tier_upgrade
# ---------------------------------------------------------------------------


class TestEvaluateTierUpgrade:
    """Tests for tier upgrade evaluation logic."""

    def test_evaluate_tier_upgrade__eligible_for_upgrade(
        self, tier_manager, user_subscription, community_usage
    ):
        """User exceeding free limits should be eligible for upgrade."""
        # User is at max communities for free tier
        community_usage["total_communities"] = 3
        community_usage["total_members_across_communities"] = 60

        result = tier_manager.evaluate_tier_upgrade(
            subscription=user_subscription,
            usage=community_usage,
        )

        assert result["eligible"] is True
        assert result["current_tier"] == "free"
        assert result["recommended_tier"] == "basic"
        assert "limit_exceeded" in result["reasons"]

    def test_evaluate_tier_upgrade__not_eligible_when_within_limits(
        self, tier_manager, user_subscription, community_usage
    ):
        """User within all limits should not be flagged for upgrade."""
        community_usage["total_communities"] = 1
        community_usage["total_members_across_communities"] = 10

        result = tier_manager.evaluate_tier_upgrade(
            subscription=user_subscription,
            usage=community_usage,
        )

        assert result["eligible"] is False
        assert result["current_tier"] == "free"
        assert result["recommended_tier"] == "free"

    def test_evaluate_tier_upgrade__already_at_highest_tier(
        self, tier_manager, community_usage
    ):
        """Enterprise users should never be recommended an upgrade."""
        subscription = {
            "user_id": "user-456",
            "current_tier": "enterprise",
            "started_at": datetime(2025, 1, 1),
            "expires_at": datetime(2025, 12, 31),
            "auto_renew": True,
        }

        result = tier_manager.evaluate_tier_upgrade(
            subscription=subscription,
            usage=community_usage,
        )

        assert result["eligible"] is False
        assert result["current_tier"] == "enterprise"
        assert result["recommended_tier"] == "enterprise"

    def test_evaluate_tier_upgrade__storage_limit_triggers_upgrade(
        self, tier_manager, user_subscription, community_usage
    ):
        """Exceeding storage limits should trigger upgrade recommendation."""
        community_usage["storage_used_mb"] = 5000  # Exceeds typical free limit

        result = tier_manager.evaluate_tier_upgrade(
            subscription=user_subscription,
            usage=community_usage,
        )

        assert result["eligible"] is True
        assert any("storage" in reason for reason in result["reasons"])

    def test_evaluate_tier_upgrade__api_usage_triggers_upgrade(
        self, tier_manager, user_subscription, community_usage
    ):
        """High API usage should trigger upgrade recommendation."""
        community_usage["api_calls_this_month"] = 10000

        result = tier_manager.evaluate_tier_upgrade(
            subscription=user_subscription,
            usage=community_usage,
        )

        assert result["eligible"] is True
        assert any("api" in reason for reason in result["reasons"])

    def test_evaluate_tier_upgrade__expiring_subscription_priority(
        self, tier_manager, community_usage
    ):
        """Expiring subscriptions should be prioritized for upgrade prompts."""
        subscription = {
            "user_id": "user-789",
            "current_tier": "basic",
            "started_at": datetime(2025, 1, 1),
            "expires_at": datetime.now() + timedelta(days=5),
            "auto_renew": False,
        }

        result = tier_manager.evaluate_tier_upgrade(
            subscription=subscription,
            usage=community_usage,
        )

        assert result["eligible"] is True
        assert result["urgency"] == "high"
        assert any("expiring" in reason for reason in result["reasons"])

    def test_evaluate_tier_upgrade__returns_upgrade_path(
        self, tier_manager, user_subscription, community_usage
    ):
        """Result should include the upgrade path with intermediate tiers."""
        community_usage["total_communities"] = 3
        community_usage["total_members_across_community"] = 60

        result = tier_manager.evaluate_tier_upgrade(
            subscription=user_subscription,
            usage=community_usage,
        )

        assert "upgrade_path" in result
        assert isinstance(result["upgrade_path"], list)
        assert len(result["upgrade_path"]) > 0

    def test_evaluate_tier_upgrade__invalid_tier_raises_error(
        self, tier_manager, community_usage
    ):
        """An unknown current tier should raise a ValueError."""
        subscription = {
            "user_id": "user-000",
            "current_tier": "nonexistent_tier",
            "started_at": datetime(2025, 1, 1),
            "expires_at": datetime(2025, 12, 31),
        }

        with pytest.raises(ValueError, match="Unknown tier"):
            tier_manager.evaluate_tier_upgrade(
                subscription=subscription,
                usage=community_usage,
            )


# ---------------------------------------------------------------------------
# Tests: calculate_tier_benefits
# ---------------------------------------------------------------------------


class TestCalculateTierBenefits:
    """Tests for tier benefits calculation."""

    def test_calculate_tier_benefits__free_tier_benefits(
        self, tier_manager, tier_config
    ):
        """Free tier should return correct base benefits."""
        benefits = tier_manager.calculate_tier_benefits("free")

        assert benefits["tier"] == "free"
        assert benefits["max_communities"] == 3
        assert benefits["max_members_per_community"] == 50
        assert "basic_chat" in benefits["features"]
        assert "public_posts" in benefits["features"]
        assert benefits["support_level"] == "community"
        assert benefits["price_monthly"] == 0

    def test_calculate_tier_benefits__basic_tier_benefits(
        self, tier_manager, tier_config
    ):
        """Basic tier should include all expected features."""
        benefits = tier_manager.calculate_tier_benefits("basic")

        assert benefits["tier"] == "basic"
        assert benefits["max_communities"] == 10
        assert benefits["max_members_per_community"] == 200
        assert "private_groups" in benefits["features"]
        assert "file_sharing" in benefits["features"]
        assert benefits["support_level"] == "email"
        assert benefits["price_monthly"] > 0

    def test_calculate_tier_benefits__premium_tier_benefits(
        self, tier_manager, tier_config
    ):
        """Premium tier should include advanced features."""
        benefits = tier_manager.calculate_tier_benefits("premium")

        assert benefits["tier"] == "premium"
        assert benefits["max_communities"] == 50
        assert benefits["max_members_per_community"] == 1000
        assert "analytics" in benefits["features"]
        assert "custom_branding" in benefits["features"]
        assert "api_access" in benefits["features"]
        assert benefits["support_level"] == "priority"

    def test_calculate_tier_benefits__enterprise_tier_benefits(
        self, tier_manager, tier_config
    ):
        """Enterprise tier should have unlimited limits and all features."""
        benefits = tier_manager.calculate_tier_benefits("enterprise")

        assert benefits["tier"] == "enterprise"
        assert benefits["max_communities"] == -1
        assert benefits["max_members_per_community"] == -1
        assert "sso" in benefits["features"]
        assert "audit_logs" in benefits["features"]
        assert "dedicated_support" in benefits["features"]
        assert benefits["support_level"] == "dedicated"

    def test_calculate_tier_benefits__includes_feature_descriptions(
        self, tier_manager
    ):
        """Benefits should include human-readable feature descriptions."""
        benefits = tier_manager.calculate_tier_benefits("premium")

        assert "feature_descriptions" in benefits
        assert isinstance(benefits["feature_descriptions"], dict)
        assert len(benefits["feature_descriptions"]) > 0

    def test_calculate_tier_benefits__includes_usage_limits(
        self, tier_manager
    ):
        """Benefits should include detailed usage limits."""
        benefits = tier_manager.calculate_tier_benefits("basic")

        assert "usage_limits" in benefits
        limits = benefits["usage_limits"]
        assert "storage_mb" in limits
        assert "api_calls_per_month" in limits
        assert "moderators_per_community" in limits

    def test_calculate_tier_benefits__comparison_with_lower_tier(
        self, tier_manager
    ):
        """Each tier should show what's gained over the previous tier."""
        benefits = tier_manager.calculate_tier_benefits("premium")

        assert "upgrade_gains" in benefits
        assert isinstance(benefits["upgrade_gains"], list)
        assert len(benefits["upgrade_gains"]) > 0

    def test_calculate_tier_benefits__invalid_tier_raises_error(
        self, tier_manager
    ):
        """Requesting benefits for unknown tier should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown tier"):
            tier_manager.calculate_tier_benefits("platinum")

    def test_calculate_tier_benefits__all_tiers_have_required_keys(
        self, tier_manager, tier_config
    ):
        """Every tier's benefits dict must contain the required keys."""
        required_keys = {
            "tier",
            "max_communities",
            "max_members_per_community",
            "features",
            "support_level",
            "price_monthly",
        }

        for tier_name in tier_config:
            benefits = tier_manager.calculate_tier_benefits(tier_name)
            missing = required_keys - set(benefits.keys())
            assert not missing, f"Tier '{tier_name}' missing keys: {missing}"

    def test_calculate_tier_benefits__price_increases_with_tier_level(
        self, tier_manager
    ):
        """Higher tiers should cost more than lower tiers."""
        free = tier_manager.calculate_tier_benefits("free")
        basic = tier_manager.calculate_tier_benefits("basic")
        premium = tier_manager.calculate_tier_benefits("premium")
        enterprise = tier_manager.calculate_tier_benefits("enterprise")

        assert free["price_monthly"] < basic["price_monthly"]
        assert basic["price_monthly"] < premium["price_monthly"]
        assert premium["price_monthly"] < enterprise["price_monthly"]


# ---------------------------------------------------------------------------
# Tests: tier_recommendation
# ---------------------------------------------------------------------------


class TestTierRecommendation:
    """Tests for tier recommendation engine."""

    def test_tier_recommendation__recommends_free_for_new_user(
        self, tier_manager
    ):
        """A new user with no usage should be recommended the free tier."""
        usage = {
            "total_communities": 0,
            "total_members_across_communities": 0,
            "storage_used_mb": 0,
            "api_calls_this_month": 0,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] == "free"
        assert result["confidence"] >= 0.8

    def test_tier_recommendation__recommends_basic_for_moderate_usage(
        self, tier_manager
    ):
        """Moderate usage should recommend basic tier."""
        usage = {
            "total_communities": 5,
            "total_members_across_communities": 100,
            "storage_used_mb": 500,
            "api_calls_this_month": 2000,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] == "basic"
        assert result["confidence"] >= 0.6

    def test_tier_recommendation__recommends_premium_for_heavy_usage(
        self, tier_manager
    ):
        """Heavy usage should recommend premium tier."""
        usage = {
            "total_communities": 25,
            "total_members_across_communities": 500,
            "storage_used_mb": 5000,
            "api_calls_this_month": 15000,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] == "premium"
        assert result["confidence"] >= 0.6

    def test_tier_recommendation__recommends_enterprise_for_power_users(
        self, tier_manager
    ):
        """Very heavy usage should recommend enterprise tier."""
        usage = {
            "total_communities": 100,
            "total_members_across_communities": 5000,
            "storage_used_mb": 50000,
            "api_calls_this_month": 100000,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] == "enterprise"
        assert result["confidence"] >= 0.6

    def test_tier_recommendation__considers_user_preferences(
        self, tier_manager
    ):
        """User preferences should influence the recommendation."""
        usage = {
            "total_communities": 5,
            "total_members_across_communities": 100,
            "storage_used_mb": 500,
            "api_calls_this_month": 2000,
        }
        preferences = {
            "priority": "cost",  # Prefer cheaper options
            "max_budget_monthly": 10,
        }

        result = tier_manager.recommend_tier(usage=usage, preferences=preferences)

        # With cost priority and low budget, should not recommend premium
        assert result["recommended_tier"] in ("free", "basic")

    def test_tier_recommendation__considers_feature_requirements(
        self, tier_manager
    ):
        """Required features should drive tier recommendation."""
        usage = {
            "total_communities": 1,
            "total_members_across_communities": 10,
            "storage_used_mb": 50,
            "api_calls_this_month": 100,
        }
        required_features = ["analytics", "api_access"]

        result = tier_manager.recommend_tier(
            usage=usage, required_features=required_features
        )

        # Analytics and api_access are premium features
        assert result["recommended_tier"] == "premium"

    def test_tier_recommendation__returns_alternatives(
        self, tier_manager
    ):
        """Recommendation should include alternative tiers."""
        usage = {
            "total_communities": 5,
            "total_members_across_communities": 100,
            "storage_used_mb": 500,
            "api_calls_this_month": 2000,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert "alternatives" in result
        assert isinstance(result["alternatives"], list)
        assert len(result["alternatives"]) >= 1
        # The primary recommendation should not be in alternatives
        assert result["recommended_tier"] not in result["alternatives"]

    def test_tier_recommendation__returns_reasoning(
        self, tier_manager
    ):
        """Recommendation should explain why a tier was chosen."""
        usage = {
            "total_communities": 25,
            "total_members_across_communities": 500,
            "storage_used_mb": 5000,
            "api_calls_this_month": 15000,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert "reasoning" in result
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0

    def test_tier_recommendation__handles_empty_usage(
        self, tier_manager
    ):
        """Empty/zero usage should default to free tier."""
        usage = {
            "total_communities": 0,
            "total_members_across_communities": 0,
            "storage_used_mb": 0,
            "api_calls_this_month": 0,
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] == "free"
        assert result["confidence"] >= 0.9

    def test_tier_recommendation__handles_partial_usage_data(
        self, tier_manager
    ):
        """Missing usage fields should be handled gracefully."""
        usage = {
            "total_communities": 5,
            # Missing other fields
        }

        result = tier_manager.recommend_tier(usage=usage)

        assert result["recommended_tier"] in ("free", "basic", "premium", "enterprise")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_tier_recommendation__confidence_within_bounds(
        self, tier_manager
    ):
        """Confidence score should always be between 0 and 1."""
        usage_scenarios = [
            {"total_communities": 0, "total_members_across_communities": 0},
            {"total_communities": 5, "total_members_across_communities": 100},
            {"total_communities": 50, "total_members_across_communities": 1000},
            {"total_communities": 200, "total_members_across_communities": 10000},
        ]

        for usage in usage_scenarios:
            result = tier_manager.recommend_tier(usage=usage)
            assert 0.0 <= result["confidence"] <= 1.0, (
                f"Confidence out of bounds for usage {usage}: {result['confidence']}"
            )

    def test_tier_recommendation__downgrade_recommendation(
        self, tier_manager
    ):
        """Over-provisioned users should be recommended a downgrade."""
        # User on premium but with very low usage
        usage = {
            "total_communities": 1,
            "total_members_across_communities": 5,
            "storage_used_mb": 10,
            "api_calls_this_month": 50,
        }
        current_tier = "premium"

        result = tier_manager.recommend_tier(usage=usage, current_tier=current_tier)

        assert result["recommended_tier"] != "premium"
        assert result["recommended_tier"] in ("free", "basic")
        assert result.get("is_downgrade") is True
