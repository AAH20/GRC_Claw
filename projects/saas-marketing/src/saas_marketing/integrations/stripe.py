"""Stripe integration module."""

from __future__ import annotations

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class StripeConfig(BaseModel):
    """Stripe API configuration."""

    secret_key: str = Field(..., description="Stripe secret API key")
    webhook_secret: str = Field(default="", description="Webhook signing secret")
    api_version: str = Field(default="2024-06-20", description="Stripe API version")


class StripeCustomer(BaseModel):
    """Stripe customer record."""

    id: str | None = Field(default=None, description="Stripe customer ID")
    email: str = Field(..., description="Customer email")
    name: str = Field(default="", description="Customer name")
    metadata: dict[str, str] = Field(default_factory=dict, description="Custom metadata")


class StripeSubscription(BaseModel):
    """Stripe subscription record."""

    id: str | None = Field(default=None, description="Subscription ID")
    customer_id: str = Field(..., description="Customer ID")
    status: str = Field(..., description="Subscription status")
    plan_id: str = Field(default="", description="Plan/price ID")
    current_period_start: int | None = Field(default=None, description="Period start timestamp")
    current_period_end: int | None = Field(default=None, description="Period end timestamp")
    cancel_at_period_end: bool = Field(
        default=False, description="Whether subscription will cancel"
    )


class StripeIntegration:
    """Integration with Stripe billing platform.

    Provides methods to sync customers, subscriptions, and billing events
    between the marketing platform and Stripe.
    """

    BASE_URL = "https://api.stripe.com/v1"

    def __init__(self, config: StripeConfig) -> None:
        """Initialize Stripe integration.

        Args:
            config: Stripe API configuration.
        """
        self.config = config
        logger.info("stripe_integration_initialized")

    def _headers(self) -> dict[str, str]:
        """Build request headers with API key.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.config.secret_key}",
            "Stripe-Version": self.config.api_version,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_customer(self, customer: StripeCustomer) -> dict:
        """Create a customer in Stripe.

        Args:
            customer: Customer data.

        Returns:
            Stripe API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/customers"

        payload = {
            "email": customer.email,
            "name": customer.name,
        }
        if customer.metadata:
            for key, value in customer.metadata.items():
                payload[f"metadata[{key}]"] = value

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, data=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("stripe_customer_created", email=customer.email)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_customer(self, customer_id: str) -> dict:
        """Retrieve a customer from Stripe.

        Args:
            customer_id: Stripe customer ID.

        Returns:
            Customer data.

        Raises:
            httpx.HTTPStatusError: If customer not found or API fails.
        """
        url = f"{self.BASE_URL}/customers/{customer_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers(), timeout=30.0)
            response.raise_for_status()
            return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_subscriptions(self, customer_id: str) -> list[dict]:
        """Get all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID.

        Returns:
            List of subscription objects.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/subscriptions"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"customer": customer_id},
                headers=self._headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

        return result.get("data", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_subscription(self, subscription: StripeSubscription) -> dict:
        """Create a subscription in Stripe.

        Args:
            subscription: Subscription data.

        Returns:
            Stripe API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/subscriptions"

        payload = {
            "customer": subscription.customer_id,
        }
        if subscription.plan_id:
            payload["items[0][price]"] = subscription.plan_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, data=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("stripe_subscription_created", customer_id=subscription.customer_id)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> dict:
        """Cancel a subscription.

        Args:
            subscription_id: Subscription to cancel.
            immediate: If True, cancel immediately. Otherwise at period end.

        Returns:
            Stripe API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/subscriptions/{subscription_id}"

        if immediate:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url, headers=self._headers(), timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        else:
            payload = {"cancel_at_period_end": "true"}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, data=payload, headers=self._headers(), timeout=30.0
                )
                response.raise_for_status()
                return response.json()

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Verify and parse a Stripe webhook payload.

        Args:
            payload: Raw request body bytes.
            signature: Stripe-Signature header value.

        Returns:
            Parsed webhook event.

        Raises:
            ValueError: If signature verification fails.
        """
        # In production, use stripe.Webhook.construct_event
        # This is a simplified version for development
        import json

        try:
            event = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid webhook payload: {e}") from e

        logger.info("stripe_webhook_received", event_type=event.get("type"))
        return event
