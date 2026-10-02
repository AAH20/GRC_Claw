"""Payment gateway integration."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


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
        self.success = success
        self.transaction_id = transaction_id
        self.amount = amount
        self.currency = currency
        self.metadata = metadata or {}


class PaymentGateway(ABC):
    """Abstract base class for payment gateway integrations."""

    @abstractmethod
    async def process_payment(
        self, amount: float, currency: str, payment_method: str, metadata: dict[str, Any]
    ) -> PaymentResult:
        """Process a payment."""
        ...

    @abstractmethod
    async def refund_payment(
        self, transaction_id: str, amount: float | None = None
    ) -> PaymentResult:
        """Refund a payment."""
        ...


class StripePaymentGateway(PaymentGateway):
    """Stripe payment gateway integration."""

    def __init__(self, api_key: str, base_url: str = "https://api.stripe.com/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def process_payment(
        self, amount: float, currency: str, payment_method: str, metadata: dict[str, Any]
    ) -> PaymentResult:
        """Process a payment through Stripe."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment_intents",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={
                        "amount": int(amount * 100),
                        "currency": currency.lower(),
                        "payment_method": payment_method,
                        "confirm": "true",
                        "metadata": metadata,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return PaymentResult(
                    success=data.get("status") == "succeeded",
                    transaction_id=data.get("id", str(uuid4())),
                    amount=amount,
                    currency=currency,
                    metadata=data,
                )
        except httpx.HTTPError as e:
            logger.error("Stripe payment failed: %s", e)
            return PaymentResult(
                success=False,
                transaction_id=str(uuid4()),
                amount=amount,
                currency=currency,
                metadata={"error": str(e)},
            )

    async def refund_payment(
        self, transaction_id: str, amount: float | None = None
    ) -> PaymentResult:
        """Refund a payment through Stripe."""
        try:
            async with httpx.AsyncClient() as client:
                data: dict[str, Any] = {"payment_intent": transaction_id}
                if amount:
                    data["amount"] = int(amount * 100)

                response = await client.post(
                    f"{self.base_url}/refunds",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                )
                response.raise_for_status()
                refund_data = response.json()
                return PaymentResult(
                    success=refund_data.get("status") == "succeeded",
                    transaction_id=refund_data.get("id", str(uuid4())),
                    amount=amount or 0.0,
                    currency="USD",
                    metadata=refund_data,
                )
        except httpx.HTTPError as e:
            logger.error("Stripe refund failed: %s", e)
            return PaymentResult(
                success=False,
                transaction_id=str(uuid4()),
                amount=amount or 0.0,
                currency="USD",
                metadata={"error": str(e)},
            )
