"""Follow-up Automation Agent.

Automated follow-up sequences and reminders to ensure
no lead or opportunity falls through the cracks.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class FollowUpStatus(StrEnum):
    """Follow-up status values."""

    SCHEDULED = "scheduled"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class FollowUpTemplate(BaseModel):
    """Follow-up template model."""

    name: str
    subject: str
    body: str
    delay_days: int
    channel: str = "email"
    condition: str | None = None


class FollowUpAction(BaseModel):
    """Follow-up action model."""

    action_id: str
    sequence_name: str
    template: FollowUpTemplate
    scheduled_for: datetime
    status: FollowUpStatus = FollowUpStatus.SCHEDULED
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    replied_at: datetime | None = None
    contact_email: str
    deal_id: str | None = None


class FollowUpSequence(BaseModel):
    """Follow-up sequence model."""

    name: str
    description: str
    steps: list[FollowUpTemplate]
    trigger_event: str
    exit_conditions: list[str] = Field(default_factory=list)


class FollowUpAutomationAgent:
    """Agent for automating follow-up sequences.

    This agent manages automated follow-up sequences, tracks engagement,
    and ensures timely communication with contacts throughout the sales cycle.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Follow-up Automation Agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.max_followups = self.config.get("max_followups", 5)
        self.intervals = self.config.get("followup_intervals_days", [1, 3, 7, 14, 30])
        self._action_counter = 0
        logger.info("FollowUpAutomationAgent initialized", enabled=self.enabled)

    def _generate_action_id(self) -> str:
        """Generate a unique action ID.

        Returns:
            Unique action identifier.
        """
        self._action_counter += 1
        return f"fu_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self._action_counter}"

    async def create_sequence(
        self,
        name: str,
        trigger_event: str,
        contact_email: str,
        deal_id: str | None = None,
    ) -> list[FollowUpAction]:
        """Create a follow-up sequence for a contact.

        Args:
            name: Sequence name.
            trigger_event: Event that triggers the sequence.
            contact_email: Contact email address.
            deal_id: Optional related deal ID.

        Returns:
            List of scheduled follow-up actions.

        Raises:
            ValueError: If sequence parameters are invalid.
        """
        if not name:
            raise ValueError("Sequence name is required")
        if not contact_email or "@" not in contact_email:
            raise ValueError("Valid contact email is required")

        logger.info(
            "Creating follow-up sequence",
            name=name,
            contact=contact_email,
            trigger=trigger_event,
        )

        actions: list[FollowUpAction] = []
        base_time = datetime.utcnow()

        for i, interval in enumerate(self.intervals[: self.max_followups]):
            template = FollowUpTemplate(
                name=f"{name}_step_{i + 1}",
                subject=f"Following up - {name}",
                body=f"This is follow-up #{i + 1} for {name}",
                delay_days=interval,
                channel="email",
            )

            action = FollowUpAction(
                action_id=self._generate_action_id(),
                sequence_name=name,
                template=template,
                scheduled_for=base_time + timedelta(days=interval),
                contact_email=contact_email,
                deal_id=deal_id,
            )
            actions.append(action)

        logger.info("Follow-up sequence created", count=len(actions))
        return actions

    async def send_follow_up(self, action: FollowUpAction) -> FollowUpAction:
        """Send a follow-up action.

        Args:
            action: The follow-up action to send.

        Returns:
            The updated action with sent status.

        Raises:
            ValueError: If action is not in scheduled state.
        """
        if action.status != FollowUpStatus.SCHEDULED:
            raise ValueError(f"Cannot send follow-up with status {action.status}")

        action.status = FollowUpStatus.SENT
        action.sent_at = datetime.utcnow()
        logger.info(
            "Follow-up sent",
            action_id=action.action_id,
            contact=action.contact_email,
        )
        return action

    async def track_open(self, action: FollowUpAction) -> FollowUpAction:
        """Track a follow-up email open.

        Args:
            action: The follow-up action.

        Returns:
            The updated action.
        """
        action.status = FollowUpStatus.OPENED
        action.opened_at = datetime.utcnow()
        logger.info("Follow-up opened", action_id=action.action_id)
        return action

    async def track_reply(self, action: FollowUpAction) -> FollowUpAction:
        """Track a follow-up reply.

        Args:
            action: The follow-up action.

        Returns:
            The updated action.
        """
        action.status = FollowUpStatus.REPLIED
        action.replied_at = datetime.utcnow()
        logger.info("Follow-up replied", action_id=action.action_id)
        return action

    async def get_pending_actions(
        self,
        actions: list[FollowUpAction],
    ) -> list[FollowUpAction]:
        """Get all pending (scheduled and due) follow-up actions.

        Args:
            actions: List of all follow-up actions.

        Returns:
            List of pending actions that are due.
        """
        now = datetime.utcnow()
        return [
            action
            for action in actions
            if action.status == FollowUpStatus.SCHEDULED
            and action.scheduled_for <= now
        ]

    async def should_exit_sequence(
        self,
        action: FollowUpAction,
        exit_conditions: list[str],
    ) -> bool:
        """Check if a contact should exit the follow-up sequence.

        Args:
            action: The current follow-up action.
            exit_conditions: List of conditions that trigger sequence exit.

        Returns:
            True if the contact should exit the sequence.
        """
        if (
            FollowUpStatus.REPLIED in [FollowUpStatus(c) for c in exit_conditions]
            and action.status == FollowUpStatus.REPLIED
        ):
            return True
        if (
            FollowUpStatus.UNSUBSCRIBED in [FollowUpStatus(c) for c in exit_conditions]
            and action.status == FollowUpStatus.UNSUBSCRIBED
        ):
            return True
        return False

    async def get_sequence_metrics(
        self,
        actions: list[FollowUpAction],
    ) -> dict[str, Any]:
        """Get metrics for a follow-up sequence.

        Args:
            actions: List of follow-up actions.

        Returns:
            Dictionary with sequence metrics.
        """
        total = len(actions)
        if total == 0:
            return {
                "total": 0, "sent": 0, "opened": 0, "replied": 0,
                "open_rate": 0.0, "reply_rate": 0.0
            }

        sent = sum(1 for a in actions if a.status != FollowUpStatus.SCHEDULED)
        opened = sum(
            1 for a in actions
            if a.status in [FollowUpStatus.OPENED, FollowUpStatus.CLICKED, FollowUpStatus.REPLIED]
        )
        replied = sum(1 for a in actions if a.status == FollowUpStatus.REPLIED)

        return {
            "total": total,
            "sent": sent,
            "opened": opened,
            "replied": replied,
            "open_rate": round(opened / sent, 2) if sent > 0 else 0.0,
            "reply_rate": round(replied / sent, 2) if sent > 0 else 0.0,
        }
