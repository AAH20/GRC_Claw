"""
Common type definitions for the connector SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime, timezone


class ConnectorCapability(str, Enum):
    """Capabilities a connector can declare."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    STREAM = "stream"
    BATCH = "batch"
    REALTIME = "realtime"
    WEBHOOK = "webhook"
    PAGINATION = "pagination"
    INCREMENTAL_SYNC = "incremental_sync"
    FULL_SYNC = "full_sync"


class ConnectorStatus(str, Enum):
    """Operational status of a connector."""

    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class ConnectorMetadata:
    """Metadata describing a connector."""

    name: str
    version: str
    vendor: str
    description: str = ""
    capabilities: list[ConnectorCapability] = field(default_factory=list)
    supported_auth: list[str] = field(default_factory=list)
    rate_limit_per_minute: int = 60
    documentation_url: str = ""
    icon_url: str = ""
    category: str = "general"
    tags: list[str] = field(default_factory=list)


@dataclass
class RequestContext:
    """Context for an outgoing request."""

    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    body: Any = None
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: f"req_{datetime.now(timezone.utc).timestamp()}")


@dataclass
class ResponseContext:
    """Context for an incoming response."""

    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    raw_content: bytes = b""
    latency_ms: float = 0.0
    request: Optional[RequestContext] = None
    is_success: bool = False
    error_message: str = ""
    retry_after_seconds: Optional[float] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    pagination_cursor: Optional[str] = None
    pagination_has_more: bool = False
