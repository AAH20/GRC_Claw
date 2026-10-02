"""GRC Unified SDK — a unified client for all 75 GRC projects.

This package provides a single, consistent interface for interacting
with the GRC API across all projects.  It includes:

- :class:`GRCClient` — the primary HTTP client with retries, pagination,
  and typed error handling.
- :class:`GRCConfig` — layered configuration management.
- Shared Pydantic models for projects, controls, evidence, findings,
  assessments, and audit entries.
- A typed exception hierarchy rooted at :class:`GRCError`.

Quick start::

    from grc_unified import GRCClient

    client = GRCClient(api_key="your-api-key")
    for project in client.paginate(client.list_projects):
        print(f"{project.name}: {project.control_count} controls")

Configuration::

    from grc_unified import GRCConfig, GRCClient

    config = GRCConfig(
        api_key="your-api-key",
        api_base_url="https://api.grc.example.com",
        timeout=60,
    )
    client = GRCClient(config=config)
"""

from __future__ import annotations

from .client import GRCClient
from .config import GRCConfig, get_config, load_config, reset_config, set_config
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConnectionError,
    ConflictError,
    GRCError,
    NotFoundError,
    ProjectNotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Assessment,
    AssessmentStatus,
    AuditEntry,
    Control,
    ControlStatus,
    Evidence,
    EvidenceType,
    Finding,
    FindingSeverity,
    FindingStatus,
    GRCBaseModel,
    HealthStatus,
    PageMetadata,
    PaginatedResponse,
    Project,
    ProjectStats,
    ProjectSummary,
)

__version__ = "1.0.0"
__author__ = "Ahmed Hassan"
__all__ = [
    # Client
    "GRCClient",
    # Configuration
    "GRCConfig",
    "get_config",
    "load_config",
    "set_config",
    "reset_config",
    # Exceptions
    "GRCError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ConnectionError",
    "ConflictError",
    "NotFoundError",
    "ProjectNotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    # Base model
    "GRCBaseModel",
    # Enums
    "AssessmentStatus",
    "ControlStatus",
    "EvidenceType",
    "FindingSeverity",
    "FindingStatus",
    # Models
    "Assessment",
    "AuditEntry",
    "Control",
    "Evidence",
    "Finding",
    "HealthStatus",
    "PageMetadata",
    "PaginatedResponse",
    "Project",
    "ProjectStats",
    "ProjectSummary",
]
