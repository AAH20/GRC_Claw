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

from .types import (
    Config,
    ApplicationConfig,
    ApiConfig,
    SecurityConfig,
    DatabaseConfig,
    RedisConfig,
    RateLimitingConfig,
    GrpcConfig,
    WebhookConfig,
    ObservabilityConfig,
    IntegrationConfig,
    NotificationConfig,
    NotificationChannelConfig,
    WorkflowConfig,
    CostConfig,
    QuotingConfig,
    BillingConfig,
    Environment,
    LogLevel,
    RateLimitAlgorithm,
    AuthType,
    NotificationChannel,
    DeploymentModel,
    SupportLevel,
    PricingTier,
    SecretBackend,
)
from .exceptions import (
    ConfigError,
    ValidationError,
    LoaderError,
    SecretError,
    SchemaError,
)
from .validator import ConfigValidator, ValidationResult, ValidationIssue
from .loader import ConfigLoader, LoadOptions
from .secrets import (
    SecretManager,
    EnvVarSecretManager,
    AWSSecretsManager,
    HashiCorpVaultManager,
    AzureKeyVaultManager,
    FileSecretManager,
    CompositeSecretManager,
    SecretReference,
    find_secret_refs,
    create_default_secret_manager,
)
from .docs_generator import ConfigDocsGenerator, generate_config_docs
from .defaults import get_default_config
from .schema import CONFIG_SCHEMA, get_schema, load_schema_from_file, save_schema_to_file

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
