"""Tests for configuration."""

from __future__ import annotations

from content_discovery.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.app_name == "content-discovery"
    assert settings.port == 8000
    assert settings.environment == "development"


def test_settings_from_env(monkeypatch) -> None:
    """Test settings from environment variables."""
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("PORT", "9000")
    settings = Settings()
    assert settings.app_name == "test-app"
    assert settings.port == 9000


def test_get_settings_cached() -> None:
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_debug_mode() -> None:
    """Test debug mode settings."""
    settings = Settings(debug=True)
    assert settings.debug is True
