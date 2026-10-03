"""Type definitions for rights management agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class InfringementDetectionRequest:
    """Represents a request to detect content infringement."""

    content_id: str
    content_url: str
    content_type: str
    reporter_id: str | None = None


@dataclass
class InfringementDetectionResult:
    """Represents the result of an infringement detection."""

    content_id: str
    is_infringing: bool
    confidence: float
    original_content_url: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LicenseDetectionRequest:
    """Represents a request to detect license information."""

    content_id: str
    content_url: str
    content_type: str


@dataclass
class LicenseDetectionResult:
    """Represents the result of a license detection."""

    content_id: str
    license_type: str | None = None
    license_url: str | None = None
    confidence: float = 0.0


@dataclass
class RightsValidationRequest:
    """Represents a request to validate rights."""

    content_id: str
    user_id: str
    action: str


@dataclass
class RightsValidation:
    """Represents the result of a rights validation."""

    content_id: str
    user_id: str
    action: str
    is_allowed: bool
    reason: str | None = None


@dataclass
class TakedownRequest:
    """Represents a content takedown request."""

    content_id: str
    reason: str
    requester_id: str
    legal_basis: str | None = None


@dataclass
class UsageRecord:
    """Represents a usage record for content."""

    content_id: str
    user_id: str
    usage_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
