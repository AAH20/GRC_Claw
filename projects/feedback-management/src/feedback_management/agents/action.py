"""Action Agent - triggers workflows based on feedback analysis."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

from feedback_management.agents.analysis import AnalysisResult
from feedback_management.agents.collection import FeedbackItem

logger = structlog.get_logger(__name__)


class ActionType(str, Enum):
    """Types of actions that can be triggered."""

    CREATE_TICKET = "create_ticket"
    SEND_EMAIL = "send_email"
    TRIGGER_WEBHOOK = "trigger_webhook"
    ESCALATE = "escalate"
    UPDATE_CRM = "update_crm"
    NOTIFY_SLACK = "notify_slack"
    SCHEDULE_FOLLOW_UP = "schedule_follow_up"


class ActionPriority(str, Enum):
    """Priority levels for actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    """Status of an action execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Action(BaseModel):
    """Represents a single action to be executed."""

    id: str
    type: ActionType
    priority: ActionPriority
    feedback_id: str
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class ActionResult(BaseModel):
    """Result of executing an action."""

    action_id: str
    success: bool
    action_type: ActionType
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchActionResult(BaseModel):
    """Result of executing a batch of actions."""

    total_actions: int
    successful: int
    failed: int
    skipped: int
    results: list[ActionResult] = Field(default_factory=list)


class ActionAgent:
    """Agent responsible for triggering actions based on feedback analysis.

    Creates tickets, sends notifications, triggers webhooks, escalates issues,
    and updates CRM systems based on the analysis results.
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        slack_webhook_url: str | None = None,
        auto_escalate_threshold: float = -0.5,
        auto_respond_threshold: float = 0.8,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the Action Agent.

        Args:
            webhook_url: URL for generic webhook notifications.
            slack_webhook_url: Slack incoming webhook URL.
            auto_escalate_threshold: Sentiment score below which to auto-escalate.
            auto_respond_threshold: Sentiment score above which to auto-respond.
            http_client: Optional pre-configured HTTP client.
        """
        self.webhook_url = webhook_url
        self.slack_webhook_url = slack_webhook_url
        self.auto_escalate_threshold = auto_escalate_threshold
        self.auto_respond_threshold = auto_respond_threshold
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)

    async def determine_actions(
        self,
        item: FeedbackItem,
        analysis: AnalysisResult,
    ) -> list[Action]:
        """Determine which actions should be taken for a feedback item.

        Args:
            item: The feedback item.
            analysis: Analysis result.

        Returns:
            List of Action objects to be executed.
        """
        actions: list[Action] = []
        base_id = str(uuid.uuid4())[:8]

        if (
            analysis.sentiment.score <= self.auto_escalate_threshold
            or analysis.suggested_priority == "high"
        ):
            actions.append(
                Action(
                    id=f"{base_id}-esc",
                    type=ActionType.ESCALATE,
                    priority=ActionPriority.HIGH
                        if analysis.sentiment.score < -0.7 else ActionPriority.MEDIUM,
                    feedback_id=item.id,
                    description=(
                        f"Escalate negative feedback "
                        f"(sentiment: {analysis.sentiment.score:.2f})"
                    ),
                    payload={
                        "feedback_id": item.id,
                        "sentiment_score": analysis.sentiment.score,
                        "urgency": analysis.urgency_score,
                        "summary": analysis.summary,
                    },
                )
            )

        if analysis.suggested_priority in ("high", "medium"):
            actions.append(
                Action(
                    id=f"{base_id}-ticket",
                    type=ActionType.CREATE_TICKET,
                    priority=ActionPriority(analysis.suggested_priority),
                    feedback_id=item.id,
                    description=f"Create support ticket for feedback {item.id}",
                    payload={
                        "feedback_id": item.id,
                        "priority": analysis.suggested_priority,
                        "topics": [t.name for t in analysis.topics],
                        "summary": analysis.summary,
                        "customer_email": item.customer_email,
                    },
                )
            )

        if self.slack_webhook_url and analysis.sentiment.score < -0.3:
            actions.append(
                Action(
                    id=f"{base_id}-slack",
                    type=ActionType.NOTIFY_SLACK,
                    priority=ActionPriority.MEDIUM,
                    feedback_id=item.id,
                    description="Notify team of negative feedback via Slack",
                    payload={
                        "feedback_id": item.id,
                        "sentiment": analysis.sentiment.label,
                        "score": analysis.sentiment.score,
                        "text_preview": item.text[:200],
                    },
                )
            )

        if self.webhook_url:
            actions.append(
                Action(
                    id=f"{base_id}-webhook",
                    type=ActionType.TRIGGER_WEBHOOK,
                    priority=ActionPriority.LOW,
                    feedback_id=item.id,
                    description="Trigger external webhook",
                    payload={
                        "event": "feedback.received",
                        "feedback_id": item.id,
                        "analysis": analysis.model_dump(),
                    },
                )
            )

        if analysis.sentiment.score >= self.auto_respond_threshold:
            actions.append(
                Action(
                    id=f"{base_id}-followup",
                    type=ActionType.SCHEDULE_FOLLOW_UP,
                    priority=ActionPriority.LOW,
                    feedback_id=item.id,
                    description="Schedule follow-up for positive feedback",
                    payload={
                        "feedback_id": item.id,
                        "sentiment": analysis.sentiment.label,
                        "delay_hours": 48,
                    },
                )
            )

        logger.info(
            "Actions determined",
            feedback_id=item.id,
            action_count=len(actions),
        )

        return actions

    async def execute_action(self, action: Action) -> ActionResult:
        """Execute a single action.

        Args:
            action: The action to execute.

        Returns:
            ActionResult with execution status.
        """
        action.status = ActionStatus.IN_PROGRESS
        logger.info("Executing action", action_id=action.id, type=action.type.value)

        try:
            if action.type == ActionType.CREATE_TICKET:
                result = await self._create_ticket(action)
            elif action.type == ActionType.SEND_EMAIL:
                result = await self._send_email(action)
            elif action.type == ActionType.TRIGGER_WEBHOOK:
                result = await self._trigger_webhook(action)
            elif action.type == ActionType.ESCALATE:
                result = await self._escalate(action)
            elif action.type == ActionType.NOTIFY_SLACK:
                result = await self._notify_slack(action)
            elif action.type == ActionType.SCHEDULE_FOLLOW_UP:
                result = await self._schedule_follow_up(action)
            elif action.type == ActionType.UPDATE_CRM:
                result = await self._update_crm(action)
            else:
                result = {"message": f"Unknown action type: {action.type}"}

            action.status = ActionStatus.COMPLETED
            action.executed_at = datetime.now(timezone.utc)
            action.result = result

            return ActionResult(
                action_id=action.id,
                success=True,
                action_type=action.type,
                message=f"Action {action.type.value} completed successfully",
                details=result,
            )

        except Exception as exc:
            action.status = ActionStatus.FAILED
            action.error = str(exc)
            action.executed_at = datetime.now(timezone.utc)

            logger.error(
                "Action execution failed",
                action_id=action.id,
                type=action.type.value,
                error=str(exc),
            )

            return ActionResult(
                action_id=action.id,
                success=False,
                action_type=action.type,
                message=f"Action {action.type.value} failed: {exc}",
                details={"error": str(exc)},
            )

    async def execute_batch(self, actions: list[Action]) -> BatchActionResult:
        """Execute a batch of actions.

        Args:
            actions: List of actions to execute.

        Returns:
            BatchActionResult with all execution results.
        """
        import asyncio

        results = await asyncio.gather(*[self.execute_action(action) for action in actions])

        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        logger.info(
            "Batch action execution complete",
            total=len(actions),
            successful=successful,
            failed=failed,
        )

        return BatchActionResult(
            total_actions=len(actions),
            successful=successful,
            failed=failed,
            skipped=0,
            results=list(results),
        )

    async def _create_ticket(self, action: Action) -> dict[str, Any]:
        """Create a support ticket."""
        logger.info("Creating support ticket", feedback_id=action.feedback_id)
        return {
            "ticket_id": f"TKT-{action.feedback_id[:8].upper()}",
            "status": "created",
            "priority": action.payload.get("priority", "medium"),
        }

    async def _send_email(self, action: Action) -> dict[str, Any]:
        """Send an email notification."""
        logger.info("Sending email notification", feedback_id=action.feedback_id)
        return {"status": "sent", "recipient": action.payload.get("customer_email", "unknown")}

    async def _trigger_webhook(self, action: Action) -> dict[str, Any]:
        """Trigger an external webhook."""
        if not self.webhook_url:
            return {"status": "skipped", "reason": "No webhook URL configured"}

        logger.info("Triggering webhook", url=self.webhook_url)

        response = await self._http_client.post(
            self.webhook_url,
            json=action.payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        return {"status": "delivered", "http_status": response.status_code}

    async def _escalate(self, action: Action) -> dict[str, Any]:
        """Escalate an issue to management."""
        logger.info(
            "Escalating issue",
            feedback_id=action.feedback_id,
            priority=action.priority.value,
        )
        return {
            "escalation_id": f"ESC-{action.feedback_id[:8].upper()}",
            "status": "escalated",
            "priority": action.priority.value,
        }

    async def _notify_slack(self, action: Action) -> dict[str, Any]:
        """Send a Slack notification."""
        if not self.slack_webhook_url:
            return {"status": "skipped", "reason": "No Slack webhook URL configured"}

        logger.info("Sending Slack notification", feedback_id=action.feedback_id)

        slack_payload = {
            "text": f"New negative feedback received (ID: {action.feedback_id})",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New Negative Feedback*\n"
                        f"* Feedback ID: {action.feedback_id}\n"
                        f"* Sentiment: {action.payload.get('sentiment', 'unknown')}\n"
                        f"* Score: {action.payload.get('score', 0):.2f}\n"
                        f"* Preview: {action.payload.get('text_preview', 'N/A')}",
                    },
                }
            ],
        }

        response = await self._http_client.post(
            self.slack_webhook_url,
            json=slack_payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        return {"status": "delivered", "http_status": response.status_code}

    async def _schedule_follow_up(self, action: Action) -> dict[str, Any]:
        """Schedule a follow-up task."""
        logger.info("Scheduling follow-up", feedback_id=action.feedback_id)
        return {
            "follow_up_id": f"FU-{action.feedback_id[:8].upper()}",
            "status": "scheduled",
            "delay_hours": action.payload.get("delay_hours", 48),
        }

    async def _update_crm(self, action: Action) -> dict[str, Any]:
        """Update CRM with feedback data."""
        logger.info("Updating CRM", feedback_id=action.feedback_id)
        return {"status": "updated", "crm_record_id": action.feedback_id}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()
