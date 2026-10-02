"""Campaign management agent for multi-channel marketing campaigns."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CampaignStatus(StrEnum):
    """Campaign lifecycle statuses."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CampaignChannel(StrEnum):
    """Supported marketing channels."""

    META = "meta"
    GOOGLE_ADS = "google_ads"
    MAILCHIMP = "mailchimp"


class CampaignRequest(BaseModel):
    """Request model for creating a marketing campaign.

    Attributes:
        name: Campaign name.
        description: Campaign description and objectives.
        channels: Marketing channels to use.
        budget: Total campaign budget in USD.
        start_date: Campaign start date.
        end_date: Campaign end date.
        target_audience: Target audience description.
    """

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    channels: list[CampaignChannel] = Field(..., min_length=1)
    budget: float = Field(..., gt=0, le=100000)
    start_date: datetime
    end_date: datetime
    target_audience: str | None = None

    def model_post_init(self, __context: Any) -> None:
        """Validate dates after initialization."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")


class CampaignResponse(BaseModel):
    """Response model for campaign operations.

    Attributes:
        id: Unique campaign identifier.
        name: Campaign name.
        status: Current campaign status.
        channels: Active channels.
        budget: Allocated budget.
        start_date: Campaign start date.
        end_date: Campaign end date.
        created_at: Creation timestamp.
    """

    id: str
    name: str
    status: CampaignStatus
    channels: list[CampaignChannel]
    budget: float
    start_date: datetime
    end_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CampaignsAgent:
    """AI agent for managing multi-channel marketing campaigns.

    Handles campaign creation, budget allocation, scheduling,
    and optimization across Meta, Google Ads, and Mailchimp.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the CampaignsAgent.

        Args:
            llm_client: Optional LLM client for optimization suggestions.
        """
        self._llm_client = llm_client
        self._logger = logger.bind(agent="campaigns")
        self._campaigns: dict[str, CampaignResponse] = {}

    async def create_campaign(self, request: CampaignRequest) -> CampaignResponse:
        """Create a new marketing campaign.

        Args:
            request: Campaign creation parameters.

        Returns:
            The created campaign response.

        Raises:
            ValueError: If the campaign parameters are invalid.
        """
        self._logger.info(
            "Creating campaign",
            name=request.name,
            channels=[c.value for c in request.channels],
            budget=request.budget,
        )

        campaign_id = self._generate_campaign_id()

        campaign = CampaignResponse(
            id=campaign_id,
            name=request.name,
            status=CampaignStatus.DRAFT,
            channels=request.channels,
            budget=request.budget,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        self._campaigns[campaign_id] = campaign

        self._logger.info("Campaign created", campaign_id=campaign_id)
        return campaign

    async def get_campaign(self, campaign_id: str) -> CampaignResponse:
        """Retrieve a campaign by ID.

        Args:
            campaign_id: Unique campaign identifier.

        Returns:
            The campaign response.

        Raises:
            KeyError: If the campaign is not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign not found: {campaign_id}")
        return self._campaigns[campaign_id]

    async def list_campaigns(
        self,
        status: CampaignStatus | None = None,
    ) -> list[CampaignResponse]:
        """List all campaigns, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            List of campaign responses.
        """
        campaigns = list(self._campaigns.values())
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns

    async def update_campaign(
        self,
        campaign_id: str,
        **updates: Any,
    ) -> CampaignResponse:
        """Update an existing campaign.

        Args:
            campaign_id: Unique campaign identifier.
            **updates: Fields to update.

        Returns:
            The updated campaign response.

        Raises:
            KeyError: If the campaign is not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign not found: {campaign_id}")

        campaign = self._campaigns[campaign_id]
        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        self._logger.info("Campaign updated", campaign_id=campaign_id)
        return campaign

    async def delete_campaign(self, campaign_id: str) -> None:
        """Delete a campaign.

        Args:
            campaign_id: Unique campaign identifier.

        Raises:
            KeyError: If the campaign is not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign not found: {campaign_id}")
        del self._campaigns[campaign_id]
        self._logger.info("Campaign deleted", campaign_id=campaign_id)

    def allocate_budget(
        self,
        total_budget: float,
        channels: list[CampaignChannel],
    ) -> dict[CampaignChannel, float]:
        """Allocate budget across channels.

        Args:
            total_budget: Total campaign budget.
            channels: Channels to allocate budget to.

        Returns:
            Budget allocation per channel.

        Raises:
            ValueError: If channels list is empty.
        """
        if not channels:
            raise ValueError("At least one channel is required")

        # Simple equal allocation — can be enhanced with AI optimization
        per_channel = total_budget / len(channels)
        return {channel: round(per_channel, 2) for channel in channels}

    def _generate_campaign_id(self) -> str:
        """Generate a unique campaign identifier.

        Returns:
            Unique campaign ID string.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"camp_{timestamp}"
