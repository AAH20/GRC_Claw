"""
Connector configuration models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class RetryConfig:
    """Retry policy configuration."""

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_backoff: bool = True
    retry_on_status_codes: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    retry_on_exceptions: list[str] = field(default_factory=lambda: ["ConnectionError", "TimeoutError"])


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    burst_size: int = 10
    strategy: str = "token_bucket"  # token_bucket, sliding_window, fixed_window


@dataclass
class CacheConfig:
    """Caching configuration."""

    enabled: bool = False
    ttl_seconds: int = 300
    max_entries: int = 1000
    key_prefix: str = "grcclaw"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: LogLevel = LogLevel.INFO
    include_request_body: bool = False
    include_response_body: bool = False
    mask_fields: list[str] = field(default_factory=lambda: ["password", "token", "api_key", "secret"])
    destination: str = "stdout"  # stdout, file, webhook


@dataclass
class ConnectorConfig:
    """Complete connector configuration."""

    name: str
    base_url: str = ""
    auth_type: str = "none"  # none, api_key, oauth2, basic, bearer
    auth_config: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    verify_ssl: bool = True
    proxy_url: Optional[str] = None
    retry: RetryConfig = field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    custom: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Connector name is required")
        if self.base_url and not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
