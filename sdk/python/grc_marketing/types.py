"""Type definitions for the GRC Marketing SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union


# ─── Enums ──────────────────────────────────────────────────────────────────


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LeadStatus(str, Enum):
    """Lead lifecycle status."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class JourneyStatus(str, Enum):
    """Journey lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Channel(str, Enum):
    """Marketing channel."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SOCIAL = "social"
    WEB = "web"


# ─── TypedDicts for API payloads ────────────────────────────────────────────


class CampaignCreatePayload(TypedDict, total=False):
    """Payload for creating a campaign."""

    name: str
    description: str
    channel: str
    status: str
    start_date: str
    end_date: str
    budget: float
    tags: List[str]
    metadata: Dict[str, Any]


class CampaignUpdatePayload(TypedDict, total=False):
    """Payload for updating a campaign."""

    name: str
    description: str
    status: str
    start_date: str
    end_date: str
    budget: float
    tags: List[str]
    metadata: Dict[str, Any]


class LeadCreatePayload(TypedDict, total=False):
    """Payload for creating a lead."""

    email: str
    first_name: str
    last_name: str
    phone: str
    company: str
    source: str
    status: str
    tags: List[str]
    metadata: Dict[str, Any]


class LeadUpdatePayload(TypedDict, total=False):
    """Payload for updating a lead."""

    email: str
    first_name: str
    last_name: str
    phone: str
    company: str
    source: str
    status: str
    tags: List[str]
    metadata: Dict[str, Any]


class JourneyCreatePayload(TypedDict, total=False):
    """Payload for creating a journey."""

    name: str
    description: str
    status: str
    steps: List[Dict[str, Any]]
    tags: List[str]
    metadata: Dict[str, Any]


class JourneyUpdatePayload(TypedDict, total=False):
    """Payload for updating a journey."""

    name: str
    description: str
    status: str
    steps: List[Dict[str, Any]]
    tags: List[str]
    metadata: Dict[str, Any]


class AnalyticsQuery(TypedDict, total=False):
    """Query parameters for analytics."""

    start_date: str
    end_date: str
    metrics: List[str]
    dimensions: List[str]
    filters: Dict[str, Any]


class PaginationParams(TypedDict, total=False):
    """Pagination parameters."""

    page: int
    per_page: int
    sort_by: str
    sort_order: str


class ListResponse(TypedDict):
    """Generic list response wrapper."""

    data: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int


# ─── Dataclasses for structured responses ────────────────────────────────────


@dataclass
class Campaign:
    """Represents a marketing campaign."""

    id: str
    name: str
    description: str = ""
    channel: Channel = Channel.EMAIL
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Campaign:
        """Create a Campaign from an API response dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            channel=Channel(data.get("channel", "email")),
            status=CampaignStatus(data.get("status", "draft")),
            start_date=cls._parse_datetime(data.get("start_date")),
            end_date=cls._parse_datetime(data.get("end_date")),
            budget=data.get("budget", 0.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse an ISO datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


@dataclass
class Lead:
    """Represents a marketing lead."""

    id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    company: str = ""
    source: str = ""
    status: LeadStatus = LeadStatus.NEW
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Lead:
        """Create a Lead from an API response dict."""
        return cls(
            id=data["id"],
            email=data["email"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone=data.get("phone", ""),
            company=data.get("company", ""),
            source=data.get("source", ""),
            status=LeadStatus(data.get("status", "new")),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=Campaign._parse_datetime(data.get("created_at")),
            updated_at=Campaign._parse_datetime(data.get("updated_at")),
        )


@dataclass
class Journey:
    """Represents a customer journey."""

    id: str
    name: str
    description: str = ""
    status: JourneyStatus = JourneyStatus.DRAFT
    steps: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Journey:
        """Create a Journey from an API response dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=JourneyStatus(data.get("status", "draft")),
            steps=data.get("steps", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=Campaign._parse_datetime(data.get("created_at")),
            updated_at=Campaign._parse_datetime(data.get("updated_at")),
        )


@dataclass
class AnalyticsReport:
    """Represents an analytics report."""

    metrics: Dict[str, Any] = field(default_factory=dict)
    dimensions: Dict[str, Any] = field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_records: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnalyticsReport:
        """Create an AnalyticsReport from an API response dict."""
        return cls(
            metrics=data.get("metrics", {}),
            dimensions=data.get("dimensions", {}),
            start_date=Campaign._parse_datetime(data.get("start_date")),
            end_date=Campaign._parse_datetime(data.get("end_date")),
            total_records=data.get("total_records", 0),
        )


@dataclass
class AuthToken:
    """Represents an authentication token."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    obtained_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        from datetime import timedelta

        return datetime.utcnow() > self.obtained_at + timedelta(seconds=self.expires_in)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthToken:
        """Create an AuthToken from an API response dict."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )
