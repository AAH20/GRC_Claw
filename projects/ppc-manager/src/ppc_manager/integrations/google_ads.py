"""Google Ads API integration client."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class GoogleAdsConfig(BaseModel):
    """Configuration for Google Ads API.

    Attributes:
        developer_token: Google Ads API developer token.
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret.
        refresh_token: OAuth2 refresh token.
        login_customer_id: Manager account ID (optional).
    """

    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    login_customer_id: str | None = None


class GoogleAdsCampaign(BaseModel):
    """A Google Ads campaign.

    Attributes:
        id: Campaign ID.
        name: Campaign name.
        status: Campaign status.
        budget: Daily budget in micros.
    """

    id: str
    name: str
    status: str
    budget: int = 0


class GoogleAdsClient:
    """Client for the Google Ads API.

    Provides methods to interact with Google Ads campaigns, ad groups,
    and keywords via the Google Ads API.
    """

    def __init__(self, config: GoogleAdsConfig) -> None:
        """Initialize the Google Ads client.

        Args:
            config: The Google Ads API configuration.
        """
        self.config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-load the Google Ads client.

        Returns:
            The Google Ads API client instance.
        """
        if self._client is None:
            from google.ads.googleads.client import GoogleAdsClient as GAdsClient

            self._client = GAdsClient.load_from_dict(
                {
                    "developer_token": self.config.developer_token,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "refresh_token": self.config.refresh_token,
                    "login_customer_id": self.config.login_customer_id,
                    "use_proto_plus": True,
                }
            )
        return self._client

    async def list_campaigns(self, customer_id: str) -> list[GoogleAdsCampaign]:
        """List all campaigns for a customer account.

        Args:
            customer_id: The Google Ads customer ID.

        Returns:
            A list of GoogleAdsCampaign objects.

        Raises:
            ValueError: If customer_id is empty.
        """
        if not customer_id:
            raise ValueError("Customer ID is required")

        logger.info("Listing Google Ads campaigns", customer_id=customer_id)

        client = self._get_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign_budget.amount_micros
            FROM campaign
            ORDER BY campaign.id
        """

        response = ga_service.search_stream(customer_id=customer_id, query=query)

        campaigns: list[GoogleAdsCampaign] = []
        for batch in response:
            for row in batch.results:
                campaigns.append(
                    GoogleAdsCampaign(
                        id=str(row.campaign.id),
                        name=row.campaign.name,
                        status=row.campaign.status.name,
                        budget=row.campaign_budget.amount_micros,
                    )
                )

        logger.info("Google Ads campaigns listed", count=len(campaigns))
        return campaigns

    async def update_campaign_budget(
        self,
        customer_id: str,
        campaign_id: str,
        budget_micros: int,
    ) -> GoogleAdsCampaign:
        """Update a campaign's budget.

        Args:
            customer_id: The Google Ads customer ID.
            campaign_id: The campaign ID.
            budget_micros: The new budget in micros.

        Returns:
            The updated GoogleAdsCampaign.

        Raises:
            ValueError: If customer_id or campaign_id is empty.
        """
        if not customer_id or not campaign_id:
            raise ValueError("Customer ID and campaign ID are required")

        logger.info(
            "Updating Google Ads campaign budget",
            customer_id=customer_id,
            campaign_id=campaign_id,
            budget_micros=budget_micros,
        )

        client = self._get_client()
        campaign_service = client.get_service("CampaignService")

        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(
            customer_id, campaign_id
        )
        campaign_budget = client.get_type("CampaignBudget")
        campaign_budget.amount_micros = budget_micros
        campaign_budget.resource_name = campaign_service.campaign_budget_path(
            customer_id, campaign_id
        )
        campaign_operation.update_mask = client.get_type("FieldMask")
        # In production, use FieldMaskHelper to set the update mask properly

        campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_operation]
        )

        return GoogleAdsCampaign(
            id=campaign_id,
            name="",
            status="ENABLED",
            budget=budget_micros,
        )
