"""Shopify platform integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class ShopifyIntegration:
    """Integration with the Shopify e-commerce platform.

    Provides methods to interact with the Shopify Admin API for
    product management, order processing, and customer data.
    """

    def __init__(
        self,
        store_url: str | None = None,
        access_token: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Initialize the Shopify integration.

        Args:
            store_url: Shopify store URL (e.g., 'my-store.myshopify.com').
            access_token: Shopify access token for Admin API.
            api_key: Shopify API key.
            api_secret: Shopify API secret.

        Raises:
            ValueError: If required credentials are not provided.
        """
        settings = get_settings()
        self.settings = settings
        self.store_url = store_url or settings.shopify_store_url
        self.access_token = access_token or settings.shopify_access_token
        self.api_key = api_key or settings.shopify_api_key
        self.api_secret = api_secret or settings.shopify_api_secret
        self.api_version = settings.integrations.shopify.api_version

        if not self.store_url:
            raise ValueError("Shopify store URL is required")
        if not self.access_token:
            raise ValueError("Shopify access token is required")

        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Shopify-Access-Token": self.access_token,
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.settings.integrations.shopify.timeout),
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
    async def get_products(self, limit: int = 50, page_info: str | None = None) -> dict[str, Any]:
        """Fetch products from Shopify.

        Args:
            limit: Maximum number of products to fetch (max 250).
            page_info: Pagination cursor for next page.

        Returns:
            Shopify products response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        params: dict[str, Any] = {"limit": min(limit, 250)}
        if page_info:
            params["page_info"] = page_info

        response = await client.get("/products.json", params=params)
        response.raise_for_status()

        logger.info("Fetched products from Shopify", count=limit)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a single product from Shopify.

        Args:
            product_id: Shopify product ID.

        Returns:
            Shopify product data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(f"/products/{product_id}.json")
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_customers(self, limit: int = 50) -> dict[str, Any]:
        """Fetch customers from Shopify.

        Args:
            limit: Maximum number of customers to fetch.

        Returns:
            Shopify customers response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get("/customers.json", params={"limit": limit})
        response.raise_for_status()

        logger.info("Fetched customers from Shopify", count=limit)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_orders(self, status: str = "any", limit: int = 50) -> dict[str, Any]:
        """Fetch orders from Shopify.

        Args:
            status: Order status filter (open, closed, cancelled, any).
            limit: Maximum number of orders to fetch.

        Returns:
            Shopify orders response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(
            "/orders.json",
            params={"status": status, "limit": limit},
        )
        response.raise_for_status()

        logger.info("Fetched orders from Shopify", status=status, count=limit)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_draft_order(self, order_data: dict[str, Any]) -> dict[str, Any]:
        """Create a draft order in Shopify.

        Args:
            order_data: Draft order data.

        Returns:
            Created draft order data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.post(
            "/draft_orders.json",
            json={"draft_order": order_data},
        )
        response.raise_for_status()

        logger.info("Created draft order in Shopify")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_inventory(
        self,
        inventory_item_id: str,
        location_id: str,
        available: int,
    ) -> dict[str, Any]:
        """Update inventory levels in Shopify.

        Args:
            inventory_item_id: Shopify inventory item ID.
            location_id: Shopify location ID.
            available: New available quantity.

        Returns:
            Updated inventory data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.post(
            "/inventory_levels/set.json",
            json={
                "location_id": location_id,
                "inventory_item_id": inventory_item_id,
                "available": available,
            },
        )
        response.raise_for_status()

        logger.info(
            "Updated inventory in Shopify",
            inventory_item_id=inventory_item_id,
            available=available,
        )
        return response.json()
