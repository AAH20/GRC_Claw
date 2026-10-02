"""Outreach agent for managing influencer communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.vetting import VettingReport

logger = structlog.get_logger(__name__)


class OutreachStatus(StrEnum):
    """Status of an outreach attempt."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    INTERESTED = "interested"
    DECLINED = "declined"
    NO_RESPONSE = "no_response"


@dataclass
class OutreachMessage:
    """An outreach message to an influencer."""

    subject: str
    body: str
    template_id: str | None = None
    personalization_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutreachResult:
    """Result of an outreach attempt."""

    influencer_id: str
    status: OutreachStatus
    message: OutreachMessage
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    replied_at: datetime | None = None
    follow_up_count: int = 0
    next_follow_up: datetime | None = None
    notes: str = ""


class OutreachAgent(BaseAgent[tuple[VettingReport, OutreachMessage], OutreachResult]):
    """Agent responsible for managing influencer outreach and communication."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="outreach",
            description="Manages initial contact and communication with influencers",
            max_retries=3,
            timeout_seconds=60,
        )
        super().__init__(config)

    async def validate_input(
        self, input_data: tuple[VettingReport, OutreachMessage]
    ) -> bool:
        """Validate outreach input."""
        vetting_report, message = input_data
        if vetting_report is None or not vetting_report.is_approved:
            self.logger.warning("Influencer not approved for outreach")
            return False
        if not message.body or len(message.body.strip()) < 10:
            self.logger.warning("Message body too short")
            return False
        return True

    async def execute(
        self, input_data: tuple[VettingReport, OutreachMessage]
    ) -> AgentResult[OutreachResult]:
        """Execute outreach to an influencer."""
        vetting_report, message = input_data
        influencer = vetting_report.influencer
        self.logger.info("Starting outreach", username=influencer.username)

        try:
            # Personalize message
            personalized = self._personalize_message(message, influencer)

            # Send message via appropriate channel
            result = await self._send_message(influencer, personalized)

            self.logger.info(
                "Outreach completed",
                username=influencer.username,
                status=result.status.value,
            )
            return AgentResult(success=True, data=result)

        except Exception as exc:
            self.logger.error("Outreach failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    def _personalize_message(
        self, message: OutreachMessage, influencer: Any
    ) -> OutreachMessage:
        """Personalize outreach message with influencer data."""
        body = message.body
        replacements = {
            "{name}": influencer.display_name or influencer.username,
            "{username}": influencer.username,
            "{followers}": str(influencer.follower_count),
            "{platform}": influencer.platform,
            "{categories}": ", ".join(influencer.categories),
        }
        for key, value in replacements.items():
            body = body.replace(key, value)

        return OutreachMessage(
            subject=message.subject.replace(
                "{name}", influencer.display_name or influencer.username
            ),
            body=body,
            template_id=message.template_id,
            personalization_data=message.personalization_data,
        )

    async def _send_message(
        self, influencer: Any, message: OutreachMessage
    ) -> OutreachResult:
        """Send message to influencer via platform-appropriate channel."""
        # Placeholder: In production, this would use platform APIs
        # (Instagram DM, TikTok messages, YouTube business inquiries, email)
        self.logger.info(
            "Sending message",
            platform=influencer.platform,
            username=influencer.username,
        )

        return OutreachResult(
            influencer_id=influencer.platform_id,
            status=OutreachStatus.SENT,
            message=message,
            sent_at=datetime.utcnow(),
        )

    async def schedule_follow_up(
        self, previous_result: OutreachResult, follow_up_message: OutreachMessage
    ) -> OutreachResult:
        """Schedule a follow-up message for non-responsive influencers."""
        if previous_result.follow_up_count >= 3:
            self.logger.warning(
                "Max follow-ups reached",
                influencer_id=previous_result.influencer_id,
            )
            return OutreachResult(
                influencer_id=previous_result.influencer_id,
                status=OutreachStatus.NO_RESPONSE,
                message=follow_up_message,
                follow_up_count=previous_result.follow_up_count,
                notes="Maximum follow-ups reached",
            )

        return OutreachResult(
            influencer_id=previous_result.influencer_id,
            status=OutreachStatus.PENDING,
            message=follow_up_message,
            follow_up_count=previous_result.follow_up_count + 1,
            next_follow_up=datetime.utcnow(),
        )
