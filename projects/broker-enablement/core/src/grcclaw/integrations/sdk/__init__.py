"""
Connector SDK — Base classes and utilities for building GRC_Claw connectors.
"""

from .base import BaseConnector, ConnectorCapability, ConnectorStatus
from .config import ConnectorConfig
from .auth import AuthStrategy, APIKeyAuth, OAuth2Auth, BasicAuth, BearerAuth
from .exceptions import (
    ConnectorError,
    AuthenticationError,
    ConnectionError,
    TimeoutError,
    RateLimitError,
    ValidationError,
)
from .registry import ConnectorRegistry
from .types import ConnectorMetadata, RequestContext, ResponseContext

__all__ = [
    "BaseConnector",
    "ConnectorCapability",
    "ConnectorStatus",
    "ConnectorConfig",
    "AuthStrategy",
    "APIKeyAuth",
    "OAuth2Auth",
    "BasicAuth",
    "BearerAuth",
    "ConnectorError",
    "AuthenticationError",
    "ConnectionError",
    "TimeoutError",
    "RateLimitError",
    "ValidationError",
    "ConnectorRegistry",
    "ConnectorMetadata",
    "RequestContext",
    "ResponseContext",
]
