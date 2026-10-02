"""Reminder Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from interview_scheduler.models.interview import Interview
from interview_scheduler.models.reminder import Reminder, ReminderCreate, ReminderType

logger = logging.getLogger(__name__)


class ReminderAgent:
    """Agent responsible for managing interview reminders.

    Uses LangChain DeepAgents to intelligently schedule, send, and
    track reminders for upcoming interviews.
    """

    def __init__(
        self,
        default_reminder_minutes: list[int] | None = None,
    ) -> None:
        """Initialize the Reminder Agent.

        Args:
            default_reminder_minutes: Default minutes before interview for reminders.
        """
        self.default_reminder_minutes = default_reminder_minutes or [1440, 60, 15]
        self._agent: Any = None

    async def _get_agent(self) -> Any:
        """Lazy-initialize the LangChain DeepAgent."""
        if self._agent is None:
            try:
                from langchain_deepagents import create_deep_agent

                self._agent = create_deep_agent(
                    tools=[self._send_reminder_tool, self._schedule_reminder_tool],
                    instructions=(
                        "You are a reminder agent. Schedule and send reminders "
                        "for upcoming interviews. Handle retries and track delivery."
                    ),
                )
            except ImportError:
                logger.warning("langchain-deepagents not available, using direct reminder management")
                self._agent = None
        return self._agent

    async def _send_reminder_tool(
        self, reminder_type: str, recipient: str, subject: str, message: str
    ) -> bool:
        """Tool for sending a reminder."""
        return await self.send_reminder(
            ReminderType(reminder_type), recipient, subject, message
        )

    async def _schedule_reminder_tool(
        self, interview_id: str, minutes_before: int, reminder_type: str, recipient: str
    ) -> str:
        """Tool for scheduling a reminder."""
        reminder = self.create_reminder(
            interview_id=interview_id,
            reminder_type=ReminderType(reminder_type),
            minutes_before=minutes_before,
            recipient=recipient,
        )
        return reminder.id

    def create_reminder(
        self,
        interview_id: str,
        reminder_type: ReminderType,
        minutes_before: int,
        recipient: str,
        subject: str | None = None,
        message: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> Reminder:
        """Create a reminder for an interview.

        Args:
            interview_id: The interview ID.
            reminder_type: Type of reminder.
            minutes_before: Minutes before the interview to send.
            recipient: Recipient address.
            subject: Optional subject line.
            message: Optional message body.
            scheduled_at: Optional explicit scheduled time.

        Returns:
            The created reminder.
        """
        return Reminder(
            interview_id=interview_id,
            reminder_type=reminder_type,
            minutes_before=minutes_before,
            recipient=recipient,
            subject=subject or f"Interview Reminder",
            message=message or f"This is a reminder for your upcoming interview.",
            scheduled_at=scheduled_at or datetime.utcnow(),
        )

    def create_default_reminders(
        self,
        interview: Interview,
    ) -> list[Reminder]:
        """Create default reminders for an interview.

        Args:
            interview: The interview to create reminders for.

        Returns:
            List of created reminders.
        """
        if not interview.scheduled_at:
            return []

        reminders: list[Reminder] = []
        for minutes_before in self.default_reminder_minutes:
            scheduled_at = interview.scheduled_at - timedelta(minutes=minutes_before)
            for participant in interview.participants:
                reminder = self.create_reminder(
                    interview_id=interview.id,
                    reminder_type=ReminderType.EMAIL,
                    minutes_before=minutes_before,
                    recipient=participant.email,
                    subject=f"Reminder: {interview.title} in {minutes_before} minutes",
                    message=(
                        f"This is a reminder that your interview '{interview.title}' "
                        f"is scheduled in {minutes_before} minutes."
                    ),
                    scheduled_at=scheduled_at,
                )
                reminders.append(reminder)
        return reminders

    async def send_reminder(
        self,
        reminder_type: ReminderType,
        recipient: str,
        subject: str,
        message: str,
    ) -> bool:
        """Send a reminder to a recipient.

        Args:
            reminder_type: Type of reminder to send.
            recipient: Recipient address.
            subject: Reminder subject.
            message: Reminder message body.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            if reminder_type == ReminderType.EMAIL:
                await self._send_email(recipient, subject, message)
            elif reminder_type == ReminderType.SMS:
                await self._send_sms(recipient, message)
            elif reminder_type == ReminderType.SLACK:
                await self._send_slack(recipient, message)
            elif reminder_type == ReminderType.WEBHOOK:
                await self._send_webhook(recipient, {"subject": subject, "message": message})
            else:
                logger.warning("Unsupported reminder type: %s", reminder_type)
                return False
            return True
        except Exception as exc:
            logger.error("Failed to send %s reminder to %s: %s", reminder_type, recipient, exc)
            return False

    async def _send_email(self, recipient: str, subject: str, message: str) -> None:
        """Send an email reminder."""
        logger.info("Sending email to %s: %s", recipient, subject)
        # Integration with email service would go here

    async def _send_sms(self, recipient: str, message: str) -> None:
        """Send an SMS reminder."""
        logger.info("Sending SMS to %s", recipient)
        # Integration with SMS service would go here

    async def _send_slack(self, recipient: str, message: str) -> None:
        """Send a Slack reminder."""
        logger.info("Sending Slack message to %s", recipient)
        # Integration with Slack would go here

    async def _send_webhook(self, url: str, payload: dict[str, Any]) -> None:
        """Send a webhook reminder."""
        import httpx

        logger.info("Sending webhook to %s", url)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

    def get_pending_reminders(
        self,
        reminders: list[Reminder],
        now: datetime | None = None,
    ) -> list[Reminder]:
        """Get reminders that are due to be sent.

        Args:
            reminders: All reminders to check.
            now: Reference time (defaults to current UTC).

        Returns:
            List of pending reminders.
        """
        if now is None:
            now = datetime.utcnow()
        return [
            r for r in reminders
            if r.status == "pending" and r.scheduled_at <= now
        ]

    def cancel_reminders_for_interview(
        self,
        reminders: list[Reminder],
        interview_id: str,
    ) -> list[Reminder]:
        """Cancel all pending reminders for an interview.

        Args:
            reminders: All reminders.
            interview_id: The interview ID.

        Returns:
            List of cancelled reminders.
        """
        cancelled: list[Reminder] = []
        for reminder in reminders:
            if reminder.interview_id == interview_id and reminder.status == "pending":
                reminder.status = "cancelled"
                cancelled.append(reminder)
        return cancelled
