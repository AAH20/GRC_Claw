"""Tests for configuration module."""

from __future__ import annotations

from recruitment_platform.config.settings import Settings, get_settings


class TestSettings:
    """Test application settings."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Recruitment Platform"
        assert settings.app_version == "1.0.0"
        assert settings.port == 8000
        assert settings.debug is False

    def test_get_settings_cached(self) -> None:
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_custom_settings(self) -> None:
        """Test custom settings values."""
        settings = Settings(app_name="Custom", port=9000)
        assert settings.app_name == "Custom"
        assert settings.port == 9000
