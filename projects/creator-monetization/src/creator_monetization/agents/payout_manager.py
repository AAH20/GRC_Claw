"""Payout Manager Agent - Handles creator payouts and payment processing."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Payout, PayoutStatus

logger = structlog.get_logger(__name__)


class PayoutSchedule(BaseModel):
    """Payout schedule configuration."""

    frequency: str = Field(default="monthly", description="Payout frequency")
    min_threshold: Decimal = Field(default=Decimal("50.00"), ge=0)
    payment_method: str = Field(default="bank_transfer")
    auto_process: bool = False


class PayoutManagerAgent:
    """Agent responsible for managing creator payouts.

    Handles payout calculation, scheduling, processing,
    and tracking of all creator payment transactions.
    """

    def __init__(
        self,
        schedule: PayoutSchedule | None = None,
        min_payout: Decimal = Decimal("50.00"),
    ) -> None:
        """Initialize the payout manager agent.

        Args:
            schedule: Payout schedule configuration.
            min_payout: Minimum payout threshold.
        """
        self.schedule = schedule or PayoutSchedule()
        self.min_payout = min_payout
        self._payouts: dict[str, Payout] = {}
        self._creator_balances: dict[str, Decimal] = {}

    async def create_payout(self, payout: Payout) -> Payout:
        """Create a new payout record.

        Args:
            payout: The payout to create.

        Returns:
            The created payout.

        Raises:
            ValueError: If payout_id already exists or amount below minimum.
        """
        if payout.payout_id in self._payouts:
            raise ValueError(f"Payout {payout.payout_id} already exists")
        if payout.amount < self.min_payout:
            raise ValueError(
                f"Payout amount {payout.amount} below minimum {self.min_payout}"
            )

        logger.info(
            "Creating payout",
            payout_id=payout.payout_id,
            creator_id=payout.creator_id,
            amount=str(payout.amount),
        )
        self._payouts[payout.payout_id] = payout
        return payout

    async def process_payout(self, payout_id: str) -> Payout:
        """Process a pending payout.

        Args:
            payout_id: The payout to process.

        Returns:
            Updated payout record.

        Raises:
            KeyError: If payout not found.
            ValueError: If payout is not in pending status.
        """
        if payout_id not in self._payouts:
            raise KeyError(f"Payout {payout_id} not found")

        payout = self._payouts[payout_id]
        if payout.status != PayoutStatus.PENDING:
            raise ValueError(
                f"Payout {payout_id} is not pending (status: {payout.status})"
            )

        logger.info("Processing payout", payout_id=payout_id)
        payout.status = PayoutStatus.PROCESSING

        # In production, integrate with payment processor (Stripe, PayPal, etc.)
        payout.status = PayoutStatus.COMPLETED
        payout.paid_at = datetime.now(UTC)

        # Update creator balance
        if payout.creator_id in self._creator_balances:
            self._creator_balances[payout.creator_id] -= payout.amount

        logger.info("Payout completed", payout_id=payout_id)
        return payout

    async def fail_payout(self, payout_id: str, reason: str) -> Payout:
        """Mark a payout as failed.

        Args:
            payout_id: The payout to fail.
            reason: Failure reason.

        Returns:
            Updated payout record.

        Raises:
            KeyError: If payout not found.
        """
        if payout_id not in self._payouts:
            raise KeyError(f"Payout {payout_id} not found")

        payout = self._payouts[payout_id]
        payout.status = PayoutStatus.FAILED
        payout.metadata["failure_reason"] = reason
        logger.warning("Payout failed", payout_id=payout_id, reason=reason)
        return payout

    async def batch_process_payouts(self, payout_ids: list[str]) -> dict[str, Any]:
        """Process multiple payouts in batch.

        Args:
            payout_ids: List of payout IDs to process.

        Returns:
            Batch processing results with success and failure counts.
        """
        results: dict[str, Any] = {
            "total": len(payout_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for payout_id in payout_ids:
            try:
                await self.process_payout(payout_id)
                results["successful"] += 1
            except (KeyError, ValueError) as exc:
                results["failed"] += 1
                results["errors"].append({"payout_id": payout_id, "error": str(exc)})

        logger.info(
            "Batch payout processing complete",
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"],
        )
        return results

    def get_pending_payouts(self) -> list[Payout]:
        """Get all pending payouts.

        Returns:
            List of pending payout records.
        """
        return [p for p in self._payouts.values() if p.status == PayoutStatus.PENDING]

    def get_creator_payouts(self, creator_id: str) -> list[Payout]:
        """Get all payouts for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            List of payout records.
        """
        return [p for p in self._payouts.values() if p.creator_id == creator_id]

    def get_creator_balance(self, creator_id: str) -> Decimal:
        """Get the current balance for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            Current balance amount.
        """
        return self._creator_balances.get(creator_id, Decimal("0"))

    def get_total_paid(self, creator_id: str) -> Decimal:
        """Get total paid amount for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            Total paid amount.
        """
        return sum(
            (
                p.amount
                for p in self._payouts.values()
                if p.creator_id == creator_id and p.status == PayoutStatus.COMPLETED
            ),
            Decimal("0"),
        )

    def get_payout_count(self) -> int:
        """Get total number of payouts.

        Returns:
            Total payout count.
        """
        return len(self._payouts)