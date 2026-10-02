"""Shopify integration module.

Provides a client for interacting with the Shopify Admin API
to fetch and update product prices.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class ShopifyError(Exception):
    """Base exception for Shopify integration errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize ShopifyError.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class ShopifyClient:
    """Client for the Shopify Admin API.

    Handles authentication, rate limiting, and provides methods
    for common product and pricing operations.
    """

    def __init__(
        self,
        shop_url: str,
        access_token: str,
        api_version: str = "2024-01",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Shopify client.

        Args:
            shop_url: The Shopify store URL (e.g., https://store.myshopify.com).
            access_token: The Shopify access token.
            api_version: The Shopify API version to use.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If shop_url or access_token is empty.
        """
        if not shop_url:
            raise ValueError("shop_url is required")
        if not access_token:
            raise ValueError("access_token is required")

        self.shop_url = shop_url.rstrip("/")
        self.access_token = access_token
        self.api_version = api_version
        self._client = httpx.AsyncClient(
            base_url=f"{self.shop_url}/admin/api/{api_version}",
            headers={
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        logger.info("shopify_client_initialized", shop_url=self.shop_url, api_version=api_version)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Shopify API.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            **kwargs: Additional arguments for httpx.

        Returns:
            Parsed JSON response.

        Raises:
            ShopifyError: If the request fails.
        """
        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.error(
                "shopify_api_error",
                status_code=status_code,
                endpoint=endpoint,
                response=exc.response.text,
            )
            raise ShopifyError(
                f"Shopify API error: {exc.response.text}",
                status_code=status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("shopify_request_error", endpoint=endpoint, error=str(exc))
            raise ShopifyError(f"Shopify request failed: {exc}") from exc

    async def get_products(
        self,
        limit: int = 50,
        page_info: str | None = None,
    ) -> dict[str, Any]:
        """Fetch products from Shopify.

        Args:
            limit: Maximum number of products to fetch (max 250).
            page_info: Pagination cursor for next page.

        Returns:
            Products response with pagination info.

        Raises:
            ShopifyError: If the API request fails.
        """
        params: dict[str, Any] = {"limit": min(limit, 250)}
        if page_info:
            params["page_info"] = page_info

        logger.info("shopify_fetching_products", limit=limit)
        return await self._request("GET", "/products.json", params=params)

    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a single product by ID.

        Args:
            product_id: The Shopify product ID.

        Returns:
            Product data.

        Raises:
            ShopifyError: If the product is not found or request fails.
        """
        logger.info("shopify_fetching_product", product_id=product_id)
        return await self._request("GET", f"/products/{product_id}.json")

    async def update_variant_price(
        self,
        variant_id: str,
        price: float,
        compare_at_price: float | None = None,
    ) -> dict[str, Any]:
        """Update a product variant's price.

        Args:
            variant_id: The Shopify variant ID.
            price: New price for the variant.
            compare_at_price: Optional compare-at price for displaying discounts.

        Returns:
            Updated variant data.

        Raises:
            ShopifyError: If the update fails.
            ValueError: If variant_id is empty or price is invalid.
        """
        if not variant_id:
            raise ValueError("variant_id is required")
        if price <= 0:
            raise ValueError("price must be positive")

        variant_data: dict[str, Any] = {
            "variant": {
                "id": int(variant_id),
                "price": str(price),
            }
        }
        if compare_at_price is not None:
            variant_data["variant"]["compare_at_price"] = str(compare_at_price)

        logger.info(
            "shopify_updating_variant_price",
            variant_id=variant_id,
            new_price=price,
        )
        return await self._request(
            "PUT",
            f"/variants/{variant_id}.json",
            json=variant_data,
        )

    async def get_inventory_levels(
        self,
        inventory_item_ids: list[str],
    ) -> dict[str, Any]:
        """Fetch inventory levels for given inventory item IDs.

        Args:
            inventory_item_ids: List of Shopify inventory item IDs.

        Returns:
            Inventory levels data.

        Raises:
            ShopifyError: If the request fails.
        """
        if not inventory_item_ids:
            raise ValueError("inventory_item_ids cannot be empty")

        ids_param = ",".join(inventory_item_ids)
        logger.info(
            "shopify_fetching_inventory",
            item_count=len(inventory_item_ids),
        )
        return await self._request(
            "GET",
            "/inventory_levels.json",
            params={"inventory_item_ids": ids_param},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("shopify_client_closed")
