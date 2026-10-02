"""Channel Orchestrator Agent for coordinating multi-channel outreach."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar

import structlog

logger = structlog.get_logger(__name__)


class ChannelType(str, Enum):
    """Available marketing channels."""

    EMAIL = "email"
    LINKEDIN_ADS = "linkedin_ads"
    GOOGLE_ADS = "google_ads"
    DIRECT_MAIL = "direct_mail"
    WEB_PERSONALIZATION = "web_personalization"
    PHONE = "phone"
    SMS = "sms"


class CampaignStatus(str, Enum):
    """Campaign execution status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class ChannelTouchpoint:
    """Represents a single touchpoint in a channel."""

    touchpoint_id: str
    channel: ChannelType
    account_id: str
    scheduled_time: datetime
    content_id: str | None = None
    status: CampaignStatus = CampaignStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationPlan:
    """Represents a multi-channel orchestration plan."""

    plan_id: str
    account_ids: list[str]
    touchpoints: list[ChannelTouchpoint] = field(default_factory=list)
    channels_used: list[ChannelType] = field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None


class ChannelOrchestratorAgent:
    """Coordinates multi-channel outreach for ABM campaigns.

    This agent plans, schedules, and orchestrates touchpoints across
    multiple channels to maximize engagement with target accounts while
    respecting frequency caps and channel preferences.
    """

    # Default channel sequence for ABM campaigns
    DEFAULT_SEQUENCE: ClassVar[list[ChannelType]] = [
        ChannelType.LINKEDIN_ADS,
        ChannelType.EMAIL,
        ChannelType.WEB_PERSONALIZATION,
        ChannelType.DIRECT_MAIL,
    ]

    def __init__(
        self,
        max_touchpoints_per_week: int = 5,
        channels: list[ChannelType] | None = None,
    ) -> None:
        """Initialize the Channel Orchestrator Agent.

        Args:
            max_touchpoints_per_week: Maximum touchpoints per account per week.
            channels: List of channels to use (defaults to DEFAULT_SEQUENCE).
        """
        self.max_touchpoints_per_week = max_touchpoints_per_week
        self.channels = channels or self.DEFAULT_SEQUENCE
        logger.info(
            "ChannelOrchestratorAgent initialized",
            max_touchpoints=max_touchpoints_per_week,
            channels=[c.value for c in self.channels],
        )

    async def create_plan(
        self,
        account_ids: list[str],
        campaign_id: str,
        start_date: datetime | None = None,
    ) -> OrchestrationPlan:
        """Create a multi-channel orchestration plan.

        Args:
            account_ids: Target accounts for the campaign.
            campaign_id: The campaign identifier.
            start_date: Optional start date for the campaign.

        Returns:
            OrchestrationPlan with scheduled touchpoints.

        Raises:
            ValueError: If account_ids is empty.
        """
        if not account_ids:
            raise ValueError("account_ids cannot be empty")

        logger.info(
            "Creating orchestration plan",
            campaign_id=campaign_id,
            account_count=len(account_ids),
        )

        start = start_date or datetime.now(tz=timezone.utc)
        touchpoints: list[ChannelTouchpoint] = []

        for account_id in account_ids:
            account_touchpoints = self._plan_account_touchpoints(
                account_id=account_id,
                campaign_id=campaign_id,
                start_date=start,
            )
            touchpoints.extend(account_touchpoints)

        plan = OrchestrationPlan(
            plan_id=f"plan_{campaign_id}",
            account_ids=account_ids,
            touchpoints=touchpoints,
            channels_used=self.channels.copy(),
            start_date=start,
        )

        logger.info(
            "Orchestration plan created",
            plan_id=plan.plan_id,
            touchpoint_count=len(touchpoints),
        )
        return plan

    async def execute_plan(self, plan: OrchestrationPlan) -> dict[str, Any]:
        """Execute an orchestration plan.

        Args:
            plan: The OrchestrationPlan to execute.

        Returns:
            Execution results with status per touchpoint.

        Raises:
            ValueError: If plan has no touchpoints.
        """
        if not plan.touchpoints:
            raise ValueError("Plan has no touchpoints to execute")

        logger.info("Executing orchestration plan", plan_id=plan.plan_id)

        results: dict[str, Any] = {
            "plan_id": plan.plan_id,
            "total_touchpoints": len(plan.touchpoints),
            "successful": 0,
            "failed": 0,
            "details": [],
        }

        for touchpoint in plan.touchpoints:
            try:
                # In production, this would call channel-specific APIs
                touchpoint.status = CampaignStatus.ACTIVE
                results["successful"] += 1
                results["details"].append({
                    "touchpoint_id": touchpoint.touchpoint_id,
                    "status": "success",
                    "channel": touchpoint.channel.value,
                })
            except RuntimeError as exc:
                logger.error(
                    "Touchpoint execution failed",
                    touchpoint_id=touchpoint.touchpoint_id,
                    error=str(exc),
                )
                results["failed"] += 1
                results["details"].append({
                    "touchpoint_id": touchpoint.touchpoint_id,
                    "status": "failed",
                    "error": str(exc),
                })

        logger.info(
            "Plan execution complete",
            plan_id=plan.plan_id,
            successful=results["successful"],
            failed=results["failed"],
        )
        return results

    def _plan_account_touchpoints(
        self,
        account_id: str,
        campaign_id: str,
        start_date: datetime,
    ) -> list[ChannelTouchpoint]:
        """Plan touchpoints for a single account.

        Args:
            account_id: The account to plan for.
            campaign_id: The campaign identifier.
            start_date: Campaign start date.

        Returns:
            List of ChannelTouchpoint objects.
        """
        touchpoints: list[ChannelTouchpoint] = []

        for i, channel in enumerate(self.channels):
            touchpoint = ChannelTouchpoint(
                touchpoint_id=f"tp_{campaign_id}_{account_id}_{channel.value}",
                channel=channel,
                account_id=account_id,
                scheduled_time=start_date,  # Would add offset based on sequence
                status=CampaignStatus.SCHEDULED,
                metadata={
                    "sequence_order": i,
                    "campaign_id": campaign_id,
                },
            )
            touchpoints.append(touchpoint)

        return touchpoints
