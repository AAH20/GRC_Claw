"""WooCommerce platform integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class WooCommerceIntegration:
    """Integration with the WooCommerce e-commerce platform.

    Provides methods to interact with the WooCommerce REST API for
    product management, order processing, and customer data.
    """

    def __init__(
        self,
        store_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Initialize the WooCommerce integration.

        Args:
            store_url: WooCommerce store URL.
            api_key: WooCommerce consumer key.
            api_secret: WooCommerce consumer secret.

        Raises:
            ValueError: If required credentials are not provided.
        """
        settings = get_settings()
        self.settings = settings
        self.store_url = (store_url or settings.woocommerce_store_url).rstrip("/")
        self.api_key = api_key or settings.woocommerce_api_key
        self.api_secret = api_secret or settings.woocommerce_api_secret
        self.api_version = settings.integrations.woocommerce.api_version

        if not self.store_url:
            raise ValueError("WooCommerce store URL is required")
        if not self.api_key or not self.api_secret:
            raise ValueError("WooCommerce API key and secret are required")

        self.base_url = f"{self.store_url}/wp-json/wc/{self.api_version}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.api_key, self.api_secret),
                headers={"Content-Type": "application/json"},
                timeout=httpx.Timeout(self.settings.integrations.woocommerce.timeout),
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
    async def get_products(self, per_page: int = 50, page: int = 1) -> list[dict[str, Any]]:
        """Fetch products from WooCommerce.

        Args:
            per_page: Number of products per page (max 100).
            page: Page number.

        Returns:
            List of WooCommerce products.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(
            "/products",
            params={"per_page": min(per_page, 100), "page": page},
        )
        response.raise_for_status()

        logger.info("Fetched products from WooCommerce", per_page=per_page, page=page)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a single product from WooCommerce.

        Args:
            product_id: WooCommerce product ID.

        Returns:
            WooCommerce product data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(f"/products/{product_id}")
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_orders(
        self,
        status: str = "any",
        per_page: int = 50,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch orders from WooCommerce.

        Args:
            status: Order status filter.
            per_page: Number of orders per page.
            page: Page number.

        Returns:
            List of WooCommerce orders.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        params: dict[str, Any] = {"per_page": min(per_page, 100), "page": page}
        if status != "any":
            params["status"] = status

        response = await client.get("/orders", params=params)
        response.raise_for_status()

        logger.info("Fetched orders from WooCommerce", status=status, per_page=per_page)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_customers(self, per_page: int = 50, page: int = 1) -> list[dict[str, Any]]:
        """Fetch customers from WooCommerce.

        Args:
            per_page: Number of customers per page.
            page: Page number.

        Returns:
            List of WooCommerce customers.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(
            "/customers",
            params={"per_page": min(per_page, 100), "page": page},
        )
        response.raise_for_status()

        logger.info("Fetched customers from WooCommerce", per_page=per_page)
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_coupon(self, coupon_data: dict[str, Any]) -> dict[str, Any]:
        """Create a coupon in WooCommerce.

        Args:
            coupon_data: Coupon data (code, amount, discount_type, etc.).

        Returns:
            Created coupon data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.post("/coupons", json=coupon_data)
        response.raise_for_status()

        logger.info("Created coupon in WooCommerce", code=coupon_data.get("code"))
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_product(
        self,
        product_id: str,
        product_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a product in WooCommerce.

        Args:
            product_id: WooCommerce product ID.
            product_data: Product fields to update.

        Returns:
            Updated product data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.put(f"/products/{product_id}", json=product_data)
        response.raise_for_status()

        logger.info("Updated product in WooCommerce", product_id=product_id)
        return response.json()
