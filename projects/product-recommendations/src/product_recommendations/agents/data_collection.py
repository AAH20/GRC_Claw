"""Data Collection Agent - Fetches product catalogs, customer behavior, and order history."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class Platform(StrEnum):
    """Supported e-commerce platforms."""

    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"


class Product(BaseModel):
    """Product data model."""

    id: str
    title: str
    description: str = ""
    price: float
    currency: str = "USD"
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    inventory_quantity: int = 0
    image_url: str = ""
    platform: Platform
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerBehavior(BaseModel):
    """Customer behavior event model."""

    customer_id: str
    event_type: str  # view, click, add_to_cart, purchase
    product_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Order(BaseModel):
    """Order data model."""

    id: str
    customer_id: str
    items: list[dict[str, Any]]
    total: float
    currency: str = "USD"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class CollectionResult:
    """Result of a data collection operation."""

    products: list[Product] = field(default_factory=list)
    behaviors: list[CustomerBehavior] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    collected_at: datetime = field(default_factory=datetime.utcnow)


class DataCollectionAgent:
    """Agent responsible for collecting data from integrated e-commerce platforms.

    This agent fetches product catalogs, customer behavior events, and order
    history from Shopify, WooCommerce, and Magento platforms.
    """

    def __init__(
        self,
        shopify_config: dict[str, str] | None = None,
        woocommerce_config: dict[str, str] | None = None,
        magento_config: dict[str, str] | None = None,
        batch_size: int = 100,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize the Data Collection Agent.

        Args:
            shopify_config: Shopify API configuration.
            woocommerce_config: WooCommerce API configuration.
            magento_config: Magento API configuration.
            batch_size: Number of items to fetch per batch.
            max_retries: Maximum number of retry attempts for failed requests.
            timeout_seconds: Request timeout in seconds.
        """
        self._shopify_config = shopify_config or {}
        self._woocommerce_config = woocommerce_config or {}
        self._magento_config = magento_config or {}
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> DataCollectionAgent:
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout_seconds),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def collect_all(
        self,
        platforms: list[Platform] | None = None,
        since: datetime | None = None,
    ) -> CollectionResult:
        """Collect data from all configured platforms.

        Args:
            platforms: List of platforms to collect from. Defaults to all configured.
            since: Only collect data after this timestamp.

        Returns:
            CollectionResult with all collected data.
        """
        platforms = platforms or self._configured_platforms()
        result = CollectionResult()

        tasks = [self._collect_platform(p, since) for p in platforms]
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        for platform, platform_result in zip(platforms, platform_results, strict=True):
            if isinstance(platform_result, Exception):
                logger.error(
                    "Platform collection failed",
                    platform=platform.value,
                    error=str(platform_result),
                )
                result.errors.append(f"{platform.value}: {platform_result}")
            else:
                result.products.extend(platform_result.products)
                result.behaviors.extend(platform_result.behaviors)
                result.orders.extend(platform_result.orders)
                result.errors.extend(platform_result.errors)

        logger.info(
            "Data collection complete",
            products=len(result.products),
            behaviors=len(result.behaviors),
            orders=len(result.orders),
            errors=len(result.errors),
        )
        return result

    async def collect_products(
        self,
        platform: Platform,
        since: datetime | None = None,
    ) -> list[Product]:
        """Collect products from a specific platform.

        Args:
            platform: The platform to collect from.
            since: Only collect products updated after this timestamp.

        Returns:
            List of collected products.
        """
        result = await self._collect_platform(platform, since)
        return result.products

    async def collect_behaviors(
        self,
        platform: Platform,
        customer_id: str | None = None,
        since: datetime | None = None,
    ) -> list[CustomerBehavior]:
        """Collect customer behavior events.

        Args:
            platform: The platform to collect from.
            customer_id: Optional customer ID to filter by.
            since: Only collect events after this timestamp.

        Returns:
            List of customer behavior events.
        """
        result = await self._collect_platform(platform, since)
        behaviors = result.behaviors
        if customer_id:
            behaviors = [b for b in behaviors if b.customer_id == customer_id]
        return behaviors

    async def collect_orders(
        self,
        platform: Platform,
        customer_id: str | None = None,
        since: datetime | None = None,
    ) -> list[Order]:
        """Collect order history.

        Args:
            platform: The platform to collect from.
            customer_id: Optional customer ID to filter by.
            since: Only collect orders after this timestamp.

        Returns:
            List of orders.
        """
        result = await self._collect_platform(platform, since)
        orders = result.orders
        if customer_id:
            orders = [o for o in orders if o.customer_id == customer_id]
        return orders

    def _configured_platforms(self) -> list[Platform]:
        """Get list of configured platforms.

        Returns:
            List of platforms that have configuration.
        """
        platforms: list[Platform] = []
        if self._shopify_config:
            platforms.append(Platform.SHOPIFY)
        if self._woocommerce_config:
            platforms.append(Platform.WOOCOMMERCE)
        if self._magento_config:
            platforms.append(Platform.MAGENTO)
        return platforms

    async def _collect_platform(
        self,
        platform: Platform,
        since: datetime | None = None,
    ) -> CollectionResult:
        """Collect data from a single platform.

        Args:
            platform: The platform to collect from.
            since: Only collect data after this timestamp.

        Returns:
            CollectionResult for the platform.
        """
        if platform == Platform.SHOPIFY:
            return await self._collect_shopify(since)
        elif platform == Platform.WOOCOMMERCE:
            return await self._collect_woocommerce(since)
        elif platform == Platform.MAGENTO:
            return await self._collect_magento(since)
        return CollectionResult(errors=[f"Unknown platform: {platform}"])

    async def _collect_shopify(self, since: datetime | None = None) -> CollectionResult:
        """Collect data from Shopify.

        Args:
            since: Only collect data after this timestamp.

        Returns:
            CollectionResult with Shopify data.
        """
        result = CollectionResult()
        if not self._shopify_config or not self._http_client:
            result.errors.append("Shopify not configured")
            return result

        try:
            products = await self._fetch_shopify_products(since)
            result.products.extend(products)
        except Exception as exc:
            logger.error("Failed to collect Shopify products", error=str(exc))
            result.errors.append(f"shopify_products: {exc}")

        return result

    async def _collect_woocommerce(self, since: datetime | None = None) -> CollectionResult:
        """Collect data from WooCommerce.

        Args:
            since: Only collect data after this timestamp.

        Returns:
            CollectionResult with WooCommerce data.
        """
        result = CollectionResult()
        if not self._woocommerce_config or not self._http_client:
            result.errors.append("WooCommerce not configured")
            return result

        try:
            products = await self._fetch_woocommerce_products(since)
            result.products.extend(products)
        except Exception as exc:
            logger.error("Failed to collect WooCommerce products", error=str(exc))
            result.errors.append(f"woocommerce_products: {exc}")

        return result

    async def _collect_magento(self, since: datetime | None = None) -> CollectionResult:
        """Collect data from Magento.

        Args:
            since: Only collect data after this timestamp.

        Returns:
            CollectionResult with Magento data.
        """
        result = CollectionResult()
        if not self._magento_config or not self._http_client:
            result.errors.append("Magento not configured")
            return result

        try:
            products = await self._fetch_magento_products(since)
            result.products.extend(products)
        except Exception as exc:
            logger.error("Failed to collect Magento products", error=str(exc))
            result.errors.append(f"magento_products: {exc}")

        return result

    async def _fetch_shopify_products(self, since: datetime | None = None) -> list[Product]:
        """Fetch products from Shopify API.

        Args:
            since: Only fetch products updated after this timestamp.

        Returns:
            List of Shopify products.
        """
        if not self._http_client:
            return []

        base_url = self._shopify_config.get("shop_url", "")
        access_token = self._shopify_config.get("access_token", "")
        api_version = self._shopify_config.get("api_version", "2024-01")

        url = f"{base_url}/admin/api/{api_version}/products.json"
        headers = {"X-Shopify-Access-Token": access_token}
        params: dict[str, Any] = {"limit": self._batch_size}
        if since:
            params["updated_at_min"] = since.isoformat()

        response = await self._http_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        products: list[Product] = []
        for item in data.get("products", []):
            variants = item.get("variants", [])
            price = float(variants[0].get("price", 0)) if variants else 0.0
            inventory = (
                sum(int(v.get("inventory_quantity", 0)) for v in variants)
                if variants
                else 0
            )
            images = item.get("images", [])
            product = Product(
                id=str(item.get("id", "")),
                title=item.get("title", ""),
                description=item.get("body_html", ""),
                price=price,
                category=item.get("product_type", ""),
                tags=item.get("tags", "").split(", ") if item.get("tags") else [],
                inventory_quantity=inventory,
                image_url=images[0].get("src", "") if images else "",
                platform=Platform.SHOPIFY,
                metadata={"vendor": item.get("vendor", ""), "handle": item.get("handle", "")},
            )
            products.append(product)

        return products

    async def _fetch_woocommerce_products(self, since: datetime | None = None) -> list[Product]:
        """Fetch products from WooCommerce API.

        Args:
            since: Only fetch products updated after this timestamp.

        Returns:
            List of WooCommerce products.
        """
        if not self._http_client:
            return []

        base_url = self._woocommerce_config.get("url", "")
        consumer_key = self._woocommerce_config.get("consumer_key", "")
        consumer_secret = self._woocommerce_config.get("consumer_secret", "")

        url = f"{base_url}/wp-json/wc/v3/products"
        params: dict[str, Any] = {
            "per_page": self._batch_size,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
        }
        if since:
            params["after"] = since.isoformat()

        response = await self._http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        products: list[Product] = []
        for item in data:
            images = item.get("images", [])
            product = Product(
                id=str(item.get("id", "")),
                title=item.get("name", ""),
                description=item.get("description", ""),
                price=float(item.get("price", 0) or 0),
                category=(
                    item.get("categories", [{}])[0].get("name", "")
                    if item.get("categories")
                    else ""
                ),
                tags=[t.get("name", "") for t in item.get("tags", [])],
                inventory_quantity=int(item.get("stock_quantity", 0) or 0),
                image_url=images[0].get("src", "") if images else "",
                platform=Platform.WOOCOMMERCE,
                metadata={"sku": item.get("sku", ""), "slug": item.get("slug", "")},
            )
            products.append(product)

        return products

    async def _fetch_magento_products(self, since: datetime | None = None) -> list[Product]:
        """Fetch products from Magento API.

        Args:
            since: Only fetch products updated after this timestamp.

        Returns:
            List of Magento products.
        """
        if not self._http_client:
            return []

        base_url = self._magento_config.get("url", "")
        access_token = self._magento_config.get("access_token", "")

        url = f"{base_url}/rest/V1/products"
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, Any] = {
            "searchCriteria[pageSize]": self._batch_size,
        }
        if since:
            params["searchCriteria[filterGroups][0][filters][0][field]"] = "updated_at"
            params["searchCriteria[filterGroups][0][filters][0][value]"] = since.isoformat()
            params["searchCriteria[filterGroups][0][filters][0][conditionType]"] = "gt"

        response = await self._http_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        products: list[Product] = []
        for item in data.get("items", []):
            extension = item.get("extension_attributes", {})
            product = Product(
                id=str(item.get("id", "")),
                title=item.get("name", ""),
                price=float(item.get("price", 0) or 0),
                platform=Platform.MAGENTO,
                metadata={
                    "sku": item.get("sku", ""),
                    "status": item.get("status", 0),
                    "visibility": item.get("visibility", ""),
                    "custom_attributes": extension.get("custom_attributes", []),
                },
            )
            products.append(product)

        return products
