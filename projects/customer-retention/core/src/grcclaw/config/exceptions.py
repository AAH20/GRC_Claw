"""
Custom exceptions for the GRC_Claw configuration management system.
"""

from __future__ import annotations

from typing import Any


class ConfigError(Exception):
    """Base exception for all configuration errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ConfigError):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        *,
        errors: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)
        self.errors = errors or []


class LoaderError(ConfigError):
    """Raised when configuration loading fails."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)
        self.source = source


class SecretError(ConfigError):
    """Raised when secret management operations fail."""

    def __init__(
        self,
        message: str,
        *,
        secret_ref: str | None = None,
        backend: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)
        self.secret_ref = secret_ref
        self.backend = backend


class SchemaError(ConfigError):
    """Raised when the configuration schema is invalid or cannot be loaded."""

    def __init__(
        self,
        message: str,
        *,
        schema_path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details=details)
        self.schema_path = schema_path
