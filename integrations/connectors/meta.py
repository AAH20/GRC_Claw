"""Meta Marketing API connector."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class MetaConnector(BaseConnector):
    """Meta (Facebook) Marketing API connector.

    Supports ad accounts, campaigns, ad sets, ads, audiences, and insights.
    Uses OAuth 2.0 for authentication.
    """

    DEFAULT_BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(
        self,
        access_token: str,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                access_token=access_token,
            )
        super().__init__(config)
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token = access_token
        self._oauth_handler: Optional[OAuth2Handler] = None

    async def authenticate(self) -> None:
        """Authenticate with Meta using the provided access token."""
        self._state = self._state.AUTHENTICATING
        try:
            # Validate the token by making a simple API call
            response = await self.get("/me", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid Meta access token")
            self._auth_token = self._access_token
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"Meta authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the Meta access token using the app credentials."""
        if not self.app_id or not self.app_secret:
            raise ConnectorError("app_id and app_secret required for token refresh")

        if not self._oauth_handler:
            self._oauth_handler = OAuth2Handler(
                client_id=self.app_id,
                client_secret=self.app_secret,
                token_url=f"{self.DEFAULT_BASE_URL}/oauth/access_token",
            )

        # Meta uses a different token exchange endpoint
        response = await self.get(
            "/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": self._access_token,
            },
            auth=False,
        )
        if response.is_success and isinstance(response.data, dict):
            self._access_token = response.data.get("access_token", self._access_token)
            self._auth_token = self._access_token

    async def health_check(self) -> bool:
        """Check if the Meta API is reachable and token is valid."""
        try:
            response = await self.get("/me", auth=False)
            return response.is_success
        except Exception:
            return False

    # ─── Ad Accounts ────────────────────────────────────────────────────

    async def get_ad_accounts(
        self, fields: Optional[List[str]] = None, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Get list of ad accounts.

        Args:
            fields: Fields to retrieve.
            limit: Maximum number of accounts to return.

        Returns:
            List of ad account dictionaries.
        """
        default_fields = ["id", "name", "account_status", "currency", "timezone_name"]
        params: Dict[str, Any] = {
            "fields": ",".join(fields or default_fields),
            "limit": limit,
        }
        response = await self.get("/me/adaccounts", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    async def get_ad_account(self, account_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get details of a specific ad account.

        Args:
            account_id: The ad account ID (with or without 'act_' prefix).
            fields: Fields to retrieve.

        Returns:
            Ad account details.
        """
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        default_fields = ["id", "name", "account_status", "currency", "timezone_name", "business"]
        params = {"fields": ",".join(fields or default_fields)}
        response = await self.get(f"/{account_id}", params=params)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Campaigns ──────────────────────────────────────────────────────

    async def get_campaigns(
        self,
        account_id: str,
        fields: Optional[List[str]] = None,
        limit: int = 25,
        effective_status: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get campaigns for an ad account.

        Args:
            account_id: The ad account ID.
            fields: Fields to retrieve.
            limit: Maximum number of campaigns.
            effective_status: Filter by status (ACTIVE, PAUSED, DELETED, etc.).

        Returns:
            List of campaign dictionaries.
        """
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        default_fields = ["id", "name", "status", "effective_status", "objective", "created_time"]
        params: Dict[str, Any] = {
            "fields": ",".join(fields or default_fields),
            "limit": limit,
        }
        if effective_status:
            params["effective_status"] = ",".join(effective_status)

        response = await self.get(f"/{account_id}/campaigns", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    async def create_campaign(
        self,
        account_id: str,
        name: str,
        objective: str,
        *,
        status: str = "PAUSED",
        special_ad_categories: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new campaign.

        Args:
            account_id: The ad account ID.
            name: Campaign name.
            objective: Campaign objective (e.g., 'OUTCOME_TRAFFIC', 'OUTCOME_SALES').
            status: Campaign status ('ACTIVE' or 'PAUSED').
            special_ad_categories: Special ad categories (e.g., ['NONE']).
            **kwargs: Additional campaign parameters.

        Returns:
            Created campaign details.
        """
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        data: Dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or ["NONE"],
            **kwargs,
        }
        response = await self.post(f"/{account_id}/campaigns", data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_campaign(self, campaign_id: str, **kwargs: Any) -> Dict[str, Any]:
        """Update an existing campaign.

        Args:
            campaign_id: The campaign ID.
            **kwargs: Fields to update.

        Returns:
            Updated campaign details.
        """
        response = await self.post(f"/{campaign_id}", data=kwargs)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/{campaign_id}")
        return response.is_success

    # ─── Ad Sets ────────────────────────────────────────────────────────

    async def get_ad_sets(
        self,
        campaign_id: str,
        fields: Optional[List[str]] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Get ad sets for a campaign.

        Args:
            campaign_id: The campaign ID.
            fields: Fields to retrieve.
            limit: Maximum number of ad sets.

        Returns:
            List of ad set dictionaries.
        """
        default_fields = ["id", "name", "status", "effective_status", "daily_budget", "campaign_id"]
        params: Dict[str, Any] = {
            "fields": ",".join(fields or default_fields),
            "limit": limit,
        }
        response = await self.get(f"/{campaign_id}/adsets", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    async def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        *,
        daily_budget: Optional[int] = None,
        lifetime_budget: Optional[int] = None,
        billing_event: str = "IMPRESSIONS",
        optimization_goal: str = "REACH",
        targeting: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new ad set.

        Args:
            campaign_id: The campaign ID.
            name: Ad set name.
            daily_budget: Daily budget in cents.
            lifetime_budget: Lifetime budget in cents.
            billing_event: Billing event type.
            optimization_goal: Optimization goal.
            targeting: Targeting specification.
            **kwargs: Additional ad set parameters.

        Returns:
            Created ad set details.
        """
        data: Dict[str, Any] = {
            "name": name,
            "campaign_id": campaign_id,
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            **kwargs,
        }
        if daily_budget:
            data["daily_budget"] = daily_budget
        if lifetime_budget:
            data["lifetime_budget"] = lifetime_budget
        if targeting:
            data["targeting"] = targeting

        response = await self.post(f"/{campaign_id}/adsets", data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Ads ────────────────────────────────────────────────────────────

    async def get_ads(
        self,
        ad_set_id: str,
        fields: Optional[List[str]] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Get ads for an ad set.

        Args:
            ad_set_id: The ad set ID.
            fields: Fields to retrieve.
            limit: Maximum number of ads.

        Returns:
            List of ad dictionaries.
        """
        default_fields = ["id", "name", "status", "effective_status", "creative", "adset_id"]
        params: Dict[str, Any] = {
            "fields": ",".join(fields or default_fields),
            "limit": limit,
        }
        response = await self.get(f"/{ad_set_id}/ads", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    async def create_ad(
        self,
        ad_set_id: str,
        name: str,
        creative: Dict[str, Any],
        *,
        status: str = "PAUSED",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new ad.

        Args:
            ad_set_id: The ad set ID.
            name: Ad name.
            creative: Ad creative specification.
            status: Ad status.
            **kwargs: Additional ad parameters.

        Returns:
            Created ad details.
        """
        data: Dict[str, Any] = {
            "name": name,
            "adset_id": ad_set_id,
            "creative": creative,
            "status": status,
            **kwargs,
        }
        response = await self.post(f"/{ad_set_id}/ads", data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Insights ───────────────────────────────────────────────────────

    async def get_insights(
        self,
        object_id: str,
        *,
        fields: Optional[List[str]] = None,
        date_preset: str = "last_30d",
        time_range: Optional[Dict[str, str]] = None,
        breakdowns: Optional[List[str]] = None,
        level: str = "ad",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get insights/analytics data.

        Args:
            object_id: The object ID (campaign, ad set, or ad).
            fields: Metrics/fields to retrieve.
            date_preset: Date preset (today, yesterday, last_7d, last_30d, etc.).
            time_range: Custom time range with 'since' and 'until' keys.
            breakdowns: Breakdown dimensions.
            level: Level of granularity (campaign, adset, ad).
            limit: Maximum number of results.

        Returns:
            List of insight data dictionaries.
        """
        default_fields = [
            "impressions", "clicks", "spend", "cpc", "cpm", "ctr",
            "reach", "frequency", "actions", "cost_per_action_type",
        ]
        params: Dict[str, Any] = {
            "fields": ",".join(fields or default_fields),
            "date_preset": date_preset,
            "level": level,
            "limit": limit,
        }
        if time_range:
            params["time_range"] = time_range
        if breakdowns:
            params["breakdowns"] = ",".join(breakdowns)

        response = await self.get(f"/{object_id}/insights", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    # ─── Audiences ──────────────────────────────────────────────────────

    async def get_custom_audiences(
        self, account_id: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Get custom audiences for an ad account.

        Args:
            account_id: The ad account ID.
            limit: Maximum number of audiences.

        Returns:
            List of audience dictionaries.
        """
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        params = {"limit": limit}
        response = await self.get(f"/{account_id}/customaudiences", params=params)
        if isinstance(response.data, dict):
            return response.data.get("data", [])
        return []

    async def create_custom_audience(
        self,
        account_id: str,
        name: str,
        *,
        subtype: str = "CUSTOM",
        description: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a custom audience.

        Args:
            account_id: The ad account ID.
            name: Audience name.
            subtype: Audience subtype.
            description: Audience description.
            **kwargs: Additional audience parameters.

        Returns:
            Created audience details.
        """
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        data: Dict[str, Any] = {
            "name": name,
            "subtype": subtype,
            "description": description,
            **kwargs,
        }
        response = await self.post(f"/{account_id}/customaudiences", data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}
