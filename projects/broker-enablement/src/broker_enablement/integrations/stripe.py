"""Stripe integration client for the Broker Enablement platform."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class StripeClient:
    """Client for Stripe API integration.

    Handles payout processing, payment intent creation, and webhook
    verification for commission payouts to partners.
    """

    def __init__(
        self,
        secret_key: str,
        webhook_secret: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Stripe client.

        Args:
            secret_key: Stripe secret API key.
            webhook_secret: Stripe webhook signing secret.
            timeout: Request timeout in seconds.
        """
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret
        self.timeout = timeout
        self._base_url = "https://api.stripe.com/v1"

        logger.info("StripeClient initialized")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_payout(
        self,
        amount: Decimal,
        currency: str,
        destination: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a payout to a connected account.

        Args:
            amount: Payout amount.
            currency: Currency code (e.g., 'usd').
            destination: Stripe account ID or bank account ID.
            metadata: Optional metadata for the payout.

        Returns:
            Created payout data from Stripe.

        Raises:
            RuntimeError: If payout creation fails.
        """
        logger.info(
            "Creating Stripe payout",
            amount=str(amount),
            currency=currency,
            destination=destination,
        )

        # Convert decimal to cents for Stripe
        amount_cents = int(amount * 100)

        data: dict[str, str] = {
            "amount": str(amount_cents),
            "currency": currency,
            "destination": destination,
        }
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/payouts",
                    data=data,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create Stripe payout",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Failed to create Stripe payout: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a payment intent.

        Args:
            amount: Payment amount.
            currency: Currency code.
            customer_id: Optional Stripe customer ID.
            metadata: Optional metadata.

        Returns:
            Created payment intent data from Stripe.

        Raises:
            RuntimeError: If creation fails.
        """
        logger.info(
            "Creating Stripe payment intent",
            amount=str(amount),
            currency=currency,
        )

        amount_cents = int(amount * 100)

        data: dict[str, str] = {
            "amount": str(amount_cents),
            "currency": currency,
            "automatic_payment_methods[enabled]": "true",
        }
        if customer_id:
            data["customer"] = customer_id
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/payment_intents",
                    data=data,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create Stripe payment intent",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Failed to create Stripe payment intent: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_payout(self, payout_id: str) -> dict[str, Any]:
        """Get payout details by ID.

        Args:
            payout_id: The Stripe payout ID.

        Returns:
            Payout data from Stripe.

        Raises:
            RuntimeError: If fetching fails.
        """
        logger.info("Fetching Stripe payout", payout_id=payout_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self._base_url}/payouts/{payout_id}",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch Stripe payout",
                payout_id=payout_id,
                status_code=e.response.status_code,
            )
            raise RuntimeError(f"Failed to fetch Stripe payout: {e}") from e

    def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> dict[str, Any] | None:
        """Verify a Stripe webhook signature.

        Args:
            payload: The raw request body.
            signature: The Stripe-Signature header value.

        Returns:
            The webhook event data if valid, None otherwise.
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return None

        try:
            import stripe

            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event  # type: ignore[return-value]
        except Exception as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return None
