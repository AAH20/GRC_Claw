"""SAP ERP integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import structlog

from sales_forecaster.core import get_settings
from sales_forecaster.core.exceptions import AuthenticationError, IntegrationError
from sales_forecaster.core.retry import async_retry

if TYPE_CHECKING:
    from datetime import datetime

logger = structlog.get_logger(__name__)


class SAPIntegration:
    """Integration with SAP ERP via OData REST API.

    Handles authentication, sales order querying, and data normalization.
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        client: str = "100",
        timeout_seconds: int = 60,
    ) -> None:
        """Initialize SAP integration.

        Args:
            base_url: SAP OData service base URL.
            username: SAP username.
            password: SAP password.
            client: SAP client number.
            timeout_seconds: HTTP request timeout.
        """
        settings = get_settings()
        self.base_url = (base_url or settings.sap_base_url).rstrip("/")
        self.username = username or settings.sap_username
        self.password = password or settings.sap_password
        self.client = client or settings.sap_client
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        """Check if the integration is properly configured."""
        return all([self.base_url, self.username, self.password])

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_auth(self) -> tuple[str, str]:
        """Get authentication tuple.

        Returns:
            Tuple of (username, password).
        """
        if not self.username or not self.password:
            raise AuthenticationError(
                "SAP credentials not configured",
                source="sap",
            )
        return (self.username, self.password)

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )
    async def get_sales_orders(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch sales orders from SAP.

        Args:
            start_date: Start date for order creation.
            end_date: End date for order creation.
            limit: Maximum number of records to fetch.

        Returns:
            List of raw sales order records.

        Raises:
            IntegrationError: If the API request fails.
        """
        if not self.is_configured:
            raise AuthenticationError(
                "SAP integration not configured",
                source="sap",
            )

        url = f"{self.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"

        params = {
            "$filter": (
                f"CreationDate ge datetime'{start_date.strftime('%Y-%m-%dT%H:%M:%S')}'"
                f" and CreationDate le datetime'{end_date.strftime('%Y-%m-%dT%H:%M:%S')}'"
            ),
            "$top": limit,
            "$format": "json",
        }

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            auth=self._get_auth(),
        ) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)

            if response.status_code != 200:
                raise IntegrationError(
                    f"SAP API request failed: {response.text}",
                    source="sap",
                    status_code=response.status_code,
                )

            data = response.json()
            orders = data.get("d", {}).get("results", [])
            logger.info("Fetched sales orders from SAP", count=len(orders))
            return orders

    async def get_customers(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch customers from SAP.

        Args:
            limit: Maximum number of records to fetch.

        Returns:
            List of raw customer records.

        Raises:
            IntegrationError: If the API request fails.
        """
        if not self.is_configured:
            raise AuthenticationError(
                "SAP integration not configured",
                source="sap",
            )

        url = f"{self.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Customer"

        params = {"$top": limit, "$format": "json"}

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            auth=self._get_auth(),
        ) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)

            if response.status_code != 200:
                raise IntegrationError(
                    f"SAP API request failed: {response.text}",
                    source="sap",
                    status_code=response.status_code,
                )

            data = response.json()
            return data.get("d", {}).get("results", [])

    async def health_check(self) -> bool:
        """Check if the SAP connection is healthy.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        if not self.is_configured:
            return False

        try:
            url = f"{self.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                auth=self._get_auth(),
            ) as client:
                response = await client.get(
                    url, headers=self._get_headers(), params={"$top": 1, "$format": "json"}
                )
                return response.status_code == 200
        except Exception as exc:
            logger.warning("SAP health check failed", error=str(exc))
            return False
