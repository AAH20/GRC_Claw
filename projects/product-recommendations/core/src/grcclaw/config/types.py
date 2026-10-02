"""
Type definitions for the GRC_Claw configuration management system.

Defines dataclasses for each configuration section, enums for
environment and log levels, and the top-level Config container.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ─── Enums ───────────────────────────────────────────────────────────────────


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithm."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


class AuthType(str, Enum):
    """Authentication type for connectors."""

    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    MTLS = "mtls"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"


class DeploymentModel(str, Enum):
    """Deployment model for quoting."""

    CLOUD_SAAS = "cloud_saas"
    PRIVATE_CLOUD = "private_cloud"
    ON_PREMISES = "on_premises"
    HYBRID = "hybrid"


class SupportLevel(str, Enum):
    """Support level for quoting."""

    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PricingTier(str, Enum):
    """Pricing tier for quoting."""

    STARTUP = "startup"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class SecretBackend(str, Enum):
    """Supported secret management backends."""

    ENV_VAR = "env_var"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    HASHICORP_VAULT = "hashicorp_vault"
    AZURE_KEY_VAULT = "azure_key_vault"
    FILE = "file"
    DOCKER_SECRET = "docker_secret"


# ─── Configuration Dataclasses ───────────────────────────────────────────────


@dataclass
class ApplicationConfig:
    """Application-level configuration."""

    name: str = "GRC_Claw"
    version: str = "1.0.0"
    description: str = "Governance, Risk, and Compliance platform for agentic AI"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    timezone: str = "UTC"
    instance_id: Optional[str] = None
    shutdown_timeout_seconds: float = 30.0


@dataclass
class ApiConfig:
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    prefix: str = "/v1.0"
    title: str = "GRC_Claw API"
    description: str = "Governance, Risk, and Compliance platform for agentic AI"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = field(default_factory=lambda: ["*"])
    max_request_size_mb: int = 50
    request_timeout_seconds: float = 30.0
    max_concurrent_requests: int = 1000


@dataclass
class SecurityConfig:
    """Security and authentication configuration."""

    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    jwt_issuer: str = "https://auth.grc-claw.io"
    jwt_audience: str = "https://api.grc-claw.io"
    oidc_issuer: str = "https://auth.grc-claw.io"
    oidc_audience: str = "https://api.grc-claw.io"
    oidc_jwks_uri: Optional[str] = None
    api_key_header: str = "Authorization"
    api_key_prefix: str = "grc_"
    mtls_enabled: bool = False
    mtls_ca_cert_path: Optional[str] = None
    password_hash_algorithm: str = "bcrypt"
    password_hash_rounds: int = 12
    mfa_enabled: bool = False
    mfa_issuer: str = "GRC_Claw"
    allowed_hosts: list[str] = field(default_factory=lambda: ["*"])
    trusted_proxies: list[str] = field(default_factory=list)
    secure_cookies: bool = True
    cookie_samesite: str = "lax"
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "postgresql+asyncpg://grc:grc@localhost:5432/grc_claw"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    migration_path: str = "migrations"
    migration_table: str = "alembic_version"
    statement_timeout_seconds: int = 30
    connection_retry_attempts: int = 3
    connection_retry_delay_seconds: float = 1.0


@dataclass
class RedisConfig:
    """Redis configuration."""

    url: str = "redis://localhost:6379/0"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    ssl_cert_reqs: str = "required"
    key_prefix: str = "grcclaw"
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class RateLimitingConfig:
    """Rate limiting configuration."""

    default_rps: int = 100
    default_burst: int = 200
    enforcement_rps: int = 10000
    enforcement_burst: int = 2000
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    daily_limit: Optional[int] = None
    key_prefix: str = "ratelimit"
    exclude_paths: list[str] = field(default_factory=lambda: ["/health", "/metrics"])
    enabled: bool = True


@dataclass
class GrpcConfig:
    """gRPC server configuration."""

    host: str = "0.0.0.0"
    port: int = 50051
    max_workers: int = 100
    max_concurrent_streams: int = 1000
    tls_enabled: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    reflection_enabled: bool = True
    health_check_enabled: bool = True
    max_receive_message_length: int = 4194304
    max_send_message_length: int = 4194304
    keepalive_time_ms: int = 30000
    keepalive_timeout_ms: int = 5000


@dataclass
class WebhookConfig:
    """Webhook delivery configuration."""

    max_retries: int = 6
    retry_delays: list[int] = field(
        default_factory=lambda: [0, 60, 300, 1800, 7200, 28800]
    )
    timeout_seconds: int = 10
    timestamp_tolerance: int = 300
    signing_secret: Optional[str] = None
    delivery_mode: str = "at_least_once"  # at_least_once, at_most_once, exactly_once
    max_payload_size_mb: int = 10
    allowed_content_types: list[str] = field(
        default_factory=lambda: ["application/json"]
    )


@dataclass
class ObservabilityConfig:
    """Observability and monitoring configuration."""

    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"  # json, text
    log_destination: str = "stdout"  # stdout, file, webhook
    log_file_path: Optional[str] = None
    log_rotation: str = "daily"  # daily, size, none
    log_max_bytes: int = 104857600  # 100MB
    log_backup_count: int = 7
    otel_service_name: str = "grc-claw"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_protocol: str = "grpc"  # grpc, http/protobuf
    otel_sample_rate: float = 1.0
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_profiling: bool = False
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    health_check_interval: int = 30
    tracing_max_attributes: int = 128
    mask_fields: list[str] = field(
        default_factory=lambda: ["password", "token", "api_key", "secret", "authorization"]
    )


@dataclass
class IntegrationConfig:
    """Integration and connector configuration."""

    connector_timeout_seconds: float = 30.0
    connector_verify_ssl: bool = True
    retry_max_retries: int = 3
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 60.0
    retry_exponential_backoff: bool = True
    retry_on_status_codes: list[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    rate_limit_strategy: str = "token_bucket"
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300
    cache_max_entries: int = 1000
    cache_key_prefix: str = "grcclaw"
    logging_include_request_body: bool = False
    logging_include_response_body: bool = False
    logging_mask_fields: list[str] = field(
        default_factory=lambda: ["password", "token", "api_key", "secret"]
    )
    logging_destination: str = "stdout"


@dataclass
class NotificationChannelConfig:
    """Configuration for a single notification channel."""

    enabled: bool = False
    rate_limit_per_minute: int = 60
    priority_filter: list[str] = field(default_factory=list)
    type_filter: list[str] = field(default_factory=list)
    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_from_address: Optional[str] = None
    # Slack
    slack_webhook_url: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_default_channel: Optional[str] = None
    # Teams
    teams_webhook_url: Optional[str] = None
    # Webhook
    webhook_url: Optional[str] = None
    webhook_headers: dict[str, str] = field(default_factory=dict)
    webhook_auth_type: str = "none"
    webhook_auth_config: dict[str, str] = field(default_factory=dict)


@dataclass
class NotificationConfig:
    """Notification and alerting configuration."""

    channels: dict[str, NotificationChannelConfig] = field(default_factory=dict)
    routing_rules: list[dict[str, Any]] = field(default_factory=list)
    template_dir: str = "templates/notifications"
    default_locale: str = "en"
    max_recipients_per_notification: int = 100
    deduplication_window_seconds: int = 300
    analytics_enabled: bool = True
    analytics_retention_days: int = 90


@dataclass
class WorkflowConfig:
    """Workflow engine configuration."""

    max_concurrent_runs: int = 1
    default_timeout_seconds: float = 3600.0
    step_default_timeout_seconds: float = 300.0
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 1.0
    retry_max_backoff_seconds: float = 300.0
    retry_backoff_multiplier: float = 2.0
    retryable_exceptions: list[str] = field(
        default_factory=lambda: ["TimeoutError", "ConnectionError"]
    )
    max_workflow_depth: int = 10
    cleanup_interval_seconds: int = 3600
    retention_days: int = 90


@dataclass
class CostConfig:
    """Cost optimization configuration."""

    currency: str = "USD"
    budget_alert_threshold: float = 0.8
    anomaly_detection_enabled: bool = True
    anomaly_detection_sensitivity: str = "medium"  # low, medium, high
    anomaly_lookback_days: int = 30
    forecast_enabled: bool = True
    forecast_default_method: str = "linear_regression"
    forecast_confidence_interval: float = 0.95
    forecast_horizon_months: int = 12
    cost_allocation_enabled: bool = True
    default_allocation_method: str = "usage_based"
    tco_enabled: bool = True
    tco_period_months: int = 12


@dataclass
class QuotingConfig:
    """Quoting and pricing configuration."""

    base_prices: dict[str, float] = field(
        default_factory=lambda: {
            "agent_base": 12000,
            "model_base": 6000,
            "policy_base": 240,
            "evidence_base": 0.50,
            "framework_base": 3600,
        }
    )
    volume_discount_tiers: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"min": 1, "max": 10, "discount_pct": 0},
            {"min": 11, "max": 50, "discount_pct": 5},
            {"min": 51, "max": 200, "discount_pct": 10},
            {"min": 201, "max": 500, "discount_pct": 15},
            {"min": 501, "max": 1000, "discount_pct": 20},
            {"min": 1001, "max": None, "discount_pct": 25},
        ]
    )
    deployment_multipliers: dict[str, float] = field(
        default_factory=lambda: {
            "cloud_saas": 1.0,
            "private_cloud": 1.35,
            "on_premises": 1.60,
            "hybrid": 1.20,
        }
    )
    support_multipliers: dict[str, float] = field(
        default_factory=lambda: {
            "standard": 1.0,
            "premium": 1.25,
            "enterprise": 1.50,
        }
    )
    tier_adjustments: dict[str, float] = field(
        default_factory=lambda: {
            "startup": -0.10,
            "growth": 0.0,
            "enterprise": 0.15,
        }
    )
    default_deployment_model: DeploymentModel = DeploymentModel.CLOUD_SAAS
    default_support_level: SupportLevel = SupportLevel.STANDARD
    default_pricing_tier: PricingTier = PricingTier.GROWTH
    quote_validity_days: int = 30
    quote_currency: str = "USD"


@dataclass
class BillingConfig:
    """Billing and usage tracking configuration."""

    metering_dimensions: list[str] = field(
        default_factory=lambda: [
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
        ]
    )
    pricing_plans: list[str] = field(
        default_factory=lambda: ["free", "starter", "professional", "enterprise", "custom"]
    )
    default_pricing_plan: str = "starter"
    revenue_recognition_method: str = "over_time"
    billing_cycle: str = "monthly"  # monthly, quarterly, annual
    invoice_due_days: int = 30
    payment_retry_attempts: int = 3
    payment_retry_interval_hours: int = 24
    usage_aggregation_interval_minutes: int = 15
    usage_retention_days: int = 365
    invoice_retention_days: int = 2555  # 7 years
    tax_calculation_enabled: bool = False
    tax_provider: Optional[str] = None


# ─── Top-Level Config Container ──────────────────────────────────────────────


@dataclass
class Config:
    """Top-level configuration container."""

    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)
    grpc: GrpcConfig = field(default_factory=GrpcConfig)
    webhooks: WebhookConfig = field(default_factory=WebhookConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    workflows: WorkflowConfig = field(default_factory=WorkflowConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    quoting: QuotingConfig = field(default_factory=QuotingConfig)
    billing: BillingConfig = field(default_factory=BillingConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entire config to a plain dictionary."""
        from dataclasses import asdict

        return asdict(self)

    def to_masked_dict(self) -> dict[str, Any]:
        """Convert to dict with sensitive fields masked."""
        from dataclasses import asdict

        data = asdict(self)
        mask_fields = self.observability.mask_fields

        def _mask(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    k: ("***MASKED***" if k.lower() in mask_fields else _mask(v))
                    for k, v in obj.items()
                }
            if isinstance(obj, list):
                return [_mask(item) for item in obj]
            return obj

        return _mask(data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Get a config value by dotted key path (e.g., 'database.pool_size')."""
        parts = dotted_key.split(".")
        obj: Any = self
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default
            if obj is None:
                return default
        return obj

    def set(self, dotted_key: str, value: Any) -> None:
        """Set a config value by dotted key path."""
        parts = dotted_key.split(".")
        obj: Any = self
        for part in parts[:-1]:
            if isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            elif hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise AttributeError(f"Cannot set '{dotted_key}': '{part}' not found")
        last = parts[-1]
        if isinstance(obj, dict):
            obj[last] = value
        elif hasattr(obj, last):
            setattr(obj, last, value)
        else:
            raise AttributeError(f"Cannot set '{dotted_key}': '{last}' not found")
