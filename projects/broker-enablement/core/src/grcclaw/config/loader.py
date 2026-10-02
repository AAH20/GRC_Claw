"""
Configuration loader with environment-specific overrides for GRC_Claw.

Supports loading from:
- JSON files
- YAML files
- Environment variables
- .env files
- Multiple config files with merge/override

Override precedence (highest to lowest):
1. Environment variables (GRCCLAW_*)
2. Environment-specific config file (config.production.json)
3. Local config file (config.local.json)
4. Base config file (config.json)
5. Default values
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .defaults import get_default_config
from .exceptions import LoaderError
from .types import Config, Environment

# Prefix for environment variables
ENV_PREFIX = "GRCCLAW_"

# Mapping of env var separators to nested keys
# GRCCLAW_DATABASE__POOL_SIZE -> database.pool_size
ENV_DOUBLE_UNDERSCORE = "__"


@dataclass
class LoadOptions:
    """Options for configuration loading."""

    environment: Environment | str = Environment.DEVELOPMENT
    config_dir: str | Path | None = None
    base_filename: str = "config"
    env_file: str | Path | None = None
    use_env_vars: bool = True
    use_env_file: bool = True
    use_base_file: bool = True
    use_env_specific_file: bool = True
    use_local_file: bool = True
    strict: bool = False  # Raise on unknown keys
    resolve_secrets: bool = True  # Resolve secret references


class ConfigLoader:
    """Loads and merges GRC_Claw configuration from multiple sources."""

    def __init__(self, options: LoadOptions | None = None):
        """Initialize the loader.

        Args:
            options: Loading options. Uses defaults if not provided.
        """
        self.options = options or LoadOptions()
        if isinstance(self.options.environment, str):
            self.options.environment = Environment(self.options.environment)

    def load(self) -> Config:
        """Load configuration from all sources and merge.

        Returns:
            Fully merged Config instance.

        Raises:
            LoaderError: If loading fails and strict mode is enabled.
        """
        # Start with defaults
        config = get_default_config(self.options.environment)
        config_dict = config.to_dict()

        # Layer 1: Base config file
        if self.options.use_base_file:
            base_config = self._load_base_file()
            if base_config:
                config_dict = self._deep_merge(config_dict, base_config)

        # Layer 2: Environment-specific config file
        if self.options.use_env_specific_file:
            env_config = self._load_env_specific_file()
            if env_config:
                config_dict = self._deep_merge(config_dict, env_config)

        # Layer 3: Local config file (git-ignored overrides)
        if self.options.use_local_file:
            local_config = self._load_local_file()
            if local_config:
                config_dict = self._deep_merge(config_dict, local_config)

        # Layer 4: .env file
        if self.options.use_env_file:
            env_file_vars = self._load_env_file()
            if env_file_vars:
                config_dict = self._deep_merge(config_dict, env_file_vars)

        # Layer 5: Environment variables (highest precedence)
        if self.options.use_env_vars:
            env_vars = self._load_env_vars()
            if env_vars:
                config_dict = self._deep_merge(config_dict, env_vars)

        # Convert dict back to Config
        return self._dict_to_config(config_dict)

    def load_dict(self) -> dict[str, Any]:
        """Load configuration as a plain dictionary."""
        config = self.load()
        return config.to_dict()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory."""
        if self.options.config_dir:
            return Path(self.options.config_dir)
        # Default: look in current working directory
        return Path.cwd()

    def _load_base_file(self) -> dict[str, Any] | None:
        """Load the base configuration file (config.json or config.yaml)."""
        config_dir = self._get_config_dir()
        for ext in [".json", ".yaml", ".yml"]:
            path = config_dir / f"{self.options.base_filename}{ext}"
            if path.exists():
                return self._parse_file(path)
        return None

    def _load_env_specific_file(self) -> dict[str, Any] | None:
        """Load environment-specific config (config.production.json)."""
        config_dir = self._get_config_dir()
        env_name = self.options.environment.value
        for ext in [".json", ".yaml", ".yml"]:
            path = config_dir / f"{self.options.base_filename}.{env_name}{ext}"
            if path.exists():
                return self._parse_file(path)
        return None

    def _load_local_file(self) -> dict[str, Any] | None:
        """Load local config file (config.local.json)."""
        config_dir = self._get_config_dir()
        for ext in [".json", ".yaml", ".yml"]:
            path = config_dir / f"{self.options.base_filename}.local{ext}"
            if path.exists():
                return self._parse_file(path)
        return None

    def _load_env_file(self) -> dict[str, Any] | None:
        """Load .env file and parse into nested dict."""
        if self.options.env_file:
            env_path = Path(self.options.env_file)
        else:
            env_path = self._get_config_dir() / ".env"

        if not env_path.exists():
            return None

        result: dict[str, Any] = {}
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    self._set_nested(result, key.lower().split("__"), value)
        except OSError as e:
            if self.options.strict:
                raise LoaderError(
                    f"Failed to read .env file: {e}",
                    source=str(env_path),
                ) from e

        return result or None

    def _load_env_vars(self) -> dict[str, Any]:
        """Load GRCCLAW_* environment variables into nested dict."""
        result: dict[str, Any] = {}
        prefix = ENV_PREFIX

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Strip prefix and split by __ for nesting
            config_key = key[len(prefix):]
            parts = config_key.split(ENV_DOUBLE_UNDERSCORE)

            # Convert value types
            typed_value = self._convert_env_value(value)

            self._set_nested(result, parts, typed_value)

        return result

    def _parse_file(self, path: Path) -> dict[str, Any]:
        """Parse a configuration file (JSON or YAML)."""
        try:
            if path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                except ImportError as e:
                    raise LoaderError(
                        "PyYAML is required to load YAML config files. Install with: pip install pyyaml",
                        source=str(path),
                    ) from e
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

            if not isinstance(data, dict):
                raise LoaderError(
                    f"Config file must contain a JSON object: {path}",
                    source=str(path),
                )
            return data

        except json.JSONDecodeError as e:
            raise LoaderError(
                f"Invalid JSON in config file {path}: {e}",
                source=str(path),
                details={"line": e.lineno, "column": e.colno},
            ) from e
        except OSError as e:
            raise LoaderError(
                f"Failed to read config file: {e}",
                source=str(path),
            ) from e

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries. Override takes precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # For lists, override replaces entirely
                result[key] = value
            else:
                result[key] = value
        return result

    def _set_nested(self, d: dict[str, Any], parts: list[str], value: Any) -> None:
        """Set a nested value in a dict using a list of key parts."""
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value

    def _convert_env_value(self, value: str) -> Any:
        """Convert an environment variable string to appropriate type."""
        # Boolean
        lower = value.lower()
        if lower in ("true", "yes", "1", "on"):
            return True
        if lower in ("false", "no", "0", "off"):
            return False
        if lower in ("null", "none", ""):
            return None

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # List (comma-separated)
        if "," in value and not value.startswith(("http://", "https://", "/")):
            return [self._convert_env_value(v.strip()) for v in value.split(",")]

        # String
        return value

    def _dict_to_config(self, data: dict[str, Any]) -> Config:
        """Convert a dictionary to a Config instance."""
        from dataclasses import fields as dc_fields

        config = Config()
        config_fields = {f.name: f for f in dc_fields(Config)}

        for key, value in data.items():
            if key not in config_fields:
                if self.options.strict:
                    raise LoaderError(f"Unknown configuration key: {key}")
                continue

            current = getattr(config, key)
            if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
                # Nested dataclass
                nested = self._dict_to_dataclass(type(current), value)
                setattr(config, key, nested)
            else:
                setattr(config, key, value)

        return config

    def _dict_to_dataclass(self, cls: type, data: dict[str, Any]) -> Any:
        """Convert a dict to a dataclass instance."""
        from dataclasses import fields as dc_fields

        field_types = {f.name: f.type for f in dc_fields(cls)}
        kwargs: dict[str, Any] = {}

        for key, value in data.items():
            if key not in field_types:
                continue
            kwargs[key] = value

        return cls(**kwargs)
