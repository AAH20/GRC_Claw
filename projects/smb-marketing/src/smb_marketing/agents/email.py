"""Email marketing agent for campaign creation and delivery."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class EmailStatus(StrEnum):
    """Email campaign statuses."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"


class EmailCampaignRequest(BaseModel):
    """Request model for creating an email campaign.

    Attributes:
        subject: Email subject line.
        body_html: HTML email body.
        body_text: Plain text fallback.
        recipient_list_id: Mailchimp audience/list ID.
        from_name: Sender display name.
        from_email: Sender email address.
        ab_test: Whether to enable A/B testing.
    """

    subject: str = Field(..., min_length=1, max_length=500)
    body_html: str = Field(..., min_length=1)
    body_text: str | None = None
    recipient_list_id: str = Field(..., min_length=1)
    from_name: str = Field(default="SMB Marketing", min_length=1, max_length=200)
    from_email: str = Field(..., min_length=3, max_length=254)
    ab_test: bool = False


class EmailCampaignResponse(BaseModel):
    """Response model for email campaign operations.

    Attributes:
        id: Unique campaign identifier.
        subject: Email subject.
        status: Current campaign status.
        recipient_count: Number of recipients.
        sent_time: When the campaign was sent.
    """

    id: str
    subject: str
    status: EmailStatus
    recipient_count: int = 0
    sent_time: datetime | None = None


class EmailAgent:
    """AI agent for email marketing campaigns.

    Manages email campaign creation, audience segmentation,
    A/B testing, and delivery via Mailchimp.
    """

    def __init__(
        self,
        mailchimp_client: Any | None = None,
        llm_client: Any | None = None,
    ) -> None:
        """Initialize the EmailAgent.

        Args:
            mailchimp_client: Optional Mailchimp API client.
            llm_client: Optional LLM client for subject line optimization.
        """
        self._mailchimp_client = mailchimp_client
        self._llm_client = llm_client
        self._logger = logger.bind(agent="email")
        self._campaigns: dict[str, EmailCampaignResponse] = {}

    async def create_campaign(self, request: EmailCampaignRequest) -> EmailCampaignResponse:
        """Create an email campaign.

        Args:
            request: Email campaign parameters.

        Returns:
            The created email campaign response.
        """
        self._logger.info(
            "Creating email campaign",
            subject=request.subject,
            list_id=request.recipient_list_id,
        )

        campaign_id = self._generate_campaign_id()

        campaign = EmailCampaignResponse(
            id=campaign_id,
            subject=request.subject,
            status=EmailStatus.DRAFT,
        )

        self._campaigns[campaign_id] = campaign

        self._logger.info("Email campaign created", campaign_id=campaign_id)
        return campaign

    async def send_campaign(self, campaign_id: str) -> EmailCampaignResponse:
        """Send an email campaign.

        Args:
            campaign_id: Unique campaign identifier.

        Returns:
            The sent campaign response.

        Raises:
            KeyError: If the campaign is not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Email campaign not found: {campaign_id}")

        campaign = self._campaigns[campaign_id]

        if self._mailchimp_client:
            try:
                await self._mailchimp_client.send_campaign(campaign_id)
                campaign.status = EmailStatus.SENT
                campaign.sent_time = datetime.utcnow()
            except Exception as exc:
                campaign.status = EmailStatus.FAILED
                self._logger.error("Failed to send email campaign", error=str(exc))
                raise RuntimeError(f"Failed to send email campaign: {exc}") from exc
        else:
            # Simulate sending for testing
            campaign.status = EmailStatus.SENT
            campaign.sent_time = datetime.utcnow()
            campaign.recipient_count = 100  # Simulated

        self._logger.info("Email campaign sent", campaign_id=campaign_id)
        return campaign

    async def get_campaign(self, campaign_id: str) -> EmailCampaignResponse:
        """Retrieve an email campaign by ID.

        Args:
            campaign_id: Unique campaign identifier.

        Returns:
            The email campaign response.

        Raises:
            KeyError: If the campaign is not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Email campaign not found: {campaign_id}")
        return self._campaigns[campaign_id]

    async def list_campaigns(
        self,
        status: EmailStatus | None = None,
    ) -> list[EmailCampaignResponse]:
        """List email campaigns with optional status filter.

        Args:
            status: Optional status filter.

        Returns:
            List of email campaign responses.
        """
        campaigns = list(self._campaigns.values())
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns

    def optimize_subject_line(self, subject: str) -> str:
        """Optimize an email subject line for open rates.

        Args:
            subject: Original subject line.

        Returns:
            Optimized subject line.
        """
        # Simple optimization — replace with LLM-powered analysis
        if len(subject) > 60:
            return subject[:57] + "..."
        return subject

    def _generate_campaign_id(self) -> str:
        """Generate a unique campaign identifier.

        Returns:
            Unique campaign ID string.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"email_{timestamp}"
