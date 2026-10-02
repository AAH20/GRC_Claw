"""
JSON Schema for GRC_Claw configuration validation.

Defines the complete JSON Schema (Draft 2020-12) for validating
configuration files. Each section corresponds to a dataclass in types.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exceptions import SchemaError


CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://grc-claw.io/schemas/config.json",
    "title": "GRC_Claw Configuration",
    "description": "Configuration schema for the GRC_Claw platform",
    "type": "object",
    "required": ["application"],
    "properties": {
        "application": {
            "type": "object",
            "description": "Application-level configuration",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 128},
                "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
                "description": {"type": "string", "maxLength": 512},
                "environment": {
                    "type": "string",
                    "enum": ["development", "staging", "production", "testing"],
                },
                "debug": {"type": "boolean"},
                "timezone": {"type": "string"},
                "instance_id": {"type": "string", "minLength": 1},
                "shutdown_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
            },
            "additionalProperties": False,
        },
        "api": {
            "type": "object",
            "description": "API server configuration",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "prefix": {"type": "string", "pattern": r"^/.*"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "cors_origins": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "cors_allow_credentials": {"type": "boolean"},
                "cors_allow_methods": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "cors_allow_headers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "max_request_size_mb": {"type": "integer", "minimum": 1},
                "request_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
                "max_concurrent_requests": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "security": {
            "type": "object",
            "description": "Security and authentication configuration",
            "properties": {
                "secret_key": {"type": "string", "minLength": 16},
                "jwt_algorithm": {
                    "type": "string",
                    "enum": ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
                },
                "jwt_access_token_expire_minutes": {"type": "integer", "minimum": 1},
                "jwt_refresh_token_expire_days": {"type": "integer", "minimum": 1},
                "jwt_issuer": {"type": "string", "format": "uri"},
                "jwt_audience": {"type": "string", "format": "uri"},
                "oidc_issuer": {"type": "string", "format": "uri"},
                "oidc_audience": {"type": "string", "format": "uri"},
                "oidc_jwks_uri": {"type": "string", "format": "uri"},
                "api_key_header": {"type": "string"},
                "api_key_prefix": {"type": "string"},
                "mtls_enabled": {"type": "boolean"},
                "mtls_ca_cert_path": {"type": "string"},
                "password_hash_algorithm": {"type": "string", "enum": ["bcrypt", "argon2", "scrypt"]},
                "password_hash_rounds": {"type": "integer", "minimum": 4, "maximum": 31},
                "mfa_enabled": {"type": "boolean"},
                "mfa_issuer": {"type": "string"},
                "allowed_hosts": {"type": "array", "items": {"type": "string"}},
                "trusted_proxies": {"type": "array", "items": {"type": "string"}},
                "secure_cookies": {"type": "boolean"},
                "cookie_samesite": {"type": "string", "enum": ["strict", "lax", "none"]},
                "hsts_max_age": {"type": "integer", "minimum": 0},
                "hsts_include_subdomains": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "database": {
            "type": "object",
            "description": "Database configuration",
            "properties": {
                "url": {"type": "string", "minLength": 1},
                "pool_size": {"type": "integer", "minimum": 1},
                "max_overflow": {"type": "integer", "minimum": 0},
                "pool_timeout": {"type": "integer", "minimum": 1},
                "pool_recycle": {"type": "integer", "minimum": 0},
                "echo": {"type": "boolean"},
                "migration_path": {"type": "string"},
                "migration_table": {"type": "string"},
                "statement_timeout_seconds": {"type": "integer", "minimum": 1},
                "connection_retry_attempts": {"type": "integer", "minimum": 0},
                "connection_retry_delay_seconds": {"type": "number", "minimum": 0},
            },
            "additionalProperties": False,
        },
        "redis": {
            "type": "object",
            "description": "Redis configuration",
            "properties": {
                "url": {"type": "string"},
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "db": {"type": "integer", "minimum": 0, "maximum": 15},
                "password": {"type": "string"},
                "ssl": {"type": "boolean"},
                "ssl_cert_reqs": {"type": "string", "enum": ["none", "optional", "required"]},
                "key_prefix": {"type": "string"},
                "max_connections": {"type": "integer", "minimum": 1},
                "socket_timeout": {"type": "number", "exclusiveMinimum": 0},
                "socket_connect_timeout": {"type": "number", "exclusiveMinimum": 0},
                "retry_on_timeout": {"type": "boolean"},
                "health_check_interval": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "rate_limiting": {
            "type": "object",
            "description": "Rate limiting configuration",
            "properties": {
                "default_rps": {"type": "integer", "minimum": 1},
                "default_burst": {"type": "integer", "minimum": 1},
                "enforcement_rps": {"type": "integer", "minimum": 1},
                "enforcement_burst": {"type": "integer", "minimum": 1},
                "algorithm": {
                    "type": "string",
                    "enum": ["token_bucket", "sliding_window", "leaky_bucket", "fixed_window"],
                },
                "daily_limit": {"type": "integer", "minimum": 1},
                "key_prefix": {"type": "string"},
                "exclude_paths": {"type": "array", "items": {"type": "string"}},
                "enabled": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "grpc": {
            "type": "object",
            "description": "gRPC server configuration",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "max_workers": {"type": "integer", "minimum": 1},
                "max_concurrent_streams": {"type": "integer", "minimum": 1},
                "tls_enabled": {"type": "boolean"},
                "tls_cert_path": {"type": "string"},
                "tls_key_path": {"type": "string"},
                "reflection_enabled": {"type": "boolean"},
                "health_check_enabled": {"type": "boolean"},
                "max_receive_message_length": {"type": "integer", "minimum": 1},
                "max_send_message_length": {"type": "integer", "minimum": 1},
                "keepalive_time_ms": {"type": "integer", "minimum": 0},
                "keepalive_timeout_ms": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
        "webhooks": {
            "type": "object",
            "description": "Webhook delivery configuration",
            "properties": {
                "max_retries": {"type": "integer", "minimum": 0},
                "retry_delays": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                },
                "timeout_seconds": {"type": "integer", "minimum": 1},
                "timestamp_tolerance": {"type": "integer", "minimum": 0},
                "signing_secret": {"type": "string"},
                "delivery_mode": {
                    "type": "string",
                    "enum": ["at_least_once", "at_most_once", "exactly_once"],
                },
                "max_payload_size_mb": {"type": "integer", "minimum": 1},
                "allowed_content_types": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": False,
        },
        "observability": {
            "type": "object",
            "description": "Observability and monitoring configuration",
            "properties": {
                "log_level": {
                    "type": "string",
                    "enum": ["debug", "info", "warning", "error", "critical"],
                },
                "log_format": {"type": "string", "enum": ["json", "text"]},
                "log_destination": {"type": "string", "enum": ["stdout", "file", "webhook"]},
                "log_file_path": {"type": "string"},
                "log_rotation": {"type": "string", "enum": ["daily", "size", "none"]},
                "log_max_bytes": {"type": "integer", "minimum": 1024},
                "log_backup_count": {"type": "integer", "minimum": 0},
                "otel_service_name": {"type": "string"},
                "otel_exporter_otlp_endpoint": {"type": "string"},
                "otel_exporter_otlp_protocol": {"type": "string", "enum": ["grpc", "http/protobuf"]},
                "otel_sample_rate": {"type": "number", "minimum": 0, "maximum": 1},
                "enable_metrics": {"type": "boolean"},
                "enable_tracing": {"type": "boolean"},
                "enable_profiling": {"type": "boolean"},
                "metrics_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "metrics_path": {"type": "string"},
                "health_check_interval": {"type": "integer", "minimum": 1},
                "tracing_max_attributes": {"type": "integer", "minimum": 1},
                "mask_fields": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "integrations": {
            "type": "object",
            "description": "Integration and connector configuration",
            "properties": {
                "connector_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
                "connector_verify_ssl": {"type": "boolean"},
                "retry_max_retries": {"type": "integer", "minimum": 0},
                "retry_base_delay_seconds": {"type": "number", "minimum": 0},
                "retry_max_delay_seconds": {"type": "number", "exclusiveMinimum": 0},
                "retry_exponential_backoff": {"type": "boolean"},
                "retry_on_status_codes": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 100, "maximum": 599},
                },
                "rate_limit_requests_per_minute": {"type": "integer", "minimum": 1},
                "rate_limit_burst_size": {"type": "integer", "minimum": 1},
                "rate_limit_strategy": {
                    "type": "string",
                    "enum": ["token_bucket", "sliding_window", "fixed_window"],
                },
                "cache_enabled": {"type": "boolean"},
                "cache_ttl_seconds": {"type": "integer", "minimum": 1},
                "cache_max_entries": {"type": "integer", "minimum": 1},
                "cache_key_prefix": {"type": "string"},
                "logging_include_request_body": {"type": "boolean"},
                "logging_include_response_body": {"type": "boolean"},
                "logging_mask_fields": {"type": "array", "items": {"type": "string"}},
                "logging_destination": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "notifications": {
            "type": "object",
            "description": "Notification and alerting configuration",
            "properties": {
                "channels": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "rate_limit_per_minute": {"type": "integer", "minimum": 1},
                            "priority_filter": {"type": "array", "items": {"type": "string"}},
                            "type_filter": {"type": "array", "items": {"type": "string"}},
                            "smtp_host": {"type": "string"},
                            "smtp_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                            "smtp_username": {"type": "string"},
                            "smtp_password": {"type": "string"},
                            "smtp_use_tls": {"type": "boolean"},
                            "smtp_from_address": {"type": "string", "format": "email"},
                            "slack_webhook_url": {"type": "string", "format": "uri"},
                            "slack_bot_token": {"type": "string"},
                            "slack_default_channel": {"type": "string"},
                            "teams_webhook_url": {"type": "string", "format": "uri"},
                            "webhook_url": {"type": "string", "format": "uri"},
                            "webhook_headers": {"type": "object", "additionalProperties": {"type": "string"}},
                            "webhook_auth_type": {"type": "string"},
                            "webhook_auth_config": {"type": "object", "additionalProperties": {"type": "string"}},
                        },
                        "additionalProperties": False,
                    },
                },
                "routing_rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "condition": {"type": "string"},
                            "channels": {"type": "array", "items": {"type": "string"}},
                            "priority": {"type": "string"},
                        },
                        "required": ["name", "channels"],
                        "additionalProperties": False,
                    },
                },
                "template_dir": {"type": "string"},
                "default_locale": {"type": "string"},
                "max_recipients_per_notification": {"type": "integer", "minimum": 1},
                "deduplication_window_seconds": {"type": "integer", "minimum": 0},
                "analytics_enabled": {"type": "boolean"},
                "analytics_retention_days": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "workflows": {
            "type": "object",
            "description": "Workflow engine configuration",
            "properties": {
                "max_concurrent_runs": {"type": "integer", "minimum": 1},
                "default_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
                "step_default_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
                "retry_max_attempts": {"type": "integer", "minimum": 1},
                "retry_backoff_seconds": {"type": "number", "minimum": 0},
                "retry_max_backoff_seconds": {"type": "number", "exclusiveMinimum": 0},
                "retry_backoff_multiplier": {"type": "number", "exclusiveMinimum": 0},
                "retryable_exceptions": {"type": "array", "items": {"type": "string"}},
                "max_workflow_depth": {"type": "integer", "minimum": 1},
                "cleanup_interval_seconds": {"type": "integer", "minimum": 1},
                "retention_days": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "cost": {
            "type": "object",
            "description": "Cost optimization configuration",
            "properties": {
                "currency": {"type": "string", "pattern": r"^[A-Z]{3}$"},
                "budget_alert_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                "anomaly_detection_enabled": {"type": "boolean"},
                "anomaly_detection_sensitivity": {"type": "string", "enum": ["low", "medium", "high"]},
                "anomaly_lookback_days": {"type": "integer", "minimum": 1},
                "forecast_enabled": {"type": "boolean"},
                "forecast_default_method": {
                    "type": "string",
                    "enum": [
                        "linear_regression",
                        "moving_average",
                        "exponential_smoothing",
                        "seasonal_decomposition",
                        "monte_carlo",
                    ],
                },
                "forecast_confidence_interval": {"type": "number", "exclusiveMinimum": 0, "maximum": 1},
                "forecast_horizon_months": {"type": "integer", "minimum": 1},
                "cost_allocation_enabled": {"type": "boolean"},
                "default_allocation_method": {
                    "type": "string",
                    "enum": ["direct", "usage_based", "headcount", "revenue", "equal_split", "weighted"],
                },
                "tco_enabled": {"type": "boolean"},
                "tco_period_months": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
        "quoting": {
            "type": "object",
            "description": "Quoting and pricing configuration",
            "properties": {
                "base_prices": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "minimum": 0},
                },
                "volume_discount_tiers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "integer", "minimum": 1},
                            "max": {"type": "integer", "minimum": 1},
                            "discount_pct": {"type": "number", "minimum": 0, "maximum": 100},
                        },
                        "required": ["min", "discount_pct"],
                        "additionalProperties": False,
                    },
                },
                "deployment_multipliers": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "exclusiveMinimum": 0},
                },
                "support_multipliers": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "exclusiveMinimum": 0},
                },
                "tier_adjustments": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                },
                "default_deployment_model": {
                    "type": "string",
                    "enum": ["cloud_saas", "private_cloud", "on_premises", "hybrid"],
                },
                "default_support_level": {
                    "type": "string",
                    "enum": ["standard", "premium", "enterprise"],
                },
                "default_pricing_tier": {
                    "type": "string",
                    "enum": ["startup", "growth", "enterprise"],
                },
                "quote_validity_days": {"type": "integer", "minimum": 1},
                "quote_currency": {"type": "string", "pattern": r"^[A-Z]{3}$"},
            },
            "additionalProperties": False,
        },
        "billing": {
            "type": "object",
            "description": "Billing and usage tracking configuration",
            "properties": {
                "metering_dimensions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "api_calls",
                            "agent_sessions",
                            "policy_evaluations",
                            "evidence_processed_gb",
                            "framework_mappings",
                            "reports_generated",
                            "storage_gb",
                            "compute_hours",
                            "token_count",
                            "active_users",
                            "custom",
                        ],
                    },
                },
                "pricing_plans": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["free", "starter", "professional", "enterprise", "custom"],
                    },
                },
                "default_pricing_plan": {
                    "type": "string",
                    "enum": ["free", "starter", "professional", "enterprise", "custom"],
                },
                "revenue_recognition_method": {
                    "type": "string",
                    "enum": ["point_in_time", "over_time", "milestone", "usage_based"],
                },
                "billing_cycle": {"type": "string", "enum": ["monthly", "quarterly", "annual"]},
                "invoice_due_days": {"type": "integer", "minimum": 0},
                "payment_retry_attempts": {"type": "integer", "minimum": 0},
                "payment_retry_interval_hours": {"type": "integer", "minimum": 1},
                "usage_aggregation_interval_minutes": {"type": "integer", "minimum": 1},
                "usage_retention_days": {"type": "integer", "minimum": 1},
                "invoice_retention_days": {"type": "integer", "minimum": 1},
                "tax_calculation_enabled": {"type": "boolean"},
                "tax_provider": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


def get_schema() -> dict[str, Any]:
    """Return a copy of the configuration JSON Schema."""
    return json.loads(json.dumps(CONFIG_SCHEMA))


def load_schema_from_file(path: str | Path) -> dict[str, Any]:
    """Load the configuration schema from a JSON file.

    Args:
        path: Path to the schema JSON file.

    Returns:
        The parsed schema dictionary.

    Raises:
        SchemaError: If the file cannot be read or parsed.
    """
    schema_path = Path(path)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise SchemaError(
            f"Schema file not found: {schema_path}",
            schema_path=str(schema_path),
        ) from e
    except json.JSONDecodeError as e:
        raise SchemaError(
            f"Invalid JSON in schema file: {e}",
            schema_path=str(schema_path),
            details={"line": e.lineno, "column": e.colno},
        ) from e


def save_schema_to_file(path: str | Path) -> None:
    """Save the configuration schema to a JSON file.

    Args:
        path: Destination file path.
    """
    schema_path = Path(path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(CONFIG_SCHEMA, f, indent=2)
        f.write("\n")
