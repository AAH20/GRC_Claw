"""Stripe API connector."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError

logger = logging.getLogger(__name__)


class StripeConnector(BaseConnector):
    """Stripe API connector.

    Supports customers, charges, subscriptions, invoices, products, and webhooks.
    Uses API key for authentication.
    """

    DEFAULT_BASE_URL = "https://api.stripe.com/v1"

    def __init__(
        self,
        api_key: str,
        *,
        webhook_secret: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                api_key=api_key,
            )
        super().__init__(config)
        self._api_key = api_key
        self._webhook_secret = webhook_secret

    async def authenticate(self) -> None:
        """Authenticate with Stripe using the API key."""
        self._state = self._state.AUTHENTICATING
        try:
            response = await self.get("/balance", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid Stripe API key")
            self._auth_token = self._api_key
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"Stripe authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Stripe API keys don't expire."""
        logger.info("Stripe API keys do not expire")

    async def health_check(self) -> bool:
        """Check if Stripe API is reachable."""
        try:
            response = await self.get("/balance", auth=False)
            return response.is_success
        except Exception:
            return False

    def _auth_headers(self) -> Dict[str, str]:
        """Get auth headers for Stripe."""
        if self._api_key:
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}

    # ─── Customers ──────────────────────────────────────────────────────

    async def get_customers(
        self,
        *,
        limit: int = 100,
        starting_after: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get customers.

        Args:
            limit: Maximum number of customers.
            starting_after: Pagination cursor.
            email: Filter by email.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if starting_after:
            params["starting_after"] = starting_after
        if email:
            params["email"] = email

        response = await self.get("/customers", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get a single customer.

        Args:
            customer_id: The customer ID.

        Returns:
            Customer details.
        """
        response = await self.get(f"/customers/{customer_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer.

        Args:
            data: Customer data (email, name, description, metadata, etc.).

        Returns:
            Created customer.
        """
        response = await self.post("/customers", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_customer(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer.

        Args:
            customer_id: The customer ID.
            data: Fields to update.

        Returns:
            Updated customer.
        """
        response = await self.post(f"/customers/{customer_id}", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer.

        Args:
            customer_id: The customer ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/customers/{customer_id}", auth=False)
        return response.is_success

    # ─── Charges ────────────────────────────────────────────────────────

    async def get_charges(
        self,
        *,
        limit: int = 100,
        starting_after: Optional[str] = None,
        customer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get charges.

        Args:
            limit: Maximum number of charges.
            starting_after: Pagination cursor.
            customer: Filter by customer ID.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if starting_after:
            params["starting_after"] = starting_after
        if customer:
            params["customer"] = customer

        response = await self.get("/charges", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_charge(self, charge_id: str) -> Dict[str, Any]:
        """Get a single charge.

        Args:
            charge_id: The charge ID.

        Returns:
            Charge details.
        """
        response = await self.get(f"/charges/{charge_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_charge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new charge.

        Args:
            data: Charge data (amount, currency, source, description, etc.).

        Returns:
            Created charge.
        """
        response = await self.post("/charges", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def capture_charge(self, charge_id: str, *, amount: Optional[int] = None) -> Dict[str, Any]:
        """Capture a previously authorized charge.

        Args:
            charge_id: The charge ID.
            amount: Amount to capture (partial capture).

        Returns:
            Captured charge.
        """
        data: Dict[str, Any] = {}
        if amount:
            data["amount"] = amount

        response = await self.post(f"/charges/{charge_id}/capture", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def refund_charge(
        self,
        charge_id: str,
        *,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refund a charge.

        Args:
            charge_id: The charge ID.
            amount: Amount to refund (partial refund).
            reason: Refund reason (duplicate, fraudulent, requested_by_customer).

        Returns:
            Refund details.
        """
        data: Dict[str, Any] = {}
        if amount:
            data["amount"] = amount
        if reason:
            data["reason"] = reason

        response = await self.post("/refunds", data={"charge": charge_id, **data}, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Subscriptions ──────────────────────────────────────────────────

    async def get_subscriptions(
        self,
        *,
        limit: int = 100,
        status: Optional[str] = None,
        customer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get subscriptions.

        Args:
            limit: Maximum number of subscriptions.
            status: Filter by status (active, canceled, past_due, etc.).
            customer: Filter by customer ID.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if status:
            params["status"] = status
        if customer:
            params["customer"] = customer

        response = await self.get("/subscriptions", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get a single subscription.

        Args:
            subscription_id: The subscription ID.

        Returns:
            Subscription details.
        """
        response = await self.get(f"/subscriptions/{subscription_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_subscription(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new subscription.

        Args:
            data: Subscription data (customer, items, metadata, etc.).

        Returns:
            Created subscription.
        """
        response = await self.post("/subscriptions", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_subscription(self, subscription_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing subscription.

        Args:
            subscription_id: The subscription ID.
            data: Fields to update.

        Returns:
            Updated subscription.
        """
        response = await self.post(f"/subscriptions/{subscription_id}", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def cancel_subscription(self, subscription_id: str, *, at_period_end: bool = False) -> Dict[str, Any]:
        """Cancel a subscription.

        Args:
            subscription_id: The subscription ID.
            at_period_end: Whether to cancel at the end of the billing period.

        Returns:
            Canceled subscription.
        """
        if at_period_end:
            response = await self.post(
                f"/subscriptions/{subscription_id}",
                data={"cancel_at_period_end": True},
                auth=False,
            )
        else:
            response = await self.delete(f"/subscriptions/{subscription_id}", auth=False)

        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Invoices ───────────────────────────────────────────────────────

    async def get_invoices(
        self,
        *,
        limit: int = 100,
        status: Optional[str] = None,
        customer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get invoices.

        Args:
            limit: Maximum number of invoices.
            status: Filter by status (draft, open, paid, uncollectible, void).
            customer: Filter by customer ID.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if status:
            params["status"] = status
        if customer:
            params["customer"] = customer

        response = await self.get("/invoices", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get a single invoice.

        Args:
            invoice_id: The invoice ID.

        Returns:
            Invoice details.
        """
        response = await self.get(f"/invoices/{invoice_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice.

        Args:
            data: Invoice data (customer, auto_advance, collection_method, etc.).

        Returns:
            Created invoice.
        """
        response = await self.post("/invoices", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def pay_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Pay an invoice.

        Args:
            invoice_id: The invoice ID.

        Returns:
            Paid invoice.
        """
        response = await self.post(f"/invoices/{invoice_id}/pay", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Products & Prices ──────────────────────────────────────────────

    async def get_products(
        self,
        *,
        limit: int = 100,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get products.

        Args:
            limit: Maximum number of products.
            active: Filter by active status.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if active is not None:
            params["active"] = str(active).lower()

        response = await self.get("/products", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product.

        Args:
            data: Product data (name, description, metadata, etc.).

        Returns:
            Created product.
        """
        response = await self.post("/products", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_prices(
        self,
        *,
        limit: int = 100,
        product: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get prices.

        Args:
            limit: Maximum number of prices.
            product: Filter by product ID.

        Returns:
            Paginated response with 'data'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if product:
            params["product"] = product

        response = await self.get("/prices", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_price(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new price.

        Args:
            data: Price data (product, unit_amount, currency, recurring, etc.).

        Returns:
            Created price.
        """
        response = await self.post("/prices", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Payment Intents ────────────────────────────────────────────────

    async def create_payment_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment intent.

        Args:
            data: Payment intent data (amount, currency, customer, etc.).

        Returns:
            Created payment intent.
        """
        response = await self.post("/payment_intents", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def confirm_payment_intent(self, payment_intent_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Confirm a payment intent.

        Args:
            payment_intent_id: The payment intent ID.
            data: Additional confirmation data.

        Returns:
            Confirmed payment intent.
        """
        response = await self.post(
            f"/payment_intents/{payment_intent_id}/confirm",
            data=data or {},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Webhooks ───────────────────────────────────────────────────────

    async def get_webhook_endpoints(self) -> Dict[str, Any]:
        """Get all webhook endpoints.

        Returns:
            Paginated response with 'data'.
        """
        response = await self.get("/webhook_endpoints", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_webhook_endpoint(self, url: str, events: List[str], *, description: str = "") -> Dict[str, Any]:
        """Create a new webhook endpoint.

        Args:
            url: The callback URL.
            events: List of event types to subscribe to.
            description: Optional description.

        Returns:
            Created webhook endpoint.
        """
        data: Dict[str, Any] = {
            "url": url,
            "enabled_events": events,
        }
        if description:
            data["description"] = description

        response = await self.post("/webhook_endpoints", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def delete_webhook_endpoint(self, webhook_endpoint_id: str) -> bool:
        """Delete a webhook endpoint.

        Args:
            webhook_endpoint_id: The webhook endpoint ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/webhook_endpoints/{webhook_endpoint_id}", auth=False)
        return response.is_success

    # ─── Webhook Verification ───────────────────────────────────────────

    def verify_webhook_signature(self, payload: bytes, sig_header: str, tolerance: int = 300) -> Dict[str, Any]:
        """Verify Stripe webhook signature.

        Args:
            payload: Raw request body bytes.
            sig_header: The Stripe-Signature header value.
            tolerance: Maximum age of the webhook in seconds.

        Returns:
            Parsed webhook event.

        Raises:
            ConnectorError: If signature verification fails.
        """
        if not self._webhook_secret:
            raise ConnectorError("Webhook secret not configured")

        try:
            timestamp, signatures = self._parse_signature_header(sig_header)
        except ValueError as e:
            raise ConnectorError(f"Invalid signature header: {e}") from e

        # Check timestamp tolerance
        if tolerance > 0 and (time.time() - timestamp) > tolerance:
            raise ConnectorError("Webhook timestamp too old")

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected_sig = hmac.new(
            self._webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Verify signature
        for sig in signatures:
            if hmac.compare_digest(sig, expected_sig):
                import json
                return json.loads(payload)

        raise ConnectorError("Webhook signature verification failed")

    @staticmethod
    def _parse_signature_header(sig_header: str) -> tuple[int, List[str]]:
        """Parse the Stripe-Signature header.

        Returns:
            Tuple of (timestamp, list of signatures).
        """
        items = sig_header.split(",")
        timestamp = 0
        signatures: List[str] = []

        for item in items:
            key, _, value = item.partition("=")
            if key == "t":
                timestamp = int(value)
            elif key == "v1":
                signatures.append(value)

        if not timestamp or not signatures:
            raise ValueError("Missing timestamp or signature")

        return timestamp, signatures
