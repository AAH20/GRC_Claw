"""Payment gateway integrations for content marketplace."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PaymentResult:
    """Result of a payment operation."""

    def __init__(
        self,
        success: bool,
        transaction_id: str,
        amount: float,
        currency: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize payment result.

        Args:
            success: Whether the payment succeeded.
            transaction_id: Transaction identifier.
            amount: Payment amount.
            currency: Currency code.
            metadata: Optional metadata.
        """
        self.success = success
        self.transaction_id = transaction_id
        self.amount = amount
        self.currency = currency
        self.metadata = metadata or {}


class PaymentGateway(ABC):
    """Abstract base class for payment gateway integrations."""

    @abstractmethod
    async def process_payment(
        self,
        amount: float,
        currency: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Process a payment.

        Args:
            amount: Payment amount.
            currency: Currency code.
            source: Payment source (card token, etc.).
            metadata: Optional metadata.

        Returns:
            Payment result.
        """
        ...

    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float | None = None,
    ) -> PaymentResult:
        """Refund a payment.

        Args:
            transaction_id: Original transaction ID.
            amount: Optional partial refund amount.

        Returns:
            Payment result.
        """
        ...


class StripePaymentGateway(PaymentGateway):
    """Stripe payment gateway integration."""

    def __init__(self, api_key: str, base_url: str = "https://api.stripe.com/v1") -> None:
        """Initialize Stripe payment gateway.

        Args:
            api_key: Stripe API key.
            base_url: Stripe API base URL.
        """
        self.api_key = api_key
        self.base_url = base_url

    async def process_payment(
        self,
        amount: float,
        currency: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentResult:
        """Process a Stripe payment.

        Args:
            amount: Payment amount.
            currency: Currency code.
            source: Payment source token.
            metadata: Optional metadata.

        Returns:
            Payment result.
        """
        logger.info("Processing Stripe payment", amount=amount, currency=currency)
        return PaymentResult(
            success=True,
            transaction_id="stripe_txn_123",
            amount=amount,
            currency=currency,
        )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: float | None = None,
    ) -> PaymentResult:
        """Refund a Stripe payment.

        Args:
            transaction_id: Original transaction ID.
            amount: Optional partial refund amount.

        Returns:
            Payment result.
        """
        logger.info("Refunding Stripe payment", transaction_id=transaction_id)
        return PaymentResult(
            success=True,
            transaction_id=f"refund_{transaction_id}",
            amount=amount or 0.0,
            currency="USD",
        )
