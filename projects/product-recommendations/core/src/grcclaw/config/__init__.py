"""
GRC_Claw Configuration Management System

Unified configuration management providing:
- JSON Schema-based configuration validation
- Environment-specific configuration loading with overrides
- Secret management integration (env vars, AWS SM, Vault, Azure KV)
- Configuration documentation generation

Usage:
    from grcclaw.config import ConfigManager

    manager = ConfigManager(environment="production")
    config = manager.load()
    manager.validate(config)
"""

from .defaults import get_default_config
from .docs_generator import ConfigDocsGenerator, generate_config_docs
from .exceptions import (
    ConfigError,
    LoaderError,
    SchemaError,
    SecretError,
    ValidationError,
)
from .loader import ConfigLoader, LoadOptions
from .schema import CONFIG_SCHEMA, get_schema, load_schema_from_file, save_schema_to_file
from .secrets import (
    AWSSecretsManager,
    AzureKeyVaultManager,
    CompositeSecretManager,
    EnvVarSecretManager,
    FileSecretManager,
    HashiCorpVaultManager,
    SecretManager,
    SecretReference,
    create_default_secret_manager,
    find_secret_refs,
)
from .types import (
    ApiConfig,
    ApplicationConfig,
    AuthType,
    BillingConfig,
    Config,
    CostConfig,
    DatabaseConfig,
    DeploymentModel,
    Environment,
    GrpcConfig,
    IntegrationConfig,
    LogLevel,
    NotificationChannel,
    NotificationChannelConfig,
    NotificationConfig,
    ObservabilityConfig,
    PricingTier,
    QuotingConfig,
    RateLimitAlgorithm,
    RateLimitingConfig,
    RedisConfig,
    SecretBackend,
    SecurityConfig,
    SupportLevel,
    WebhookConfig,
    WorkflowConfig,
)
from .validator import ConfigValidator, ValidationIssue, ValidationResult

__version__ = "1.0.0"

__all__ = [
    # Types
    "Config",
    "ApplicationConfig",
    "ApiConfig",
    "SecurityConfig",
    "DatabaseConfig",
    "RedisConfig",
    "RateLimitingConfig",
    "GrpcConfig",
    "WebhookConfig",
    "ObservabilityConfig",
    "IntegrationConfig",
    "NotificationConfig",
    "NotificationChannelConfig",
    "WorkflowConfig",
    "CostConfig",
    "QuotingConfig",
    "BillingConfig",
    "Environment",
    "LogLevel",
    "RateLimitAlgorithm",
    "AuthType",
    "NotificationChannel",
    "DeploymentModel",
    "SupportLevel",
    "PricingTier",
    "SecretBackend",
    # Exceptions
    "ConfigError",
    "ValidationError",
    "LoaderError",
    "SecretError",
    "SchemaError",
    # Validator
    "ConfigValidator",
    "ValidationResult",
    "ValidationIssue",
    # Loader
    "ConfigLoader",
    "LoadOptions",
    # Secrets
    "SecretManager",
    "EnvVarSecretManager",
    "AWSSecretsManager",
    "HashiCorpVaultManager",
    "AzureKeyVaultManager",
    "FileSecretManager",
    "CompositeSecretManager",
    "SecretReference",
    "find_secret_refs",
    "create_default_secret_manager",
    # Docs
    "ConfigDocsGenerator",
    "generate_config_docs",
    # Defaults
    "get_default_config",
    # Schema
    "CONFIG_SCHEMA",
    "get_schema",
    "load_schema_from_file",
    "save_schema_to_file",
]
