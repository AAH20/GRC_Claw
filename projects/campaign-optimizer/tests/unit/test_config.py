"""Unit tests for core configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from core.config import Settings, get_settings, load_yaml_config


class TestSettings:
    """Tests for application settings."""

    def test_default_settings(self) -> None:
        """Test that default settings are loaded correctly."""
        settings = Settings()
        assert settings.app_name == "campaign-optimizer"
        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.log_level == "INFO"

    def test_environment_validation(self) -> None:
        """Test that invalid environment values are rejected."""
        with pytest.raises(ValueError, match="environment must be one of"):
            Settings(environment="invalid")

    def test_valid_environments(self) -> None:
        """Test that all valid environments are accepted."""
        for env in ["development", "staging", "production"]:
            settings = Settings(environment=env)
            assert settings.environment == env

    def test_database_settings_defaults(self) -> None:
        """Test database settings defaults."""
        settings = Settings()
        assert settings.database.pool_size == 10
        assert settings.database.max_overflow == 20

    def test_governance_settings_defaults(self) -> None:
        """Test governance settings defaults."""
        settings = Settings()
        assert settings.governance.enabled is True
        assert settings.governance.approval_threshold == 0.8
        assert "budget_limits" in settings.governance.compliance_checks

    def test_optimization_settings_defaults(self) -> None:
        """Test optimization settings defaults."""
        settings = Settings()
        assert settings.optimization.interval == 300
        assert settings.optimization.min_improvement_threshold == 0.05
        assert settings.optimization.max_budget_adjustment == 0.15


class TestLoadYamlConfig:
    """Tests for YAML configuration loading."""

    def test_load_existing_config(self, tmp_path: Path) -> None:
        """Test loading an existing YAML config file."""
        config_data = {"app": {"name": "test"}, "debug": True}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        result = load_yaml_config(str(config_file))
        assert result["app"]["name"] == "test"
        assert result["debug"] is True

    def test_load_nonexistent_config(self, tmp_path: Path) -> None:
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config(str(tmp_path / "nonexistent.yaml"))

    def test_load_empty_config(self, tmp_path: Path) -> None:
        """Test loading an empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        result = load_yaml_config(str(config_file))
        assert result == {}


class TestGetSettings:
    """Tests for the cached settings getter."""

    def test_get_settings_returns_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self) -> None:
        """Test that get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
