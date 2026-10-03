"""Tests for configuration."""

from __future__ import annotations

import pytest

from ugc_marketplace.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Test settings defaults."""
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.port == 8000


def test_get_settings() -> None:
    """Test get_settings returns singleton."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_is_production() -> None:
    """Test is_production property."""
    settings = Settings(app_env="production")
    assert settings.is_production is True
    assert settings.is_development is False


def test_is_development() -> None:
    """Test is_development property."""
    settings = Settings(app_env="development")
    assert settings.is_development is True
    assert settings.is_production is False
