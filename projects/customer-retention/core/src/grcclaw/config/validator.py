"""
Configuration validator for GRC_Claw.

Validates configuration dictionaries and Config instances against
the JSON Schema defined in schema.py. Supports custom validation rules
beyond what JSON Schema can express.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .exceptions import ValidationError
from .schema import CONFIG_SCHEMA, get_schema, load_schema_from_file
from .types import Config, Environment


@dataclass
class ValidationIssue:
    """A single validation issue."""

    path: str
    message: str
    severity: str = "error"  # error, warning
    rule: str = ""


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return only error-severity issues."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return only warning-severity issues."""
        return [i for i in self.issues if i.severity == "warning"]

    def raise_for_errors(self) -> None:
        """Raise ValidationError if there are any errors."""
        if self.errors:
            raise ValidationError(
                f"Configuration validation failed with {len(self.errors)} error(s)",
                errors=[
                    {"path": i.path, "message": i.message, "rule": i.rule}
                    for i in self.errors
                ],
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": [{"path": i.path, "message": i.message, "rule": i.rule} for i in self.errors],
            "warnings": [{"path": i.path, "message": i.message, "rule": i.rule} for i in self.warnings],
        }


class ConfigValidator:
    """Validates GRC_Claw configuration against the JSON Schema and custom rules."""

    def __init__(
        self,
        schema: Optional[dict[str, Any]] = None,
        schema_path: Optional[str | Path] = None,
        custom_rules: Optional[list] = None,
    ):
        """Initialize the validator.

        Args:
            schema: JSON Schema dictionary. If None, uses the built-in schema.
            schema_path: Path to a JSON Schema file. Overrides schema if provided.
            custom_rules: List of custom validation callables.
        """
        if schema_path:
            self._schema = load_schema_from_file(schema_path)
        elif schema:
            self._schema = schema
        else:
            self._schema = get_schema()
        self._custom_rules = custom_rules or []
        self._json_schema_validator: Optional[Any] = None

    @property
    def schema(self) -> dict[str, Any]:
        """Return the JSON Schema being used for validation."""
        return self._schema

    def validate(self, config: dict[str, Any] | Config) -> ValidationResult:
        """Validate a configuration.

        Args:
            config: Configuration dictionary or Config instance.

        Returns:
            ValidationResult with any issues found.
        """
        if isinstance(config, Config):
            config_dict = config.to_dict()
        else:
            config_dict = config

        issues: list[ValidationIssue] = []

        # JSON Schema validation
        issues.extend(self._validate_json_schema(config_dict))

        # Custom rule validation
        for rule in self._custom_rules:
            issues.extend(rule(config_dict))

        # Built-in semantic validation
        issues.extend(self._validate_semantics(config_dict))

        errors = [i for i in issues if i.severity == "error"]
        return ValidationResult(valid=len(errors) == 0, issues=issues)

    def validate_or_raise(self, config: dict[str, Any] | Config) -> None:
        """Validate and raise ValidationError on failure."""
        result = self.validate(config)
        result.raise_for_errors()

    def _validate_json_schema(self, config: dict[str, Any]) -> list[ValidationIssue]:
        """Validate against JSON Schema."""
        issues: list[ValidationIssue] = []

        try:
            import jsonschema
        except ImportError:
            # Fallback: basic structural validation without jsonschema
            return self._basic_structural_validation(config)

        try:
            validator_cls = jsonschema.validators.validator_for(self._schema)
            validator_cls.check_schema(self._schema)
            validator = validator_cls(self._schema)
        except Exception as e:
            issues.append(ValidationIssue(
                path="$",
                message=f"Schema error: {e}",
                severity="error",
                rule="schema_validity",
            ))
            return issues

        for error in validator.iter_errors(config):
            path = "$"
            for part in error.absolute_path:
                path += f".{part}" if isinstance(part, str) else f"[{part}]"
            issues.append(ValidationIssue(
                path=path or "$",
                message=error.message,
                severity="error",
                rule=f"json_schema.{error.validator}",
            ))

        return issues

    def _basic_structural_validation(self, config: dict[str, Any]) -> list[ValidationIssue]:
        """Basic structural validation when jsonschema is not available."""
        issues: list[ValidationIssue] = []

        if not isinstance(config, dict):
            issues.append(ValidationIssue(
                path="$",
                message="Configuration must be a dictionary",
                severity="error",
                rule="type",
            ))
            return issues

        # Check required top-level key
        if "application" not in config:
            issues.append(ValidationIssue(
                path="application",
                message="Missing required section: application",
                severity="error",
                rule="required",
            ))

        # Check known sections
        known_sections = set(self._schema.get("properties", {}).keys())
        for key in config:
            if key not in known_sections:
                issues.append(ValidationIssue(
                    path=key,
                    message=f"Unknown configuration section: {key}",
                    severity="warning",
                    rule="additionalProperties",
                ))

        return issues

    def _validate_semantics(self, config: dict[str, Any]) -> list[ValidationIssue]:
        """Validate semantic constraints beyond JSON Schema."""
        issues: list[ValidationIssue] = []

        # Validate retry delays are non-decreasing
        webhooks = config.get("webhooks", {})
        retry_delays = webhooks.get("retry_delays", [])
        if retry_delays:
            for i in range(1, len(retry_delays)):
                if retry_delays[i] < retry_delays[i - 1]:
                    issues.append(ValidationIssue(
                        path=f"webhooks.retry_delays[{i}]",
                        message=f"Retry delay {retry_delays[i]} is less than previous {retry_delays[i-1]}. Delays should be non-decreasing.",
                        severity="warning",
                        rule="webhooks.retry_delays.monotonic",
                    ))

        # Validate retry_max_retries matches retry_delays length
        max_retries = webhooks.get("max_retries", 0)
        if retry_delays and max_retries != len(retry_delays):
            issues.append(ValidationIssue(
                path="webhooks.max_retries",
                message=f"max_retries ({max_retries}) does not match retry_delays length ({len(retry_delays)})",
                severity="warning",
                rule="webhooks.max_retries.consistency",
            ))

        # Validate database pool_size + max_overflow > 0
        db = config.get("database", {})
        pool_size = db.get("pool_size", 0)
        max_overflow = db.get("max_overflow", 0)
        if pool_size + max_overflow <= 0:
            issues.append(ValidationIssue(
                path="database.pool_size",
                message="pool_size + max_overflow must be > 0",
                severity="error",
                rule="database.pool.positive",
            ))

        # Validate rate limiting: burst >= rps
        rl = config.get("rate_limiting", {})
        default_rps = rl.get("default_rps", 0)
        default_burst = rl.get("default_burst", 0)
        if default_burst < default_rps:
            issues.append(ValidationIssue(
                path="rate_limiting.default_burst",
                message=f"default_burst ({default_burst}) should be >= default_rps ({default_rps})",
                severity="warning",
                rule="rate_limiting.burst_gte_rps",
            ))

        # Validate gRPC keepalive timeout < time
        grpc = config.get("grpc", {})
        ka_time = grpc.get("keepalive_time_ms", 0)
        ka_timeout = grpc.get("keepalive_timeout_ms", 0)
        if ka_time > 0 and ka_timeout > ka_time:
            issues.append(ValidationIssue(
                path="grpc.keepalive_timeout_ms",
                message=f"keepalive_timeout_ms ({ka_timeout}) should be <= keepalive_time_ms ({ka_time})",
                severity="warning",
                rule="grpc.keepalive.consistency",
            ))

        # Validate production security
        app = config.get("application", {})
        env = app.get("environment", "development")
        security = config.get("security", {})
        if env == "production":
            secret_key = security.get("secret_key", "")
            if secret_key == "change-me-in-production" or len(secret_key) < 32:
                issues.append(ValidationIssue(
                    path="security.secret_key",
                    message="Production environment requires a strong secret_key (>= 32 chars)",
                    severity="error",
                    rule="security.production.secret_key",
                ))
            if not security.get("secure_cookies", False):
                issues.append(ValidationIssue(
                    path="security.secure_cookies",
                    message="Production environment should have secure_cookies enabled",
                    severity="warning",
                    rule="security.production.secure_cookies",
                ))
            if security.get("debug", False):
                issues.append(ValidationIssue(
                    path="application.debug",
                    message="Debug mode should not be enabled in production",
                    severity="error",
                    rule="application.production.debug",
                ))

        # Validate notification channel references
        notifications = config.get("notifications", {})
        channels = notifications.get("channels", {})
        routing_rules = notifications.get("routing_rules", [])
        for rule in routing_rules:
            for ch in rule.get("channels", []):
                if ch not in channels:
                    issues.append(ValidationIssue(
                        path=f"notifications.routing_rules.{rule.get('name', '')}",
                        message=f"Routing rule references unknown channel: {ch}",
                        severity="error",
                        rule="notifications.routing.unknown_channel",
                    ))

        # Validate quoting tiers are sorted
        quoting = config.get("quoting", {})
        tiers = quoting.get("volume_discount_tiers", [])
        prev_max = 0
        for i, tier in enumerate(tiers):
            tier_min = tier.get("min", 0)
            if i > 0 and tier_min <= prev_max:
                issues.append(ValidationIssue(
                    path=f"quoting.volume_discount_tiers[{i}].min",
                    message=f"Tier min ({tier_min}) should be > previous tier max ({prev_max})",
                    severity="warning",
                    rule="quoting.tiers.sorted",
                ))
            prev_max = tier.get("max", prev_max)

        return issues
