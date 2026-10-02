"""Content agent for coordinating content creation and approval."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.negotiation import NegotiationResult, NegotiationStatus

logger = structlog.get_logger(__name__)


class ContentStatus(StrEnum):
    """Status of a content piece."""

    PENDING = "pending"
    BRIEF_SENT = "brief_sent"
    DRAFT_SUBMITTED = "draft_submitted"
    IN_REVIEW = "in_review"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


@dataclass
class ContentBrief:
    """Brief for content creation."""

    campaign_id: str
    deliverable_type: str  # e.g., "instagram_post", "tiktok_video", "youtube_short"
    topic: str
    key_messages: list[str] = field(default_factory=list)
    tone: str = "authentic"
    mandatory_elements: list[str] = field(default_factory=list)
    prohibited_elements: list[str] = field(default_factory=list)
    due_date: datetime | None = None
    reference_materials: list[str] = field(default_factory=list)
    brand_guidelines_url: str | None = None


@dataclass
class ContentPiece:
    """A piece of content created by an influencer."""

    id: str
    influencer_id: str
    campaign_id: str
    deliverable_type: str
    status: ContentStatus
    brief: ContentBrief
    draft_url: str | None = None
    published_url: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    published_at: datetime | None = None
    revision_count: int = 0
    feedback: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ContentAgent(BaseAgent[tuple[NegotiationResult, ContentBrief], ContentPiece]):
    """Agent responsible for coordinating content creation and approval workflows."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="content",
            description="Coordinates content creation, review, and approval workflows",
            max_retries=3,
            timeout_seconds=120,
        )
        super().__init__(config)
        self.max_revision_rounds = 3

    async def validate_input(
        self, input_data: tuple[NegotiationResult, ContentBrief]
    ) -> bool:
        """Validate content agent input."""
        negotiation, brief = input_data
        if negotiation.status != NegotiationStatus.ACCEPTED:
            self.logger.warning("Negotiation not accepted, cannot proceed with content")
            return False
        if not brief.deliverable_type:
            self.logger.warning("Deliverable type not specified")
            return False
        return True

    async def execute(
        self, input_data: tuple[NegotiationResult, ContentBrief]
    ) -> AgentResult[ContentPiece]:
        """Execute content coordination workflow."""
        negotiation, brief = input_data
        self.logger.info(
            "Starting content coordination",
            influencer_id=negotiation.influencer_id,
            deliverable=brief.deliverable_type,
        )

        try:
            content = ContentPiece(
                id=f"content_{datetime.utcnow().timestamp()}",
                influencer_id=negotiation.influencer_id,
                campaign_id=brief.campaign_id,
                deliverable_type=brief.deliverable_type,
                status=ContentStatus.BRIEF_SENT,
                brief=brief,
            )

            # Send brief to influencer
            await self._send_brief(negotiation.influencer_id, brief)

            self.logger.info(
                "Content brief sent",
                content_id=content.id,
                influencer_id=negotiation.influencer_id,
            )
            return AgentResult(success=True, data=content)

        except Exception as exc:
            self.logger.error("Content coordination failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    async def _send_brief(self, influencer_id: str, brief: ContentBrief) -> None:
        """Send content brief to influencer."""
        self.logger.info(
            "Sending content brief",
            influencer_id=influencer_id,
            deliverable=brief.deliverable_type,
        )
        # Placeholder: In production, this would send via email or platform DM

    async def review_content(
        self, content: ContentPiece, feedback: str, approve: bool
    ) -> ContentPiece:
        """Review submitted content and provide feedback."""
        content.reviewed_at = datetime.utcnow()
        content.feedback.append(feedback)

        if approve:
            content.status = ContentStatus.APPROVED
            self.logger.info("Content approved", content_id=content.id)
        else:
            content.revision_count += 1
            if content.revision_count >= self.max_revision_rounds:
                content.status = ContentStatus.REJECTED
                self.logger.warning(
                    "Content rejected after max revisions", content_id=content.id
                )
            else:
                content.status = ContentStatus.REVISION_REQUESTED
                self.logger.info(
                    "Content revision requested",
                    content_id=content.id,
                    revision=content.revision_count,
                )

        return content
