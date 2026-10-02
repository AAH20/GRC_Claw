"""Tests for the configuration settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from onboarding_automator.config.settings import Settings, get_settings


def test_settings_defaults() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.log_level == "INFO"


def test_settings_is_production() -> None:
    """Test production environment detection."""
    assert Settings(environment="production").is_production is True
    assert Settings(environment="development").is_production is False


def test_settings_is_test() -> None:
    """Test test environment detection."""
    assert Settings(environment="test").is_test is True
    assert Settings(environment="production").is_test is False


def test_invalid_log_level() -> None:
    """Test validation of invalid log level."""
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID")


def test_invalid_temperature() -> None:
    """Test validation of invalid temperature."""
    with pytest.raises(ValidationError):
        Settings(llm_temperature=3.0)


def test_get_settings_cached() -> None:
    """Test that get_settings returns cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
