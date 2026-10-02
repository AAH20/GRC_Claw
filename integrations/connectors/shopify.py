"""Shopify API connector."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, parse_qs, urlparse

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError

logger = logging.getLogger(__name__)


class ShopifyConnector(BaseConnector):
    """Shopify Admin API connector.

    Supports products, orders, customers, inventory, and webhooks.
    Uses API key + password (private apps) or OAuth 2.0 (public apps).
    """

    API_VERSION = "2024-01"

    def __init__(
        self,
        shop_domain: str,
        api_key: str,
        api_password: str,
        *,
        api_version: str = API_VERSION,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        self.shop_domain = shop_domain
        self.api_key = api_key
        self.api_password = api_password
        self.api_version = api_version

        if config is None:
            config = ConnectorConfig(
                base_url=f"https://{shop_domain}/admin/api/{api_version}",
                extra_headers={
                    "X-Shopify-Access-Token": api_password,
                },
            )
        super().__init__(config)

    async def authenticate(self) -> None:
        """Authenticate with Shopify using API key + password."""
        self._state = self._state.AUTHENTICATING
        try:
            response = await self.get("/shop.json", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid Shopify credentials")
            self._auth_token = self.api_password
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"Shopify authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Shopify private app tokens don't expire."""
        logger.info("Shopify private app tokens do not expire")

    async def health_check(self) -> bool:
        """Check if Shopify API is reachable."""
        try:
            response = await self.get("/shop.json", auth=False)
            return response.is_success
        except Exception:
            return False

    # ─── Shop ───────────────────────────────────────────────────────────

    async def get_shop(self) -> Dict[str, Any]:
        """Get shop details.

        Returns:
            Shop information.
        """
        response = await self.get("/shop.json", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("shop", {})
        return {}

    # ─── Products ───────────────────────────────────────────────────────

    async def get_products(
        self,
        *,
        limit: int = 50,
        page_info: Optional[str] = None,
        collection_id: Optional[str] = None,
        product_type: Optional[str] = None,
        status: str = "active",
    ) -> Dict[str, Any]:
        """Get products.

        Args:
            limit: Maximum number of products (max 250).
            page_info: Pagination cursor.
            collection_id: Filter by collection.
            product_type: Filter by product type.
            status: Filter by status (active, draft, archived).

        Returns:
            Paginated response with 'products'.
        """
        params: Dict[str, Any] = {
            "limit": min(limit, 250),
            "status": status,
        }
        if page_info:
            params["page_info"] = page_info
        if collection_id:
            params["collection_id"] = collection_id
        if product_type:
            params["product_type"] = product_type

        response = await self.get("/products.json", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a single product.

        Args:
            product_id: The product ID.

        Returns:
            Product details.
        """
        response = await self.get(f"/products/{product_id}.json", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("product", {})
        return {}

    async def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product.

        Args:
            data: Product data (title, body_html, vendor, product_type, etc.).

        Returns:
            Created product.
        """
        response = await self.post("/products.json", data={"product": data}, auth=False)
        if isinstance(response.data, dict):
            return response.data.get("product", {})
        return {}

    async def update_product(self, product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product.

        Args:
            product_id: The product ID.
            data: Fields to update.

        Returns:
            Updated product.
        """
        response = await self.put(
            f"/products/{product_id}.json",
            data={"product": data},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("product", {})
        return {}

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product.

        Args:
            product_id: The product ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/products/{product_id}.json", auth=False)
        return response.is_success

    # ─── Orders ─────────────────────────────────────────────────────────

    async def get_orders(
        self,
        *,
        limit: int = 50,
        status: str = "any",
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get orders.

        Args:
            limit: Maximum number of orders.
            status: Filter by status (open, closed, cancelled, any).
            created_at_min: Minimum creation date (ISO 8601).
            created_at_max: Maximum creation date (ISO 8601).
            financial_status: Filter by financial status.
            fulfillment_status: Filter by fulfillment status.

        Returns:
            Paginated response with 'orders'.
        """
        params: Dict[str, Any] = {
            "limit": min(limit, 250),
            "status": status,
        }
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max
        if financial_status:
            params["financial_status"] = financial_status
        if fulfillment_status:
            params["fulfillment_status"] = fulfillment_status

        response = await self.get("/orders.json", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a single order.

        Args:
            order_id: The order ID.

        Returns:
            Order details.
        """
        response = await self.get(f"/orders/{order_id}.json", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("order", {})
        return {}

    async def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order.

        Args:
            data: Order data (line_items, customer, financial_status, etc.).

        Returns:
            Created order.
        """
        response = await self.post("/orders.json", data={"order": data}, auth=False)
        if isinstance(response.data, dict):
            return response.data.get("order", {})
        return {}

    async def update_order(self, order_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing order.

        Args:
            order_id: The order ID.
            data: Fields to update.

        Returns:
            Updated order.
        """
        response = await self.put(
            f"/orders/{order_id}.json",
            data={"order": data},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("order", {})
        return {}

    async def cancel_order(self, order_id: str, *, reason: str = "customer") -> Dict[str, Any]:
        """Cancel an order.

        Args:
            order_id: The order ID.
            reason: Cancellation reason.

        Returns:
            Cancelled order.
        """
        response = await self.post(
            f"/orders/{order_id}/cancel.json",
            data={"reason": reason},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("order", {})
        return {}

    # ─── Customers ──────────────────────────────────────────────────────

    async def get_customers(
        self,
        *,
        limit: int = 50,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get customers.

        Args:
            limit: Maximum number of customers.
            created_at_min: Minimum creation date.
            created_at_max: Maximum creation date.

        Returns:
            Paginated response with 'customers'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 250)}
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max

        response = await self.get("/customers.json", params=params, auth=False)
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
        response = await self.get(f"/customers/{customer_id}.json", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("customer", {})
        return {}

    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer.

        Args:
            data: Customer data (first_name, last_name, email, phone, etc.).

        Returns:
            Created customer.
        """
        response = await self.post("/customers.json", data={"customer": data}, auth=False)
        if isinstance(response.data, dict):
            return response.data.get("customer", {})
        return {}

    async def update_customer(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer.

        Args:
            customer_id: The customer ID.
            data: Fields to update.

        Returns:
            Updated customer.
        """
        response = await self.put(
            f"/customers/{customer_id}.json",
            data={"customer": data},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("customer", {})
        return {}

    # ─── Inventory ──────────────────────────────────────────────────────

    async def get_inventory_levels(
        self,
        *,
        inventory_item_ids: Optional[List[str]] = None,
        location_ids: Optional[List[str]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get inventory levels.

        Args:
            inventory_item_ids: Filter by inventory item IDs.
            location_ids: Filter by location IDs.
            limit: Maximum number of results.

        Returns:
            Paginated response with 'inventory_levels'.
        """
        params: Dict[str, Any] = {"limit": min(limit, 250)}
        if inventory_item_ids:
            params["inventory_item_ids"] = ",".join(inventory_item_ids)
        if location_ids:
            params["location_ids"] = ",".join(location_ids)

        response = await self.get("/inventory_levels.json", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def set_inventory_level(
        self,
        inventory_item_id: str,
        location_id: str,
        available: int,
    ) -> Dict[str, Any]:
        """Set inventory level for an item at a location.

        Args:
            inventory_item_id: The inventory item ID.
            location_id: The location ID.
            available: Available quantity.

        Returns:
            Updated inventory level.
        """
        response = await self.post(
            "/inventory_levels/set.json",
            data={
                "inventory_item_id": inventory_item_id,
                "location_id": location_id,
                "available": available,
            },
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("inventory_level", {})
        return {}

    # ─── Webhooks ───────────────────────────────────────────────────────

    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all webhooks.

        Returns:
            List of webhook dictionaries.
        """
        response = await self.get("/webhooks.json", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("webhooks", [])
        return []

    async def create_webhook(self, topic: str, address: str, *, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new webhook.

        Args:
            topic: Webhook topic (e.g., 'orders/create', 'products/update').
            address: The callback URL.
            fields: Fields to include in the webhook payload.

        Returns:
            Created webhook.
        """
        data: Dict[str, Any] = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json",
            }
        }
        if fields:
            data["webhook"]["fields"] = fields

        response = await self.post("/webhooks.json", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data.get("webhook", {})
        return {}

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook.

        Args:
            webhook_id: The webhook ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/webhooks/{webhook_id}.json", auth=False)
        return response.is_success

    # ─── GraphQL ────────────────────────────────────────────────────────

    async def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Query variables.

        Returns:
            GraphQL response data.
        """
        data: Dict[str, Any] = {"query": query}
        if variables:
            data["variables"] = variables

        response = await self.post(
            "/graphql.json",
            data=data,
            headers={"Content-Type": "application/json"},
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Webhook Verification ───────────────────────────────────────────

    @staticmethod
    def verify_webhook_hmac(data: bytes, hmac_header: str, secret: str) -> bool:
        """Verify Shopify webhook HMAC signature.

        Args:
            data: Raw request body bytes.
            hmac_header: The X-Shopify-Hmac-Sha256 header value.
            secret: The webhook secret (app credentials).

        Returns:
            True if the HMAC is valid.
        """
        digest = hmac.new(
            secret.encode("utf-8"),
            data,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(digest, hmac_header)
