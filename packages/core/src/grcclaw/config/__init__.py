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
    WorkflowConfig,
    CostConfig,
    QuotingConfig,
    BillingConfig,
    Environment,
    LogLevel,
)
from .exceptions import (
    ConfigError,
    ValidationError,
    LoaderError,
    SecretError,
    SchemaError,
)
from .validator import ConfigValidator, ValidationResult
from .loader import ConfigLoader, LoadOptions
from .secrets import (
    SecretManager,
    EnvVarSecretManager,
    AWSSecretsManager,
    HashiCorpVaultManager,
    AzureKeyVaultManager,
    FileSecretManager,
    SecretReference,
)
from .docs_generator import ConfigDocsGenerator
from .defaults import get_default_config

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
    "WorkflowConfig",
    "CostConfig",
    "QuotingConfig",
    "BillingConfig",
    "Environment",
    "LogLevel",
    # Exceptions
    "ConfigError",
    "ValidationError",
    "LoaderError",
    "SecretError",
    "SchemaError",
    # Validator
    "ConfigValidator",
    "ValidationResult",
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
    "SecretReference",
    # Docs
    "ConfigDocsGenerator",
    # Defaults
    "get_default_config",
]
