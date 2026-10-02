"""Configuration management for the GRC Unified SDK.

This module provides a layered configuration system that resolves settings
from (in order of precedence):

1. Explicit keyword arguments passed to :class:`GRCConfig`.
2. Environment variables prefixed with ``GRC_``.
3. A JSON or TOML configuration file.
4. Sensible defaults.

The resolved configuration is immutable once constructed and can be
accessed as attributes or exported as a dictionary.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENV_PREFIX = "GRC_"
DEFAULT_CONFIG_FILENAMES = ("grc_config.json", "grc_config.toml", ".grc.json")
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 1.0
DEFAULT_PAGE_SIZE = 100
DEFAULT_CACHE_TTL = 300.0
DEFAULT_LOG_LEVEL = "INFO"


# ---------------------------------------------------------------------------
# Pydantic settings model
# ---------------------------------------------------------------------------


class GRCConfig(BaseModel):
    """Immutable configuration for the GRC Unified SDK.

    All fields are optional; omitted fields fall back to environment
    variables or defaults.  Instantiate directly or use
    :func:`load_config` for layered resolution.

    Attributes:
        api_key: Default API key for GRC project authentication.
        api_base_url: Base URL for the GRC API gateway.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retries for transient failures.
        retry_backoff: Base backoff multiplier (exponential).
        page_size: Default page size for paginated list operations.
        cache_ttl: Time-to-live for cached responses, in seconds.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        verify_ssl: Whether to verify TLS certificates.
        user_agent: User-Agent header value.
        default_project_id: Project ID to use when none is specified.
        extra_headers: Additional headers sent with every request.
        config_path: Path to the configuration file that was loaded.
    """

    api_key: str | None = None
    api_base_url: str = "https://api.grc.local"
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_backoff: float = DEFAULT_RETRY_BACKOFF
    page_size: int = DEFAULT_PAGE_SIZE
    cache_ttl: float = DEFAULT_CACHE_TTL
    log_level: str = DEFAULT_LOG_LEVEL
    verify_ssl: bool = True
    user_agent: str = "grc-unified-sdk/1.0"
    default_project_id: str | None = None
    extra_headers: dict[str, str] = Field(default_factory=dict)
    config_path: Path | None = None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("timeout")
    @classmethod
    def _validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ConfigurationError("timeout must be a positive number")
        return v

    @field_validator("max_retries")
    @classmethod
    def _validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ConfigurationError("max_retries must be non-negative")
        return v

    @field_validator("retry_backoff")
    @classmethod
    def _validate_retry_backoff(cls, v: float) -> float:
        if v < 0:
            raise ConfigurationError("retry_backoff must be non-negative")
        return v

    @field_validator("page_size")
    @classmethod
    def _validate_page_size(cls, v: int) -> int:
        if v <= 0:
            raise ConfigurationError("page_size must be a positive integer")
        return v

    @field_validator("cache_ttl")
    @classmethod
    def _validate_cache_ttl(cls, v: float) -> float:
        if v < 0:
            raise ConfigurationError("cache_ttl must be non-negative")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ConfigurationError(
                f"log_level must be one of {sorted(allowed)}, got {v!r}"
            )
        return upper

    @field_validator("api_base_url")
    @classmethod
    def _validate_api_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"api_base_url must start with http:// or https://, got {v!r}"
            )
        return v.rstrip("/")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def to_dict(self, *, include_secrets: bool = False) -> dict[str, Any]:
        """Return the configuration as a plain dictionary.

        Args:
            include_secrets: If ``False`` (default), the ``api_key`` field
                is redacted to ``"***"``.
        """
        data = self.model_dump(mode="json")
        if not include_secrets and self.api_key is not None:
            data["api_key"] = "***"
        return data

    def with_overrides(self, **kwargs: Any) -> GRCConfig:
        """Return a new config with the given overrides applied.

        The original config is not modified.
        """
        return self.model_copy(update=kwargs)


# ---------------------------------------------------------------------------
# Layered loading
# ---------------------------------------------------------------------------


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base* and return the result."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_from_file(path: Path) -> dict[str, Any]:
    """Load configuration data from a JSON or TOML file."""
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")

    if path.suffix == ".toml":
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError as exc:
                raise ConfigurationError(
                    f"TOML config file {path} requires tomli on Python < 3.11"
                ) from exc
        try:
            return tomllib.loads(text)
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to parse TOML config file {path}: {exc}"
            ) from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Failed to parse JSON config file {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Config file {path} must contain a JSON object at the top level"
        )
    return data


def _load_from_env() -> dict[str, Any]:
    """Load configuration from ``GRC_``-prefixed environment variables."""
    result: dict[str, Any] = {}
    prefix = ENV_PREFIX

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        # Strip prefix and convert to lowercase for field matching
        field_name = key[len(prefix) :].lower()
        # Support nested keys via double underscore: GRC_EXTRA__X
        parts = field_name.split("__")
        cursor = result
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value

    return result


def _find_config_file(
    explicit_path: str | Path | None = None,
    search_dirs: list[str | Path] | None = None,
) -> Path | None:
    """Locate a configuration file.

    Resolution order:
    1. *explicit_path* if provided.
    2. Each directory in *search_dirs* (default: current directory and
       the user's home directory), checking each filename in
       ``DEFAULT_CONFIG_FILENAMES``.
    """
    if explicit_path is not None:
        path = Path(explicit_path).expanduser()
        if path.exists():
            return path
        return None

    dirs: list[Path] = []
    if search_dirs:
        dirs.extend(Path(d).expanduser() for d in search_dirs)
    else:
        dirs.append(Path.cwd())
        dirs.append(Path.home())

    for directory in dirs:
        for filename in DEFAULT_CONFIG_FILENAMES:
            candidate = directory / filename
            if candidate.exists():
                return candidate
    return None


def load_config(
    *,
    config_path: str | Path | None = None,
    search_dirs: list[str | Path] | None = None,
    env_prefix: str = ENV_PREFIX,
    **overrides: Any,
) -> GRCConfig:
    """Load and resolve configuration from all supported sources.

    Precedence (highest first):
    1. Keyword *overrides*.
    2. Environment variables with the given *env_prefix*.
    3. Configuration file found via *config_path* or *search_dirs*.
    4. Pydantic field defaults.

    Args:
        config_path: Explicit path to a JSON or TOML config file.
        search_dirs: Directories to search for a config file.
        env_prefix: Environment variable prefix (default ``GRC_``).
        **overrides: Direct field overrides that take highest precedence.

    Returns:
        A fully resolved :class:`GRCConfig` instance.

    Raises:
        ConfigurationError: If a config file exists but cannot be parsed,
            or if resolved values fail validation.
    """
    global ENV_PREFIX
    original_prefix = ENV_PREFIX
    ENV_PREFIX = env_prefix

    try:
        # Layer 1: file
        file_data: dict[str, Any] = {}
        resolved_path = _find_config_file(config_path, search_dirs)
        if resolved_path is not None:
            file_data = _load_from_file(resolved_path)

        # Layer 2: environment
        env_data = _load_from_env()

        # Layer 3: explicit overrides
        # Merge: file < env < overrides
        merged = _deep_merge(file_data, env_data)
        merged = _deep_merge(merged, overrides)

        # Track which file was loaded
        if resolved_path is not None:
            merged.setdefault("config_path", resolved_path)

        return GRCConfig(**merged)
    except ConfigurationError:
        raise
    except Exception as exc:
        raise ConfigurationError(f"Failed to load configuration: {exc}") from exc
    finally:
        ENV_PREFIX = original_prefix


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_config: GRCConfig | None = None


def get_config() -> GRCConfig:
    """Return the default configuration, loading it on first access.

    If no configuration has been set via :func:`set_config`, this calls
    :func:`load_config` with default arguments.
    """
    global _default_config
    if _default_config is None:
        _default_config = load_config()
    return _default_config


def set_config(config: GRCConfig) -> None:
    """Set the module-level default configuration.

    Args:
        config: The configuration to use as the default.
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """Clear the module-level default configuration.

    The next call to :func:`get_config` will reload from scratch.
    """
    global _default_config
    _default_config = None
