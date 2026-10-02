"""Payout Agent - Commission calculation and payment processing."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PayoutStatus(StrEnum):
    """Status of a payout."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CommissionTier(BaseModel):
    """Commission tier with threshold and rate."""

    min_amount: Decimal = Field(..., ge=0, description="Minimum amount for this tier")
    rate: Decimal = Field(..., ge=0, le=1, description="Commission rate (0-1)")


class PayoutRecord(BaseModel):
    """Represents a payout to an affiliate partner."""

    payout_id: str = Field(..., description="Unique payout identifier")
    partner_id: str = Field(..., description="Partner ID")
    amount: Decimal = Field(..., gt=0, description="Payout amount")
    currency: str = Field(default="USD", description="Currency code")
    status: PayoutStatus = Field(default=PayoutStatus.PENDING)
    period_start: datetime = Field(..., description="Payout period start")
    period_end: datetime = Field(..., description="Payout period end")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    paid_at: datetime | None = Field(default=None, description="When payout was completed")
    payment_method: str = Field(default="bank_transfer", description="Payment method")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PayoutAgent:
    """Agent responsible for commission calculations and payout processing.

    Handles tiered commission structures, payment scheduling,
    and payout status tracking.
    """

    def __init__(
        self,
        commission_tiers: list[CommissionTier] | None = None,
        min_payout: Decimal = Decimal("50.00"),
    ) -> None:
        """Initialize the payout agent.

        Args:
            commission_tiers: Tiered commission structure.
            min_payout: Minimum payout threshold.
        """
        self.commission_tiers = commission_tiers or [
            CommissionTier(min_amount=Decimal("0"), rate=Decimal("0.10")),
            CommissionTier(min_amount=Decimal("1000"), rate=Decimal("0.15")),
            CommissionTier(min_amount=Decimal("5000"), rate=Decimal("0.20")),
        ]
        self.min_payout = min_payout
        self._payouts: dict[str, PayoutRecord] = {}

    def calculate_commission(self, amount: Decimal) -> Decimal:
        """Calculate commission for a given sale amount.

        Args:
            amount: The sale amount.

        Returns:
            Calculated commission amount.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        applicable_rate = Decimal("0")
        for tier in self.commission_tiers:
            if amount >= tier.min_amount:
                applicable_rate = tier.rate

        commission = (amount * applicable_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        logger.info("Calculated commission", amount=str(amount), commission=str(commission))
        return commission

    async def create_payout(self, record: PayoutRecord) -> PayoutRecord:
        """Create a new payout record.

        Args:
            record: The payout record to create.

        Returns:
            The created payout record.

        Raises:
            ValueError: If payout_id already exists or amount below minimum.
        """
        if record.payout_id in self._payouts:
            raise ValueError(f"Payout {record.payout_id} already exists")
        if record.amount < self.min_payout:
            raise ValueError(
                f"Payout amount {record.amount} below minimum {self.min_payout}"
            )

        logger.info(
            "Creating payout",
            payout_id=record.payout_id,
            partner_id=record.partner_id,
            amount=str(record.amount),
        )
        self._payouts[record.payout_id] = record
        return record

    async def process_payout(self, payout_id: str) -> PayoutRecord:
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
            raise ValueError(f"Payout {payout_id} is not pending (status: {payout.status})")

        logger.info("Processing payout", payout_id=payout_id)
        payout.status = PayoutStatus.PROCESSING

        # In production, integrate with payment processor (Stripe, PayPal, etc.)
        payout.status = PayoutStatus.COMPLETED
        payout.paid_at = datetime.now(UTC)

        logger.info("Payout completed", payout_id=payout_id)
        return payout

    async def fail_payout(self, payout_id: str, reason: str) -> PayoutRecord:
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

    def get_pending_payouts(self) -> list[PayoutRecord]:
        """Get all pending payouts.

        Returns:
            List of pending payout records.
        """
        return [p for p in self._payouts.values() if p.status == PayoutStatus.PENDING]

    def get_partner_payouts(self, partner_id: str) -> list[PayoutRecord]:
        """Get all payouts for a partner.

        Args:
            partner_id: The partner to get payouts for.

        Returns:
            List of payout records.
        """
        return [p for p in self._payouts.values() if p.partner_id == partner_id]

    def get_total_paid(self, partner_id: str) -> Decimal:
        """Get total paid amount for a partner.

        Args:
            partner_id: The partner to get total paid for.

        Returns:
            Total paid amount.
        """
        return sum(
            (p.amount for p in self._payouts.values()
             if p.partner_id == partner_id and p.status == PayoutStatus.COMPLETED),
            Decimal("0"),
        )
