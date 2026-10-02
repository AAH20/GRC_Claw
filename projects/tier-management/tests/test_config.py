"""Tests for configuration and settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tier_management.config.settings import Settings, get_settings


def test_settings_defaults() -> None:
    """Test Settings has correct default values."""
    settings = Settings()
    assert settings.app_name == "tier-management"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.port == 8000


def test_settings_is_production() -> None:
    """Test is_production property."""
    settings = Settings(environment="production")
    assert settings.is_production is True
    assert settings.is_development is False


def test_settings_is_development() -> None:
    """Test is_development property."""
    settings = Settings(environment="development")
    assert settings.is_development is True
    assert settings.is_production is False


def test_settings_invalid_log_level() -> None:
    """Test Settings rejects invalid log level."""
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID")


def test_settings_invalid_environment() -> None:
    """Test Settings rejects invalid environment."""
    with pytest.raises(ValidationError):
        Settings(environment="invalid")


def test_get_settings_caching() -> None:
    """Test get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_custom_values() -> None:
    """Test Settings with custom values."""
    settings = Settings(
        app_name="custom-tier",
        environment="staging",
        port=9000,
        log_level="DEBUG",
    )
    assert settings.app_name == "custom-tier"
    assert settings.environment == "staging"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"
