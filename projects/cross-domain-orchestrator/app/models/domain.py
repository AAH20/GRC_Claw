"""Domain-related Pydantic models.

Defines the data structures for domain routing and domain information.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DomainType(str, Enum):
    """Enumeration of supported domain types."""

    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HR = "hr"
    IT = "it"
    LEGAL = "legal"
    CUSTOM = "custom"


class DomainInfo(BaseModel):
    """Information about a registered domain.

    Attributes:
        name: Domain name.
        type: Domain type.
        description: Domain description.
        capabilities: List of domain capabilities.
        status: Current domain status.
        endpoint: Domain service endpoint.
    """

    name: str = Field(..., min_length=1, max_length=128, description="Domain name")
    type: DomainType = Field(..., description="Domain type")
    description: str = Field(default="", description="Domain description")
    capabilities: list[str] = Field(
        default_factory=list,
        description="Domain capabilities",
    )
    status: str = Field(default="active", description="Domain status")
    endpoint: str = Field(default="", description="Domain service endpoint")


class DomainRequest(BaseModel):
    """Request to route to a specific domain.

    Attributes:
        id: Unique request identifier.
        domain: Target domain name.
        action: Action to perform.
        payload: Request payload.
        priority: Request priority (1-10).
        metadata: Additional request metadata.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Request unique identifier",
    )
    domain: str = Field(..., min_length=1, max_length=128, description="Target domain")
    action: str = Field(..., min_length=1, max_length=128, description="Action to perform")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Request payload",
    )
    priority: int = Field(default=5, ge=1, le=10, description="Request priority (1-10)")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request metadata",
    )


class DomainResponse(BaseModel):
    """Response from a domain request.

    Attributes:
        request_id: Original request identifier.
        domain: Domain that handled the request.
        success: Whether the request succeeded.
        data: Response data.
        error: Error message if the request failed.
        processed_at: Processing timestamp.
    """

    request_id: str = Field(..., description="Original request identifier")
    domain: str = Field(..., description="Domain that handled the request")
    success: bool = Field(..., description="Whether the request succeeded")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Response data",
    )
    error: str | None = Field(default=None, description="Error message if failed")
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Processing timestamp",
    )
