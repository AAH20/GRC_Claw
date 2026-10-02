"""LinkedIn Marketing API connector."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class LinkedInConnector(BaseConnector):
    """LinkedIn Marketing API connector.

    Supports ad accounts, campaigns, creatives, and analytics.
    Uses OAuth 2.0 for authentication.
    """

    DEFAULT_BASE_URL = "https://api.linkedin.com/v2"
    AUTH_BASE_URL = "https://www.linkedin.com/oauth/v2"

    def __init__(
        self,
        access_token: str,
        organization_id: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                access_token=access_token,
            )
        super().__init__(config)
        self._access_token = access_token
        self.organization_id = organization_id

    async def authenticate(self) -> None:
        """Authenticate with LinkedIn using the provided access token."""
        self._state = self._state.AUTHENTICATING
        try:
            response = await self.get("/me", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid LinkedIn access token")
            self._auth_token = self._access_token
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"LinkedIn authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the LinkedIn access token."""
        # LinkedIn tokens are typically long-lived; refresh requires re-authorization
        logger.info("LinkedIn token refresh requires re-authorization via OAuth flow")

    async def health_check(self) -> bool:
        """Check if the LinkedIn API is reachable."""
        try:
            response = await self.get("/me", auth=False)
            return response.is_success
        except Exception:
            return False

    # ─── Ad Accounts ────────────────────────────────────────────────────

    async def get_ad_accounts(
        self,
        *,
        statuses: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get list of ad accounts.

        Args:
            statuses: Filter by account status (ACTIVE, CANCELED, DRAFT, etc.).
            limit: Maximum number of accounts.

        Returns:
            List of ad account dictionaries.
        """
        params: Dict[str, Any] = {
            "q": "search",
            "count": limit,
        }
        if statuses:
            params["status"] = ",".join(statuses)

        response = await self.get("/adAccountsV2", params=params)
        if isinstance(response.data, dict):
            return response.data.get("elements", [])
        return []

    async def get_ad_account(self, account_id: str) -> Dict[str, Any]:
        """Get details of a specific ad account.

        Args:
            account_id: The ad account ID (URN format: urn:li:sponsoredAccount:XXXXX).

        Returns:
            Ad account details.
        """
        response = await self.get(f"/adAccountsV2/{account_id}")
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Campaigns ──────────────────────────────────────────────────────

    async def get_campaigns(
        self,
        account_id: str,
        *,
        statuses: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get campaigns for an ad account.

        Args:
            account_id: The ad account ID.
            statuses: Filter by campaign status.
            limit: Maximum number of campaigns.

        Returns:
            List of campaign dictionaries.
        """
        params: Dict[str, Any] = {
            "q": "search",
            "account": account_id,
            "count": limit,
        }
        if statuses:
            params["status"] = ",".join(statuses)

        response = await self.get("/adCampaignsV2", params=params)
        if isinstance(response.data, dict):
            return response.data.get("elements", [])
        return []

    async def create_campaign(
        self,
        account_id: str,
        name: str,
        *,
        campaign_group_id: Optional[str] = None,
        type: str = "SPONSORED_UPDATES",
        status: str = "DRAFT",
        daily_budget: Optional[Dict[str, Any]] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        targeting: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new campaign.

        Args:
            account_id: The ad account ID.
            name: Campaign name.
            campaign_group_id: Optional campaign group ID.
            type: Campaign type.
            status: Campaign status.
            daily_budget: Daily budget with 'amount' and 'currencyCode'.
            start_date: Start date as Unix timestamp (milliseconds).
            end_date: End date as Unix timestamp (milliseconds).
            targeting: Targeting criteria.
            **kwargs: Additional campaign parameters.

        Returns:
            Created campaign details.
        """
        data: Dict[str, Any] = {
            "account": account_id,
            "name": name,
            "type": type,
            "status": status,
            **kwargs,
        }
        if campaign_group_id:
            data["campaignGroup"] = campaign_group_id
        if daily_budget:
            data["dailyBudget"] = daily_budget
        if start_date:
            data["startAt"] = start_date
        if end_date:
            data["endAt"] = end_date
        if targeting:
            data["targetingCriteria"] = targeting

        response = await self.post("/adCampaignsV2", data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_campaign(
        self,
        campaign_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update an existing campaign.

        Args:
            campaign_id: The campaign ID.
            **kwargs: Fields to update.

        Returns:
            Updated campaign details.
        """
        response = await self.post(f"/adCampaignsV2/{campaign_id}", data=kwargs)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Creatives ──────────────────────────────────────────────────────

    async def get_creatives(
        self,
        campaign_id: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get creatives for a campaign.

        Args:
            campaign_id: The campaign ID.
            limit: Maximum number of creatives.

        Returns:
            List of creative dictionaries.
        """
        params = {
            "q": "search",
            "campaign": campaign_id,
            "count": limit,
        }
        response = await self.get("/adCreativesV2", params=params)
        if isinstance(response.data, dict):
            return response.data.get("elements", [])
        return []

    # ─── Analytics ──────────────────────────────────────────────────────

    async def get_analytics(
        self,
        account_id: str,
        *,
        date_range: Optional[Dict[str, str]] = None,
        pivot: str = "CAMPAIGN",
        fields: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get analytics data.

        Args:
            account_id: The ad account ID.
            date_range: Date range with 'start' and 'end' keys.
            pivot: Pivot dimension (CAMPAIGN, CREATIVE, etc.).
            fields: Fields to retrieve.
            limit: Maximum number of results.

        Returns:
            List of analytics data dictionaries.
        """
        params: Dict[str, Any] = {
            "q": "statistics",
            "pivot": pivot,
            "count": limit,
        }
        if date_range:
            params["dateRange"] = date_range
        if fields:
            params["fields"] = ",".join(fields)

        response = await self.get(
            f"/adAnalyticsV2",
            params={**params, "accounts": f"List({account_id})"},
        )
        if isinstance(response.data, dict):
            return response.data.get("elements", [])
        return []

    # ─── Organizations ──────────────────────────────────────────────────

    async def get_organization(self, organization_id: str) -> Dict[str, Any]:
        """Get organization details.

        Args:
            organization_id: The organization ID (URN format).

        Returns:
            Organization details.
        """
        response = await self.get(f"/organizations/{organization_id}")
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_organization_acl(self) -> List[Dict[str, Any]]:
        """Get organization ACL (access control list).

        Returns:
            List of ACL entries.
        """
        response = await self.get("/organizationAcls", params={"q": "roleAssignee"})
        if isinstance(response.data, dict):
            return response.data.get("elements", [])
        return []
