"""Promotion Agent - Handles marketing campaigns, social media, and ticket sales."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from event_management.agents.base import AgentContext, BaseAgent


class MarketingChannel(BaseModel):
    """A marketing channel with its strategy."""

    channel: str  # email, social_media, paid_ads, content_marketing, partnerships
    description: str
    budget_allocation: float
    target_audience: str
    key_messages: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    timeline: str = ""


class CampaignAsset(BaseModel):
    """A marketing asset for the campaign."""

    asset_type: str  # email, social_post, landing_page, flyer, video
    title: str
    description: str
    channel: str
    publish_date: str
    status: str = "draft"  # draft, review, approved, published


class PromotionInput(BaseModel):
    """Input for the Promotion Agent."""

    event_name: str
    event_type: str
    event_date: str
    target_audience: str
    ticket_price: float
    expected_attendees: int
    marketing_budget: float
    goals: list[str] = Field(default_factory=list)
    brand_guidelines: dict[str, Any] = Field(default_factory=dict)
    existing_contacts: int = 0


class PromotionOutput(BaseModel):
    """Output from the Promotion Agent."""

    campaign_strategy: str = ""
    channels: list[MarketingChannel] = Field(default_factory=list)
    assets: list[CampaignAsset] = Field(default_factory=list)
    ticket_sales_strategy: str = ""
    social_media_calendar: list[dict[str, Any]] = Field(default_factory=list)
    email_sequence: list[dict[str, Any]] = Field(default_factory=list)
    kpis: dict[str, float] = Field(default_factory=dict)


class PromotionAgent(BaseAgent[PromotionInput, PromotionOutput]):
    """Agent responsible for event promotion and marketing."""

    @property
    def name(self) -> str:
        return "PromotionAgent"

    async def execute(self, input_data: PromotionInput, context: AgentContext) -> PromotionOutput:
        """Generate a comprehensive promotion plan.

        Args:
            input_data: The promotion requirements and constraints.
            context: Execution context with event and user info.

        Returns:
            A complete promotion plan with channels, assets, and KPIs.
        """
        self.logger.info(
            "generating_promotion_plan",
            event_name=input_data.event_name,
            target_audience=input_data.target_audience,
            marketing_budget=input_data.marketing_budget,
        )

        channels = self._plan_channels(input_data)
        assets = self._create_assets(input_data)
        ticket_strategy = self._create_ticket_strategy(input_data)
        social_calendar = self._build_social_calendar(input_data)
        email_sequence = self._build_email_sequence(input_data)
        kpis = self._define_kpis(input_data)
        strategy = self._create_campaign_strategy(input_data)

        return PromotionOutput(
            campaign_strategy=strategy,
            channels=channels,
            assets=assets,
            ticket_sales_strategy=ticket_strategy,
            social_media_calendar=social_calendar,
            email_sequence=email_sequence,
            kpis=kpis,
        )

    def _plan_channels(self, data: PromotionInput) -> list[MarketingChannel]:
        """Plan marketing channels based on budget and audience."""
        budget = data.marketing_budget
        return [
            MarketingChannel(
                channel="email",
                description="Email marketing to existing contacts and lists",
                budget_allocation=budget * 0.15,
                target_audience="Existing community and past attendees",
                key_messages=[
                    f"Join us for {data.event_name}",
                    "Early bird pricing available",
                    "Limited seats remaining",
                ],
                metrics=["open_rate", "click_rate", "conversion_rate"],
                timeline="T-45 days to T-1 day",
            ),
            MarketingChannel(
                channel="social_media",
                description="Organic and paid social media campaigns",
                budget_allocation=budget * 0.30,
                target_audience=data.target_audience,
                key_messages=[
                    f"🎯 {data.event_name} is happening!",
                    "Register now - early bird ends soon",
                    "Don't miss out on this amazing event",
                ],
                metrics=["reach", "engagement", "clicks", "registrations"],
                timeline="T-30 days to T-0",
            ),
            MarketingChannel(
                channel="paid_ads",
                description="Targeted paid advertising campaigns",
                budget_allocation=budget * 0.35,
                target_audience=data.target_audience,
                key_messages=[
                    f"Register for {data.event_name}",
                    "Limited time early bird discount",
                ],
                metrics=["impressions", "ctr", "cpa", "roas"],
                timeline="T-21 days to T-3 days",
            ),
            MarketingChannel(
                channel="content_marketing",
                description="Blog posts, articles, and SEO content",
                budget_allocation=budget * 0.10,
                target_audience="Organic search audience",
                key_messages=[
                    f"Why you should attend {data.event_name}",
                    "Speaker announcements and teasers",
                ],
                metrics=["traffic", "time_on_page", "registrations"],
                timeline="T-60 days to T-0",
            ),
            MarketingChannel(
                channel="partnerships",
                description="Cross-promotion with partners and sponsors",
                budget_allocation=budget * 0.10,
                target_audience="Partner networks and communities",
                key_messages=[
                    f"Partnering with {data.event_name}",
                    "Exclusive partner discounts",
                ],
                metrics=["referrals", "registrations", "reach"],
                timeline="T-30 days to T-0",
            ),
        ]

    def _create_assets(self, data: PromotionInput) -> list[CampaignAsset]:
        """Create marketing assets for the campaign."""
        return [
            CampaignAsset(
                asset_type="landing_page",
                title=f"{data.event_name} - Registration Page",
                description="Main event registration landing page",
                channel="website",
                publish_date="T-45 days",
                status="draft",
            ),
            CampaignAsset(
                asset_type="email",
                title="Save the Date Announcement",
                description="Initial announcement email to mailing list",
                channel="email",
                publish_date="T-45 days",
                status="draft",
            ),
            CampaignAsset(
                asset_type="social_post",
                title="Event Announcement Post",
                description="Social media announcement with event details",
                channel="social_media",
                publish_date="T-30 days",
                status="draft",
            ),
            CampaignAsset(
                asset_type="video",
                title="Event Promo Video",
                description="Short promotional video for social channels",
                channel="social_media",
                publish_date="T-21 days",
                status="draft",
            ),
            CampaignAsset(
                asset_type="flyer",
                title="Event Flyer",
                description="Printable and shareable event flyer",
                channel="content_marketing",
                publish_date="T-30 days",
                status="draft",
            ),
        ]

    def _create_ticket_strategy(self, data: PromotionInput) -> str:
        """Create a ticket sales strategy."""
        return (
            f"Implement tiered pricing for {data.event_name}: "
            f"Early Bird (${data.ticket_price * 0.7:.2f}) for first 50 tickets, "
            f"Regular (${data.ticket_price:.2f}) until 2 weeks before, "
            f"Late (${data.ticket_price * 1.2:.2f}) for final week. "
            f"Offer group discounts (10% off for 5+). "
            f"Target: sell 80% of {data.expected_attendees} capacity by T-7 days."
        )

    def _build_social_calendar(self, data: PromotionInput) -> list[dict[str, Any]]:
        """Build a social media content calendar."""
        base_date = datetime(2026, 1, 1)  # Placeholder - would use actual event date
        posts = []
        for week in range(6, 0, -1):
            post_date = base_date + timedelta(days=-7 * week)
            posts.append({
                "date": post_date.isoformat(),
                "platform": "twitter",
                "content_type": "announcement" if week == 6 else "reminder",
                "message": f"🎯 {data.event_name} - {week} weeks away! Register now.",
            })
            posts.append({
                "date": post_date.isoformat(),
                "platform": "linkedin",
                "content_type": "professional",
                "message": f"Excited to announce {data.event_name}. Join us!",
            })
        return posts

    def _build_email_sequence(self, data: PromotionInput) -> list[dict[str, Any]]:
        """Build an email marketing sequence."""
        return [
            {
                "sequence_order": 1,
                "timing": "T-45 days",
                "subject": f"Save the Date: {data.event_name}",
                "goal": "Announce event and build anticipation",
            },
            {
                "sequence_order": 2,
                "timing": "T-30 days",
                "subject": f"Early Bird Registration Open: {data.event_name}",
                "goal": "Drive early registrations with discount",
            },
            {
                "sequence_order": 3,
                "timing": "T-14 days",
                "subject": f"Speaker Lineup Revealed: {data.event_name}",
                "goal": "Generate excitement with speaker announcements",
            },
            {
                "sequence_order": 4,
                "timing": "T-7 days",
                "subject": f"Last Chance for Early Bird: {data.event_name}",
                "goal": "Create urgency for early bird deadline",
            },
            {
                "sequence_order": 5,
                "timing": "T-3 days",
                "subject": f"Final Reminder: {data.event_name} is Almost Here!",
                "goal": "Last push for registrations",
            },
        ]

    def _define_kpis(self, data: PromotionInput) -> dict[str, float]:
        """Define key performance indicators for the campaign."""
        return {
            "registration_target": float(data.expected_attendees),
            "email_open_rate_target": 0.25,
            "email_click_rate_target": 0.05,
            "social_engagement_rate_target": 0.03,
            "paid_ad_ctr_target": 0.02,
            "cost_per_acquisition_target": data.marketing_budget / max(data.expected_attendees, 1),
            "overall_roas_target": 3.0,
        }

    def _create_campaign_strategy(self, data: PromotionInput) -> str:
        """Create a high-level campaign strategy summary."""
        return (
            f"Multi-channel promotion campaign for {data.event_name} targeting "
            f"{data.target_audience}. Budget: ${data.marketing_budget:,.2f}. "
            f"Focus on early bird conversions, social engagement, and "
            f"partnership amplification. Goal: {data.expected_attendees} attendees."
        )
