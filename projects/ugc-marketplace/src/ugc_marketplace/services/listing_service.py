"""Listing service for UGC marketplace.

Provides core business logic for creating, retrieving, and searching listings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class ListingStatus(str, Enum):
    """Lifecycle status of a listing."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    ARCHIVED = "archived"


class ListingCategory(str, Enum):
    """High-level category for a listing."""

    DIGITAL_ART = "digital_art"
    PHOTOGRAPHY = "photography"
    VIDEO = "video"
    AUDIO = "audio"
    WRITING = "writing"
    TEMPLATE = "template"
    OTHER = "other"


@dataclass(frozen=True)
class Money:
    """Monetary amount with ISO 4217 currency code."""

    amount_cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount_cents < 0:
            raise ValueError("amount_cents must be non-negative")
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("currency must be a 3-letter ISO 4217 code")


@dataclass
class Listing:
    """A marketplace listing."""

    id: str
    seller_id: str
    title: str
    description: str
    category: ListingCategory
    price: Money
    status: ListingStatus = ListingStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Repository protocol (dependency-inversion)
# ---------------------------------------------------------------------------

class ListingRepository(Protocol):
    """Persistence contract the service depends on."""

    def save(self, listing: Listing) -> Listing: ...
    def get_by_id(self, listing_id: str) -> Optional[Listing]: ...
    def search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int,
        offset: int,
    ) -> List[Listing]: ...
    def count(
        self,
        query: str,
        filters: Dict[str, Any],
    ) -> int: ...


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ListingValidationError(Exception):
    """Raised when listing data fails validation."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ListingNotFoundError(Exception):
    """Raised when a listing cannot be found by ID."""

    def __init__(self, listing_id: str) -> None:
        self.listing_id = listing_id
        super().__init__(f"Listing '{listing_id}' not found")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ListingService:
    """High-level service for listing operations."""

    # -- constants ---------------------------------------------------------

    _TITLE_MIN_LEN = 3
    _TITLE_MAX_LEN = 120
    _DESC_MIN_LEN = 10
    _DESC_MAX_LEN = 5000
    _MAX_TAGS = 10
    _MAX_MEDIA = 20
    _DEFAULT_PAGE_SIZE = 20
    _MAX_PAGE_SIZE = 100

    # -- constructor -------------------------------------------------------

    def __init__(self, repository: ListingRepository) -> None:
        self._repo = repository

    # -- public API --------------------------------------------------------

    def create_listing(self, data: Dict[str, Any]) -> Listing:
        """Create a new listing from raw input data.

        Parameters
        ----------
        data:
            Dictionary with keys ``seller_id``, ``title``, ``description``,
            ``category``, ``price`` (``{"amount_cents": int, "currency": str}``),
            and optionally ``tags``, ``media_urls``, ``status``, ``metadata``.

        Returns
        -------
        Listing
            The persisted listing.

        Raises
        ------
        ListingValidationError
            If any required field is missing or invalid.
        """
        listing = self._validate_and_build(data)
        return self._repo.save(listing)

    def get_listing(self, listing_id: str) -> Listing:
        """Retrieve a single listing by its unique identifier.

        Parameters
        ----------
        listing_id:
            The listing's unique ID.

        Returns
        -------
        Listing

        Raises
        ------
        ListingNotFoundError
            If no listing exists with the given ID.
        """
        if not listing_id or not listing_id.strip():
            raise ListingValidationError("listing_id", "must be a non-empty string")

        listing = self._repo.get_by_id(listing_id)
        if listing is None:
            raise ListingNotFoundError(listing_id)
        return listing

    def search_listings(
        self,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        *,
        limit: int = _DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search listings with optional filters and pagination.

        Parameters
        ----------
        query:
            Free-text search string (matches title, description, tags).
        filters:
            Key-value filters such as ``category``, ``status``,
            ``min_price_cents``, ``max_price_cents``, ``seller_id``.
        limit:
            Maximum number of results to return (1 – 100).
        offset:
            Number of results to skip (for pagination).

        Returns
        -------
        dict
            ``{"results": List[Listing], "total": int, "limit": int,
            "offset": int}``

        Raises
        ------
        ListingValidationError
            If ``limit`` or ``offset`` are out of range.
        """
        filters = filters or {}

        # Clamp / validate pagination
        if not isinstance(limit, int) or limit < 1:
            raise ListingValidationError("limit", "must be a positive integer")
        if limit > self._MAX_PAGE_SIZE:
            limit = self._MAX_PAGE_SIZE
        if not isinstance(offset, int) or offset < 0:
            raise ListingValidationError("offset", "must be a non-negative integer")

        # Normalise query
        query = (query or "").strip()

        # Validate filter keys
        allowed_filter_keys = {
            "category",
            "status",
            "min_price_cents",
            "max_price_cents",
            "seller_id",
            "tags",
        }
        unknown = set(filters) - allowed_filter_keys
        if unknown:
            raise ListingValidationError(
                "filters",
                f"unknown filter keys: {', '.join(sorted(unknown))}",
            )

        results = self._repo.search(query, filters, limit, offset)
        total = self._repo.count(query, filters)

        return {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # -- private helpers ---------------------------------------------------

    def _validate_and_build(self, data: Dict[str, Any]) -> Listing:
        """Validate raw data and return an unsaved Listing instance."""

        if not isinstance(data, dict):
            raise ListingValidationError("data", "must be a dictionary")

        # --- required scalar fields ---
        seller_id = self._require_str(data, "seller_id")
        title = self._require_str(data, "title")
        description = self._require_str(data, "description")

        # --- category ---
        category_raw = data.get("category")
        if category_raw is None:
            raise ListingValidationError("category", "is required")
        try:
            category = ListingCategory(category_raw)
        except ValueError:
            valid = ", ".join(c.value for c in ListingCategory)
            raise ListingValidationError(
                "category", f"must be one of: {valid}"
            ) from None

        # --- price ---
        price_raw = data.get("price")
        if price_raw is None:
            raise ListingValidationError("price", "is required")
        price = self._parse_price(price_raw)

        # --- optional status ---
        status_raw = data.get("status", ListingStatus.DRAFT.value)
        try:
            status = ListingStatus(status_raw)
        except ValueError:
            valid = ", ".join(s.value for s in ListingStatus)
            raise ListingValidationError(
                "status", f"must be one of: {valid}"
            ) from None

        # --- tags ---
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            raise ListingValidationError("tags", "must be a list of strings")
        if len(tags) > self._MAX_TAGS:
            raise ListingValidationError(
                "tags", f"cannot exceed {self._MAX_TAGS} tags"
            )
        for i, tag in enumerate(tags):
            if not isinstance(tag, str) or not tag.strip():
                raise ListingValidationError(
                    "tags", f"tag at index {i} must be a non-empty string"
                )

        # --- media_urls ---
        media_urls = data.get("media_urls", [])
        if not isinstance(media_urls, list):
            raise ListingValidationError("media_urls", "must be a list of strings")
        if len(media_urls) > self._MAX_MEDIA:
            raise ListingValidationError(
                "media_urls", f"cannot exceed {self._MAX_MEDIA} URLs"
            )
        for i, url in enumerate(media_urls):
            if not isinstance(url, str) or not url.strip():
                raise ListingValidationError(
                    "media_urls", f"URL at index {i} must be a non-empty string"
                )

        # --- metadata ---
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ListingValidationError("metadata", "must be a dictionary")

        # --- length checks ---
        if len(title) < self._TITLE_MIN_LEN:
            raise ListingValidationError(
                "title",
                f"must be at least {self._TITLE_MIN_LEN} characters",
            )
        if len(title) > self._TITLE_MAX_LEN:
            raise ListingValidationError(
                "title",
                f"cannot exceed {self._TITLE_MAX_LEN} characters",
            )
        if len(description) < self._DESC_MIN_LEN:
            raise ListingValidationError(
                "description",
                f"must be at least {self._DESC_MIN_LEN} characters",
            )
        if len(description) > self._DESC_MAX_LEN:
            raise ListingValidationError(
                "description",
                f"cannot exceed {self._DESC_MAX_LEN} characters",
            )

        # --- build ---
        import uuid

        return Listing(
            id=str(uuid.uuid4()),
            seller_id=seller_id,
            title=title.strip(),
            description=description.strip(),
            category=category,
            price=price,
            status=status,
            tags=[t.strip() for t in tags if t.strip()],
            media_urls=[u.strip() for u in media_urls if u.strip()],
            metadata=metadata,
        )

    # -- small validation utilities ----------------------------------------

    @staticmethod
    def _require_str(data: Dict[str, Any], key: str) -> str:
        value = data.get(key)
        if value is None:
            raise ListingValidationError(key, "is required")
        if not isinstance(value, str) or not value.strip():
            raise ListingValidationError(key, "must be a non-empty string")
        return value.strip()

    def _parse_price(self, raw: Any) -> Money:
        if isinstance(raw, Money):
            return raw
        if not isinstance(raw, dict):
            raise ListingValidationError(
                "price", "must be a dict with 'amount_cents' and 'currency'"
            )
        amount = raw.get("amount_cents")
        if not isinstance(amount, int) or amount < 0:
            raise ListingValidationError(
                "price.amount_cents", "must be a non-negative integer"
            )
        currency = raw.get("currency", "USD")
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            raise ListingValidationError(
                "price.currency", "must be a 3-letter ISO 4217 code"
            )
        return Money(amount_cents=amount, currency=currency)
