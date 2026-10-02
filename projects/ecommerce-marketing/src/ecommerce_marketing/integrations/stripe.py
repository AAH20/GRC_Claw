"""Stripe payment platform integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class StripeIntegration:
    """Integration with the Stripe payment platform.

    Provides methods to interact with the Stripe API for payment processing,
    customer management, and subscription handling.
    """

    def __init__(
        self,
        secret_key: str | None = None,
        webhook_secret: str | None = None,
    ) -> None:
        """Initialize the Stripe integration.

        Args:
            secret_key: Stripe secret API key.
            webhook_secret: Stripe webhook signing secret.

        Raises:
            ValueError: If required credentials are not provided.
        """
        settings = get_settings()
        self.settings = settings
        self.secret_key = secret_key or settings.stripe_secret_key
        self.webhook_secret = webhook_secret or settings.stripe_webhook_secret
        self.api_version = settings.integrations.stripe.api_version

        if not self.secret_key:
            raise ValueError("Stripe secret key is required")

        self.base_url = "https://api.stripe.com/v1"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.secret_key, ""),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=httpx.Timeout(self.settings.integrations.stripe.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_customer(self, email: str, name: str | None = None, metadata: dict[str, str] | None = None) -> dict[str, Any]:
        """Create a customer in Stripe.

        Args:
            email: Customer email address.
            name: Customer name.
            metadata: Additional metadata.

        Returns:
            Created Stripe customer.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        data: dict[str, str] = {"email": email}
        if name:
            data["name"] = name
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        response = await client.post("/customers", data=data)
        response.raise_for_status()

        logger.info("Created customer in Stripe", email=email)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a payment intent in Stripe.

        Args:
            amount: Amount in smallest currency unit (cents for USD).
            currency: Three-letter ISO currency code.
            customer_id: Optional Stripe customer ID.
            metadata: Additional metadata.

        Returns:
            Created payment intent.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        data: dict[str, str] = {
            "amount": str(amount),
            "currency": currency,
            "automatic_payment_methods[enabled]": "true",
        }
        if customer_id:
            data["customer"] = customer_id
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        response = await client.post("/payment_intents", data=data)
        response.raise_for_status()

        logger.info("Created payment intent in Stripe", amount=amount, currency=currency)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        """Fetch a customer from Stripe.

        Args:
            customer_id: Stripe customer ID.

        Returns:
            Stripe customer data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(f"/customers/{customer_id}")
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a subscription in Stripe.

        Args:
            customer_id: Stripe customer ID.
            price_id: Stripe price ID.
            metadata: Additional metadata.

        Returns:
            Created subscription.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        data: dict[str, str] = {
            "customer": customer_id,
            "items[0][price]": price_id,
        }
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        response = await client.post("/subscriptions", data=data)
        response.raise_for_status()

        logger.info("Created subscription in Stripe", customer_id=customer_id, price_id=price_id)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_charges(
        self,
        customer_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List charges from Stripe.

        Args:
            customer_id: Optional customer ID filter.
            limit: Maximum number of charges to return.

        Returns:
            List of Stripe charges.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        params: dict[str, str] = {"limit": str(min(limit, 100))}
        if customer_id:
            params["customer"] = customer_id

        response = await client.get("/charges", params=params)
        response.raise_for_status()

        return response.json().get("data", [])

    def verify_webhook(self, payload: bytes, signature: str) -> dict[str, Any] | None:
        """Verify a Stripe webhook signature.

        Args:
            payload: Raw request body bytes.
            signature: Stripe-Signature header value.

        Returns:
            Parsed webhook event if valid, None otherwise.
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return None

        try:
            import stripe

            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            logger.info("Webhook verified", event_type=event.get("type"))
            return event
        except Exception as exc:
            logger.error("Webhook verification failed", error=str(exc))
            return None
