"""
Default configuration values for GRC_Claw.

Provides factory functions for creating Config instances with
environment-specific defaults.
"""

from __future__ import annotations

from .types import (
    Config,
    Environment,
)


def get_default_config(environment: Environment | str = Environment.DEVELOPMENT) -> Config:
    """Create a Config instance with environment-specific defaults.

    Args:
        environment: Target environment. Defaults to development.

    Returns:
        Config instance with appropriate defaults.
    """
    if isinstance(environment, str):
        environment = Environment(environment)

    config = Config()

    # Apply environment-specific overrides
    if environment == Environment.DEVELOPMENT:
        _apply_development_defaults(config)
    elif environment == Environment.STAGING:
        _apply_staging_defaults(config)
    elif environment == Environment.PRODUCTION:
        _apply_production_defaults(config)
    elif environment == Environment.TESTING:
        _apply_testing_defaults(config)

    return config


def _apply_development_defaults(config: Config) -> None:
    """Apply development environment defaults."""
    config.application.environment = Environment.DEVELOPMENT
    config.application.debug = True
    config.api.cors_origins = ["*"]
    config.api.cors_allow_credentials = True
    config.security.secret_key = "dev-secret-key-not-for-production-use-only"
    config.security.secure_cookies = False
    config.security.allowed_hosts = ["*"]
    config.database.echo = True
    config.database.pool_size = 5
    config.database.max_overflow = 10
    config.redis.host = "localhost"
    config.redis.port = 6379
    config.rate_limiting.enabled = True
    config.rate_limiting.default_rps = 1000
    config.rate_limiting.default_burst = 2000
    config.grpc.reflection_enabled = True
    config.observability.log_level = "debug"
    config.observability.log_format = "text"
    config.observability.enable_tracing = True
    config.observability.otel_sample_rate = 1.0
    config.integrations.connector_verify_ssl = False
    config.integrations.logging_include_request_body = True
    config.integrations.logging_include_response_body = True
    config.workflows.max_concurrent_runs = 5
    config.cost.anomaly_detection_enabled = False
    config.cost.forecast_enabled = False


def _apply_staging_defaults(config: Config) -> None:
    """Apply staging environment defaults."""
    config.application.environment = Environment.STAGING
    config.application.debug = False
    config.api.cors_origins = ["https://staging.grc-claw.io"]
    config.api.cors_allow_credentials = True
    config.security.secure_cookies = True
    config.security.allowed_hosts = ["staging.grc-claw.io", "*.staging.grc-claw.io"]
    config.database.echo = False
    config.database.pool_size = 10
    config.database.max_overflow = 20
    config.redis.host = "staging-redis.grc-claw.io"
    config.rate_limiting.enabled = True
    config.rate_limiting.default_rps = 500
    config.rate_limiting.default_burst = 1000
    config.grpc.reflection_enabled = True
    config.observability.log_level = "info"
    config.observability.log_format = "json"
    config.observability.enable_tracing = True
    config.observability.otel_sample_rate = 0.5
    config.integrations.connector_verify_ssl = True
    config.workflows.max_concurrent_runs = 10
    config.cost.anomaly_detection_enabled = True
    config.cost.forecast_enabled = True


def _apply_production_defaults(config: Config) -> None:
    """Apply production environment defaults."""
    config.application.environment = Environment.PRODUCTION
    config.application.debug = False
    config.api.cors_origins = ["https://grc-claw.io", "https://app.grc-claw.io"]
    config.api.cors_allow_credentials = True
    config.security.secure_cookies = True
    config.security.allowed_hosts = ["grc-claw.io", "*.grc-claw.io"]
    config.security.mtls_enabled = True
    config.security.mfa_enabled = True
    config.database.echo = False
    config.database.pool_size = 20
    config.database.max_overflow = 40
    config.database.statement_timeout_seconds = 60
    config.redis.ssl = True
    config.redis.max_connections = 100
    config.rate_limiting.enabled = True
    config.rate_limiting.default_rps = 100
    config.rate_limiting.default_burst = 200
    config.grpc.tls_enabled = True
    config.grpc.reflection_enabled = False
    config.observability.log_level = "info"
    config.observability.log_format = "json"
    config.observability.enable_tracing = True
    config.observability.otel_sample_rate = 0.1
    config.observability.enable_profiling = False
    config.integrations.connector_verify_ssl = True
    config.integrations.logging_include_request_body = False
    config.integrations.logging_include_response_body = False
    config.workflows.max_concurrent_runs = 50
    config.workflows.retention_days = 365
    config.cost.anomaly_detection_enabled = True
    config.cost.forecast_enabled = True
    config.billing.tax_calculation_enabled = True


def _apply_testing_defaults(config: Config) -> None:
    """Apply testing environment defaults."""
    config.application.environment = Environment.TESTING
    config.application.debug = True
    config.api.cors_origins = ["*"]
    config.security.secret_key = "test-secret-key"
    config.security.secure_cookies = False
    config.security.allowed_hosts = ["*"]
    config.database.echo = False
    config.database.pool_size = 2
    config.database.max_overflow = 5
    config.redis.host = "localhost"
    config.redis.db = 15  # Use separate DB for tests
    config.rate_limiting.enabled = False
    config.grpc.reflection_enabled = True
    config.observability.log_level = "error"
    config.observability.log_format = "text"
    config.observability.enable_tracing = False
    config.observability.otel_sample_rate = 0.0
    config.integrations.connector_verify_ssl = False
    config.workflows.max_concurrent_runs = 1
    config.workflows.retention_days = 1
    config.cost.anomaly_detection_enabled = False
    config.cost.forecast_enabled = False
