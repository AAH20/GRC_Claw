"""Tracking Agent - Monitors clicks, conversions, and attribution."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ConversionStatus(StrEnum):
    """Status of a conversion event."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ClickEvent(BaseModel):
    """Represents a click tracking event."""

    click_id: str = Field(..., description="Unique click identifier")
    partner_id: str = Field(..., description="Affiliate partner ID")
    campaign_id: str = Field(..., description="Campaign identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: str | None = Field(default=None, description="Visitor IP address")
    user_agent: str | None = Field(default=None, description="Visitor user agent")
    referrer: str | None = Field(default=None, description="Referrer URL")


class ConversionEvent(BaseModel):
    """Represents a conversion/sale tracking event."""

    conversion_id: str = Field(..., description="Unique conversion identifier")
    click_id: str = Field(..., description="Associated click ID")
    partner_id: str = Field(..., description="Attributing partner ID")
    campaign_id: str = Field(..., description="Campaign identifier")
    amount: float = Field(..., gt=0, description="Conversion amount")
    commission: float = Field(..., ge=0, description="Commission amount")
    status: ConversionStatus = Field(default=ConversionStatus.PENDING)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrackingAgent:
    """Agent responsible for tracking affiliate clicks and conversions.

    Handles click attribution, conversion tracking, and provides
    real-time monitoring of affiliate performance.
    """

    def __init__(self) -> None:
        """Initialize the tracking agent."""
        self._clicks: dict[str, ClickEvent] = {}
        self._conversions: dict[str, ConversionEvent] = {}

    async def track_click(self, event: ClickEvent) -> ClickEvent:
        """Track a click event.

        Args:
            event: The click event to track.

        Returns:
            The stored click event.

        Raises:
            ValueError: If click_id already exists.
        """
        if event.click_id in self._clicks:
            raise ValueError(f"Click {event.click_id} already tracked")

        logger.info("Tracking click", click_id=event.click_id, partner_id=event.partner_id)
        self._clicks[event.click_id] = event
        return event

    async def track_conversion(self, event: ConversionEvent) -> ConversionEvent:
        """Track a conversion event.

        Args:
            event: The conversion event to track.

        Returns:
            The stored conversion event.

        Raises:
            ValueError: If conversion_id already exists or click_id not found.
        """
        if event.conversion_id in self._conversions:
            raise ValueError(f"Conversion {event.conversion_id} already tracked")
        if event.click_id not in self._clicks:
            raise ValueError(f"Click {event.click_id} not found for attribution")

        logger.info(
            "Tracking conversion",
            conversion_id=event.conversion_id,
            partner_id=event.partner_id,
            amount=event.amount,
        )
        self._conversions[event.conversion_id] = event
        return event

    async def update_conversion_status(
        self, conversion_id: str, status: ConversionStatus
    ) -> ConversionEvent:
        """Update the status of a conversion.

        Args:
            conversion_id: The conversion to update.
            status: New status.

        Returns:
            Updated conversion event.

        Raises:
            KeyError: If conversion_id not found.
        """
        if conversion_id not in self._conversions:
            raise KeyError(f"Conversion {conversion_id} not found")

        conversion = self._conversions[conversion_id]
        conversion.status = status
        logger.info("Updated conversion status", conversion_id=conversion_id, status=status)
        return conversion

    def get_partner_stats(self, partner_id: str) -> dict[str, Any]:
        """Get tracking statistics for a partner.

        Args:
            partner_id: The partner to get stats for.

        Returns:
            Dictionary with clicks, conversions, and revenue.
        """
        clicks = [c for c in self._clicks.values() if c.partner_id == partner_id]
        conversions = [c for c in self._conversions.values() if c.partner_id == partner_id]

        total_revenue = sum(c.amount for c in conversions)
        total_commission = sum(c.commission for c in conversions)
        conversion_rate = len(conversions) / len(clicks) if clicks else 0.0

        return {
            "partner_id": partner_id,
            "total_clicks": len(clicks),
            "total_conversions": len(conversions),
            "conversion_rate": round(conversion_rate, 4),
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2),
        }

    def get_click_count(self) -> int:
        """Get total tracked clicks.

        Returns:
            Total number of clicks.
        """
        return len(self._clicks)

    def get_conversion_count(self) -> int:
        """Get total tracked conversions.

        Returns:
            Total number of conversions.
        """
        return len(self._conversions)
