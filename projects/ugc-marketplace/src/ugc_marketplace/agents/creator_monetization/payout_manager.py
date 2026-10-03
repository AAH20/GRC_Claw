"""Payout Manager Agent for creator monetization."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PayoutSchedule(BaseModel):
    """Payout schedule configuration."""

    frequency: str = Field(default="monthly", description="Payout frequency")
    next_payout_date: datetime = Field(..., description="Next payout date")
    minimum_threshold: Decimal = Field(default=Decimal("50.00"), ge=0)


class PayoutManagerAgent:
    """Agent responsible for managing creator payouts.

    Handles payout scheduling, processing, and tracking
    for creator monetization.
    """

    def __init__(self) -> None:
        """Initialize the payout manager agent."""
        self._payouts: dict[str, dict[str, Any]] = {}
        self._schedules: dict[str, PayoutSchedule] = {}
        self._counter = 0

    async def schedule_payout(
        self,
        creator_id: str,
        schedule: PayoutSchedule,
    ) -> dict[str, Any]:
        """Schedule a payout for a creator.

        Args:
            creator_id: Creator identifier.
            schedule: Payout schedule configuration.

        Returns:
            Schedule confirmation data.
        """
        self._schedules[creator_id] = schedule
        logger.info("Payout scheduled", creator_id=creator_id, frequency=schedule.frequency)
        return {
            "creator_id": creator_id,
            "schedule": schedule.model_dump(),
            "status": "scheduled",
        }

    async def create_payout(
        self,
        creator_id: str,
        amount: Decimal,
        currency: str = "USD",
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a payout for a creator.

        Args:
            creator_id: Creator identifier.
            amount: Payout amount.
            currency: Currency code.
            period_start: Payout period start.
            period_end: Payout period end.

        Returns:
            Created payout data.

        Raises:
            ValueError: If amount is non-positive.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self._counter += 1
        payout_id = f"po_{self._counter:06d}"

        payout = {
            "payout_id": payout_id,
            "creator_id": creator_id,
            "amount": str(amount),
            "currency": currency,
            "status": "pending",
            "period_start": (period_start or datetime.now(UTC)).isoformat(),
            "period_end": (period_end or datetime.now(UTC)).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }

        self._payouts[payout_id] = payout
        logger.info("Payout created", payout_id=payout_id, creator_id=creator_id, amount=str(amount))
        return payout

    async def process_payout(self, payout_id: str) -> dict[str, Any]:
        """Process a pending payout.

        Args:
            payout_id: Payout identifier.

        Returns:
            Updated payout data.

        Raises:
            ValueError: If payout not found.
        """
        if payout_id not in self._payouts:
            raise ValueError(f"Payout {payout_id} not found")

        payout = self._payouts[payout_id]
        payout["status"] = "processing"
        payout["updated_at"] = datetime.now(UTC).isoformat()

        logger.info("Payout processing", payout_id=payout_id)
        return payout

    async def complete_payout(self, payout_id: str) -> dict[str, Any]:
        """Mark a payout as completed.

        Args:
            payout_id: Payout identifier.

        Returns:
            Updated payout data.

        Raises:
            ValueError: If payout not found.
        """
        if payout_id not in self._payouts:
            raise ValueError(f"Payout {payout_id} not found")

        payout = self._payouts[payout_id]
        payout["status"] = "completed"
        payout["paid_at"] = datetime.now(UTC).isoformat()

        logger.info("Payout completed", payout_id=payout_id)
        return payout

    async def fail_payout(self, payout_id: str, reason: str = "Processing failed") -> dict[str, Any]:
        """Mark a payout as failed.

        Args:
            payout_id: Payout identifier.
            reason: Failure reason.

        Returns:
            Updated payout data.

        Raises:
            ValueError: If payout not found.
        """
        if payout_id not in self._payouts:
            raise ValueError(f"Payout {payout_id} not found")

        payout = self._payouts[payout_id]
        payout["status"] = "failed"
        payout["failure_reason"] = reason
        payout["updated_at"] = datetime.now(UTC).isoformat()

        logger.warning("Payout failed", payout_id=payout_id, reason=reason)
        return payout

    def get_payout(self, payout_id: str) -> dict[str, Any] | None:
        """Get a payout by ID.

        Args:
            payout_id: Payout identifier.

        Returns:
            Payout data or None if not found.
        """
        return self._payouts.get(payout_id)

    def list_payouts(
        self,
        creator_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List payouts with optional filtering.

        Args:
            creator_id: Filter by creator.
            status: Filter by status.

        Returns:
            List of payout data.
        """
        results = list(self._payouts.values())
        if creator_id:
            results = [p for p in results if p["creator_id"] == creator_id]
        if status:
            results = [p for p in results if p["status"] == status]
        return results

    def get_creator_balance(self, creator_id: str) -> dict[str, Any]:
        """Get balance summary for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            Balance summary data.
        """
        creator_payouts = [p for p in self._payouts.values() if p["creator_id"] == creator_id]
        total = sum(Decimal(p["amount"]) for p in creator_payouts if p["status"] == "completed")
        pending = sum(Decimal(p["amount"]) for p in creator_payouts if p["status"] == "pending")

        return {
            "creator_id": creator_id,
            "total_paid": str(total),
            "pending": str(pending),
            "currency": "USD",
        }
