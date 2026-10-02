"""Tests for configuration settings."""

from __future__ import annotations

from quality_scoring.config.settings import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.app_name == "quality-scoring"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.port == 8000


def test_settings_is_production():
    settings = Settings(environment="production")
    assert settings.is_production is True


def test_settings_is_not_production():
    settings = Settings(environment="development")
    assert settings.is_production is False


def test_get_settings_returns_cached():
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
