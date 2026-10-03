"""Gated Communities SDK — Python client for the Gated Communities API.

This package provides a production-grade Python SDK for interacting with
the Gated Communities platform. It includes an authenticated HTTP client,
Pydantic request/response models, and custom exception types.

Quick start:
    >>> from gated_communities import GatedCommunitiesClient
    >>> client = GatedCommunitiesClient(api_key="your-api-key")
    >>> communities = client.communities.list()
"""

from .client import GatedCommunitiesClient
from .exceptions import (
                         AuthenticationError,
                         AuthorizationError,
                         GatedCommunitiesError,
                         NotFoundError,
                         RateLimitError,
                         ServerError,
                         ValidationError,
)
from .models import (
                         Community,
                         CommunityCreate,
                         CommunityUpdate,
                         Member,
                         MemberCreate,
                         MemberUpdate,
                         PaginatedResponse,
                         User,
)

__version__ = "1.0.0"
__author__ = "GRC Claw"
__license__ = "MIT"

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "Community",
    "CommunityCreate",
    "CommunityUpdate",
    "GatedCommunitiesClient",
    "GatedCommunitiesError",
    "Member",
    "MemberCreate",
    "MemberUpdate",
    "NotFoundError",
    "PaginatedResponse",
    "RateLimitError",
    "ServerError",
    "User",
    "ValidationError",
]
