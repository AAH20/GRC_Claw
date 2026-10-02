"""Stripe integration module.

Provides a client for interacting with the Stripe API
to manage prices and products.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class StripeError(Exception):
    """Base exception for Stripe integration errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize StripeError.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class StripeClient:
    """Client for the Stripe API.

    Handles authentication, provides methods for price and product
    management. Uses the newer Stripe Prices API.
    """

    def __init__(
        self,
        api_key: str,
        api_version: str = "2023-10-16",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Stripe client.

        Args:
            api_key: The Stripe secret API key.
            api_version: The Stripe API version.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If api_key is empty.
        """
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.api_version = api_version
        self._client = httpx.AsyncClient(
            base_url="https://api.stripe.com/v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Stripe-Version": self.api_version,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=timeout,
        )
        logger.info("stripe_client_initialized", api_version=api_version)

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
        """Make an authenticated request to the Stripe API.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            **kwargs: Additional arguments for httpx.

        Returns:
            Parsed JSON response.

        Raises:
            StripeError: If the request fails.
        """
        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.error(
                "stripe_api_error",
                status_code=status_code,
                endpoint=endpoint,
                response=exc.response.text,
            )
            raise StripeError(
                f"Stripe API error: {exc.response.text}",
                status_code=status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("stripe_request_error", endpoint=endpoint, error=str(exc))
            raise StripeError(f"Stripe request failed: {exc}") from exc

    async def list_prices(
        self,
        limit: int = 100,
        starting_after: str | None = None,
        active: bool | None = None,
    ) -> dict[str, Any]:
        """List prices from Stripe.

        Args:
            limit: Maximum number of prices to return.
            starting_after: Pagination cursor.
            active: Filter by active status.

        Returns:
            Prices list response with pagination.

        Raises:
            StripeError: If the API request fails.
        """
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if starting_after:
            params["starting_after"] = starting_after
        if active is not None:
            params["active"] = str(active).lower()

        logger.info("stripe_listing_prices", limit=limit)
        return await self._request("GET", "/prices", params=params)

    async def get_price(self, price_id: str) -> dict[str, Any]:
        """Fetch a single price by ID.

        Args:
            price_id: The Stripe price ID.

        Returns:
            Price data.

        Raises:
            StripeError: If the price is not found or request fails.
        """
        logger.info("stripe_fetching_price", price_id=price_id)
        return await self._request("GET", f"/prices/{price_id}")

    async def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str = "usd",
        metadata: dict[str, str] | None = None,
        recurring: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new price for a product.

        Args:
            product_id: The Stripe product ID.
            unit_amount: Price amount in cents.
            currency: Three-letter ISO currency code.
            metadata: Optional metadata key-value pairs.
            recurring: Optional recurring billing configuration.

        Returns:
            Created price data.

        Raises:
            StripeError: If the creation fails.
            ValueError: If product_id is empty or unit_amount is invalid.
        """
        if not product_id:
            raise ValueError("product_id is required")
        if unit_amount <= 0:
            raise ValueError("unit_amount must be positive")

        data: dict[str, Any] = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
        }
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value
        if recurring:
            for key, value in recurring.items():
                data[f"recurring[{key}]"] = value

        logger.info(
            "stripe_creating_price",
            product_id=product_id,
            unit_amount=unit_amount,
            currency=currency,
        )
        return await self._request("POST", "/prices", data=data)

    async def update_price(
        self,
        price_id: str,
        active: bool | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing price.

        Note: Stripe prices are immutable for unit_amount/currency.
        This method can only update active status and metadata.
        To change the amount, create a new price.

        Args:
            price_id: The Stripe price ID.
            active: Set to False to deactivate the price.
            metadata: Metadata key-value pairs to update.

        Returns:
            Updated price data.

        Raises:
            StripeError: If the update fails.
            ValueError: If price_id is empty.
        """
        if not price_id:
            raise ValueError("price_id is required")

        data: dict[str, Any] = {}
        if active is not None:
            data["active"] = str(active).lower()
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        logger.info("stripe_updating_price", price_id=price_id)
        return await self._request("POST", f"/prices/{price_id}", data=data)

    async def archive_price(self, price_id: str) -> dict[str, Any]:
        """Archive (deactivate) a price.

        Args:
            price_id: The Stripe price ID to archive.

        Returns:
            Updated price data with active=False.

        Raises:
            StripeError: If the operation fails.
        """
        logger.info("stripe_archiving_price", price_id=price_id)
        return await self.update_price(price_id, active=False)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("stripe_client_closed")
