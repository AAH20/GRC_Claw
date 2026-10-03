"""SLA Tracker Agent - monitors and tracks SLA compliance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from escalation_workflow.agents.base import BaseAgent
from escalation_workflow.models.sla import SLA, SLABreach, SLAStatus
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class SLATrackerInput(BaseModel):
    """Input schema for the SLA tracker agent."""

    escalation_id: str
    priority: str
    started_at: datetime
    response_deadline: datetime
    resolution_deadline: datetime
    current_time: datetime | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class SLATrackerAgent(BaseAgent[SLATrackerInput, SLA]):
    """Agent that tracks SLA compliance and predicts breach risk.

    Monitors escalation progress against SLA deadlines, calculates
    remaining time, and provides breach risk assessments.
    """

    SYSTEM_PROMPT = """You are an expert SLA tracker. Monitor escalation progress against
service level agreements and provide:
1. Current SLA status (active, at_risk, breached, met)
2. Time remaining before breach
3. Risk assessment and recommendations
4. Escalation urgency level"""

    async def run(self, input_data: SLATrackerInput) -> SLA:
        """Track SLA status for an escalation.

        Args:
            input_data: SLA tracking input with deadlines and timing info.

        Returns:
            SLA: Current SLA status with breach risk assessment.
        """
        self.logger.info(
            "Tracking SLA for escalation",
            escalation_id=input_data.escalation_id,
        )

        now = input_data.current_time or datetime.utcnow()
        response_remaining = (input_data.response_deadline - now).total_seconds() / 60
        resolution_remaining = (
            input_data.resolution_deadline - now
        ).total_seconds() / 60

        status = self._determine_status(response_remaining, resolution_remaining)
        elapsed = (now - input_data.started_at).total_seconds() / 60

        # Use LLM for risk assessment
        await self._assess_risk(input_data, response_remaining, resolution_remaining)

        return SLA(
            escalation_id=input_data.escalation_id,
            priority=input_data.priority,
            response_time_minutes=int(
                (input_data.response_deadline - input_data.started_at).total_seconds()
                / 60
            ),
            resolution_time_minutes=int(
                (input_data.resolution_deadline - input_data.started_at).total_seconds()
                / 60
            ),
            status=status,
            started_at=input_data.started_at,
            response_deadline=input_data.response_deadline,
            resolution_deadline=input_data.resolution_deadline,
            elapsed_minutes=max(0, elapsed),
            remaining_minutes=max(0, resolution_remaining),
        )

    def _determine_status(
        self, response_remaining: float, resolution_remaining: float
    ) -> SLAStatus:
        """Determine SLA status based on remaining time.

        Args:
            response_remaining: Minutes remaining for response.
            resolution_remaining: Minutes remaining for resolution.

        Returns:
            SLAStatus: Current SLA status.
        """
        if response_remaining < 0 or resolution_remaining < 0:
            return SLAStatus.BREACHED
        elif response_remaining < 15 or resolution_remaining < 30:
            return SLAStatus.AT_RISK
        return SLAStatus.ACTIVE

    async def _assess_risk(
        self,
        input_data: SLATrackerInput,
        response_remaining: float,
        resolution_remaining: float,
    ) -> str:
        """Use LLM to assess breach risk.

        Args:
            input_data: SLA tracking input.
            response_remaining: Minutes remaining for response.
            resolution_remaining: Minutes remaining for resolution.

        Returns:
            str: Risk assessment text.
        """
        user_content = f"""
Escalation ID: {input_data.escalation_id}
Priority: {input_data.priority}
Response remaining: {response_remaining:.1f} minutes
Resolution remaining: {resolution_remaining:.1f} minutes
Context: {input_data.context}

Assess the breach risk and provide recommendations.
"""
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self.model.ainvoke(messages)
            return response.content
        except Exception as exc:
            self.logger.error("Risk assessment failed", error=str(exc))
            return "Risk assessment unavailable"

    def calculate_breach(
        self, sla: SLA, breach_time: datetime | None = None
    ) -> SLABreach:
        """Calculate and record an SLA breach.

        Args:
            sla: The SLA that was breached.
            breach_time: When the breach occurred. Defaults to now.

        Returns:
            SLABreach: The recorded breach event.
        """
        now = breach_time or datetime.utcnow()
        overdue = max(0, (now - sla.resolution_deadline).total_seconds() / 60)

        return SLABreach(
            sla_id=sla.id,
            escalation_id=sla.escalation_id,
            breached_at=now,
            minutes_overdue=overdue,
            severity="critical" if overdue > 60 else "high",
        )
