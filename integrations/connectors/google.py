"""Google Ads API connector."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class GoogleAdsConnector(BaseConnector):
    """Google Ads API connector.

    Supports campaigns, ad groups, ads, keywords, and reporting.
    Uses OAuth 2.0 for authentication.
    """

    DEFAULT_BASE_URL = "https://googleads.googleapis.com/v14"
    DEVELOPER_TOKEN_HEADER = "developer-token"
    LOGIN_CUSTOMER_ID_HEADER = "login-customer-id"

    def __init__(
        self,
        developer_token: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        *,
        login_customer_id: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                extra_headers={
                    self.DEVELOPER_TOKEN_HEADER: developer_token,
                },
            )
            if login_customer_id:
                config.extra_headers[self.LOGIN_CUSTOMER_ID_HEADER] = login_customer_id

        super().__init__(config)
        self.developer_token = developer_token
        self.login_customer_id = login_customer_id
        self._oauth_handler = OAuth2Handler(
            client_id=client_id,
            client_secret=client_secret,
            token_url="https://oauth2.googleapis.com/token",
        )
        self._oauth_handler._token = None
        self._refresh_token = refresh_token

    async def authenticate(self) -> None:
        """Authenticate with Google using OAuth 2.0 refresh token flow."""
        self._state = self._state.AUTHENTICATING
        try:
            # Use refresh token to get access token
            self._oauth_handler._token = type(self._oauth_handler._token)(
                access_token="",
                refresh_token=self._refresh_token,
                expires_in=0,
                obtained_at=0,
            )
            token = await self._oauth_handler.get_valid_token(session=self._session)
            self._auth_token = token
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"Google Ads authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the Google OAuth token."""
        if self._oauth_handler:
            token = await self._oauth_handler.refresh(session=self._session)
            self._auth_token = token.access_token

    async def health_check(self) -> bool:
        """Check if the Google Ads API is reachable."""
        try:
            response = await self.get(
                f"/customers/{self.login_customer_id}:searchStream",
                data={"query": "SELECT customer.id FROM customer LIMIT 1"},
            )
            return response.is_success
        except Exception:
            return False

    # ─── Customers ──────────────────────────────────────────────────────

    async def list_accessible_customers(self) -> List[Dict[str, Any]]:
        """List all accessible customer accounts.

        Returns:
            List of customer resource names.
        """
        response = await self.get("/customers:listAccessibleCustomers")
        if isinstance(response.data, dict):
            return response.data.get("resourceNames", [])
        return []

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details.

        Args:
            customer_id: The customer ID (without dashes).

        Returns:
            Customer details.
        """
        response = await self.get(f"/customers/{customer_id}")
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Campaigns ──────────────────────────────────────────────────────

    async def get_campaigns(
        self,
        customer_id: str,
        *,
        campaign_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get campaigns for a customer.

        Args:
            customer_id: The customer ID.
            campaign_ids: Optional list of campaign IDs to filter.

        Returns:
            List of campaign dictionaries.
        """
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign.start_date,
                campaign.end_date
            FROM campaign
            ORDER BY campaign.id
        """
        if campaign_ids:
            ids_str = ", ".join(campaign_ids)
            query += f" WHERE campaign.id IN ({ids_str})"

        return await self._search_stream(customer_id, query)

    async def create_campaign(
        self,
        customer_id: str,
        name: str,
        *,
        advertising_channel_type: str = "SEARCH",
        status: str = "PAUSED",
        bidding_strategy_type: str = "MANUAL_CPC",
        budget_micros: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new campaign.

        Args:
            customer_id: The customer ID.
            name: Campaign name.
            advertising_channel_type: Channel type (SEARCH, DISPLAY, etc.).
            status: Campaign status.
            bidding_strategy_type: Bidding strategy.
            budget_micros: Daily budget in micros.
            **kwargs: Additional campaign parameters.

        Returns:
            Created campaign details.
        """
        operations = [{
            "create": {
                "name": name,
                "advertising_channel_type": advertising_channel_type,
                "status": status,
                "bidding_strategy_type": bidding_strategy_type,
                **kwargs,
            }
        }]
        if budget_micros:
            operations[0]["create"]["campaign_budget"] = (
                f"customers/{customer_id}/campaignBudgets/{budget_micros}"
            )

        response = await self.mutate(customer_id, operations)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_campaign(
        self,
        customer_id: str,
        campaign_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update an existing campaign.

        Args:
            customer_id: The customer ID.
            campaign_id: The campaign ID.
            **kwargs: Fields to update.

        Returns:
            Updated campaign details.
        """
        resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
        operations = [{
            "update": {
                "resourceName": resource_name,
                **kwargs,
            },
            "updateMask": ",".join(kwargs.keys()),
        }]
        response = await self.mutate(customer_id, operations)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Ad Groups ──────────────────────────────────────────────────────

    async def get_ad_groups(
        self,
        customer_id: str,
        *,
        campaign_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get ad groups for a customer.

        Args:
            customer_id: The customer ID.
            campaign_id: Optional campaign ID to filter by.

        Returns:
            List of ad group dictionaries.
        """
        query = """
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                campaign.id
            FROM ad_group
        """
        if campaign_id:
            query += f" WHERE campaign.id = {campaign_id}"
        query += " ORDER BY ad_group.id"

        return await self._search_stream(customer_id, query)

    # ─── Keywords ───────────────────────────────────────────────────────

    async def get_keywords(
        self,
        customer_id: str,
        *,
        ad_group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get keywords for a customer.

        Args:
            customer_id: The customer ID.
            ad_group_id: Optional ad group ID to filter by.

        Returns:
            List of keyword dictionaries.
        """
        query = """
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.criterion_id,
                ad_group_criterion.status,
                ad_group.id
            FROM ad_group_criterion
            WHERE ad_group_criterion.type = KEYWORD
        """
        if ad_group_id:
            query += f" AND ad_group.id = {ad_group_id}"

        return await self._search_stream(customer_id, query)

    # ─── Reporting ──────────────────────────────────────────────────────

    async def get_report(
        self,
        customer_id: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Run a GAQL query and return results.

        Args:
            customer_id: The customer ID.
            query: GAQL query string.

        Returns:
            List of result row dictionaries.
        """
        return await self._search_stream(customer_id, query)

    # ─── Mutations ──────────────────────────────────────────────────────

    async def mutate(
        self,
        customer_id: str,
        operations: List[Dict[str, Any]],
    ) -> APIResponse:
        """Execute a mutation operation.

        Args:
            customer_id: The customer ID.
            operations: List of operation dictionaries.

        Returns:
            API response with mutation results.
        """
        return await self.post(
            f"/customers/{customer_id}:mutate",
            data={"operations": operations},
        )

    # ─── Internal Helpers ───────────────────────────────────────────────

    async def _search_stream(
        self,
        customer_id: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Execute a searchStream query and return all results.

        Args:
            customer_id: The customer ID.
            query: GAQL query string.

        Returns:
            List of result row dictionaries.
        """
        response = await self.post(
            f"/customers/{customer_id}:searchStream",
            data={"query": query},
        )
        if isinstance(response.data, list):
            return response.data
        if isinstance(response.data, dict):
            return response.data.get("results", [])
        return []
