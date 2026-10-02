"""Tests for configuration and settings."""

from __future__ import annotations

from community_governance.config.settings import Settings, get_settings


def test_settings_defaults() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.app_name == "community-governance"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.log_level == "INFO"


def test_settings_is_production() -> None:
    """Test production environment detection."""
    settings = Settings(environment="production")
    assert settings.is_production is True

    settings = Settings(environment="development")
    assert settings.is_production is False


def test_settings_parse_api_keys() -> None:
    """Test parsing comma-separated API keys."""
    settings = Settings(allowed_api_keys="key1,key2,key3")
    assert settings.allowed_api_keys == ["key1", "key2", "key3"]


def test_settings_invalid_log_level() -> None:
    """Test that invalid log level raises error."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(log_level="INVALID")


def test_get_settings_cached() -> None:
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
