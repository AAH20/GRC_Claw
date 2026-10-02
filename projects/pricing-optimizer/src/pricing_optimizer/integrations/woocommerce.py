"""WooCommerce integration module.

Provides a client for interacting with the WooCommerce REST API
to fetch and update product prices.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class WooCommerceError(Exception):
    """Base exception for WooCommerce integration errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize WooCommerceError.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class WooCommerceClient:
    """Client for the WooCommerce REST API.

    Handles authentication via consumer key/secret, rate limiting,
    and provides methods for product and pricing operations.
    """

    def __init__(
        self,
        url: str,
        consumer_key: str,
        consumer_secret: str,
        api_version: str = "v3",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the WooCommerce client.

        Args:
            url: The WooCommerce store URL.
            consumer_key: The WooCommerce consumer key.
            consumer_secret: The WooCommerce consumer secret.
            api_version: The WooCommerce API version.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If any required parameter is empty.
        """
        if not url:
            raise ValueError("url is required")
        if not consumer_key:
            raise ValueError("consumer_key is required")
        if not consumer_secret:
            raise ValueError("consumer_secret is required")

        self.url = url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = api_version
        self._client = httpx.AsyncClient(
            base_url=f"{self.url}/wp-json/wc/{api_version}",
            auth=(self.consumer_key, self.consumer_secret),
            timeout=timeout,
        )
        logger.info(
            "woocommerce_client_initialized",
            url=self.url,
            api_version=api_version,
        )

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
        """Make an authenticated request to the WooCommerce API.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            **kwargs: Additional arguments for httpx.

        Returns:
            Parsed JSON response.

        Raises:
            WooCommerceError: If the request fails.
        """
        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.error(
                "woocommerce_api_error",
                status_code=status_code,
                endpoint=endpoint,
                response=exc.response.text,
            )
            raise WooCommerceError(
                f"WooCommerce API error: {exc.response.text}",
                status_code=status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("woocommerce_request_error", endpoint=endpoint, error=str(exc))
            raise WooCommerceError(f"WooCommerce request failed: {exc}") from exc

    async def get_products(
        self,
        per_page: int = 50,
        page: int = 1,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch products from WooCommerce.

        Args:
            per_page: Number of products per page (max 100).
            page: Page number.
            category: Optional category ID filter.

        Returns:
            List of product data.

        Raises:
            WooCommerceError: If the API request fails.
        """
        params: dict[str, Any] = {
            "per_page": min(per_page, 100),
            "page": page,
        }
        if category:
            params["category"] = category

        logger.info("woocommerce_fetching_products", per_page=per_page, page=page)
        result = await self._request("GET", "/products", params=params)
        return result if isinstance(result, list) else []

    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a single product by ID.

        Args:
            product_id: The WooCommerce product ID.

        Returns:
            Product data.

        Raises:
            WooCommerceError: If the product is not found or request fails.
        """
        logger.info("woocommerce_fetching_product", product_id=product_id)
        return await self._request("GET", f"/products/{product_id}")

    async def update_product_price(
        self,
        product_id: str,
        regular_price: float,
        sale_price: float | None = None,
    ) -> dict[str, Any]:
        """Update a product's price.

        Args:
            product_id: The WooCommerce product ID.
            regular_price: New regular price.
            sale_price: Optional sale price.

        Returns:
            Updated product data.

        Raises:
            WooCommerceError: If the update fails.
            ValueError: If product_id is empty or price is invalid.
        """
        if not product_id:
            raise ValueError("product_id is required")
        if regular_price <= 0:
            raise ValueError("regular_price must be positive")

        product_data: dict[str, Any] = {
            "regular_price": str(regular_price),
        }
        if sale_price is not None:
            if sale_price <= 0:
                raise ValueError("sale_price must be positive")
            product_data["sale_price"] = str(sale_price)

        logger.info(
            "woocommerce_updating_product_price",
            product_id=product_id,
            new_price=regular_price,
        )
        return await self._request(
            "PUT",
            f"/products/{product_id}",
            json=product_data,
        )

    async def batch_update_prices(
        self,
        updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Batch update multiple product prices.

        Args:
            updates: List of dicts with 'id', 'regular_price', and optional 'sale_price'.

        Returns:
            Batch operation results.

        Raises:
            WooCommerceError: If the batch update fails.
            ValueError: If updates list is empty.
        """
        if not updates:
            raise ValueError("updates list cannot be empty")

        logger.info("woocommerce_batch_updating_prices", count=len(updates))
        return await self._request(
            "POST",
            "/products/batch",
            json={"update": updates},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("woocommerce_client_closed")
