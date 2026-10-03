"""Tests for community health scorer configuration."""

from __future__ import annotations

import pytest
from community_health_scorer.config import Settings, get_settings


class TestSettings:
    """Tests for Settings model."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "community-health-scorer"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.environment == "development"
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000
        assert settings.workers == 1
        assert settings.llm_model == "gpt-4o-mini"
        assert settings.llm_temperature == 0.1
        assert settings.llm_max_tokens == 2048
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.redis_ttl == 3600
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window == 60
        assert settings.log_level == "INFO"
        assert settings.enable_metrics is True
        assert settings.enable_tracing is False

    def test_default_weights(self) -> None:
        """Test default scoring weights."""
        settings = Settings()
        assert settings.engagement_weight == 0.30
        assert settings.toxicity_weight == 0.25
        assert settings.growth_weight == 0.25
        assert settings.churn_weight == 0.20

    def test_weights_sum(self) -> None:
        """Test that weights sum to 1.0."""
        settings = Settings()
        assert abs(settings.weights_sum - 1.0) < 0.001

    def test_is_production_false(self) -> None:
        """Test is_production is False for development."""
        settings = Settings(environment="development")
        assert settings.is_production is False

    def test_is_production_true(self) -> None:
        """Test is_production is True for production."""
        settings = Settings(environment="production")
        assert settings.is_production is True

    def test_invalid_environment(self) -> None:
        """Test invalid environment raises error."""
        with pytest.raises(ValueError, match="Environment must be one of"):
            Settings(environment="invalid")

    def test_invalid_weight_negative(self) -> None:
        """Test negative weight raises error."""
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            Settings(engagement_weight=-0.1)

    def test_invalid_weight_over_one(self) -> None:
        """Test weight over 1.0 raises error."""
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            Settings(toxicity_weight=1.5)

    def test_custom_settings(self) -> None:
        """Test creating settings with custom values."""
        settings = Settings(
            app_name="custom-scorer",
            environment="staging",
            debug=True,
            port=9000,
        )
        assert settings.app_name == "custom-scorer"
        assert settings.environment == "staging"
        assert settings.debug is True
        assert settings.port == 9000


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self) -> None:
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
