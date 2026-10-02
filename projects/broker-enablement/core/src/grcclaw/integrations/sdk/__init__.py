"""
Connector SDK — Base classes and utilities for building GRC_Claw connectors.
"""

from .auth import APIKeyAuth, AuthStrategy, BasicAuth, BearerAuth, OAuth2Auth
from .base import BaseConnector, ConnectorCapability, ConnectorStatus
from .config import ConnectorConfig
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    ConnectorError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .registry import ConnectorRegistry
from .types import ConnectorMetadata, RequestContext, ResponseContext

__all__ = [
    "APIKeyAuth",
    "AuthStrategy",
    "AuthenticationError",
    "BaseConnector",
    "BasicAuth",
    "BearerAuth",
    "ConnectionError",
    "ConnectorCapability",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectorMetadata",
    "ConnectorRegistry",
    "ConnectorStatus",
    "OAuth2Auth",
    "RateLimitError",
    "RequestContext",
    "ResponseContext",
    "TimeoutError",
    "ValidationError",
]
