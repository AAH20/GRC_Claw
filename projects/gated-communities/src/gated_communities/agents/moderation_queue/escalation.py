"""Escalation Agent for managing high-priority moderation cases."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from moderation_queue.agents.base import AgentConfig, BaseAgent
from moderation_queue.models import Escalation, ModerationItem, PriorityLevel


class EscalationInput(BaseModel):
    """Input for the Escalation Agent."""

    item: ModerationItem = Field(..., description="Moderation item to escalate")
    reason: str = Field(..., description="Reason for escalation")
    available_teams: list[dict[str, Any]] = Field(
        default_factory=list, description="Available escalation teams"
    )
    escalation_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Previous escalation history"
    )
    urgency_indicators: dict[str, Any] = Field(
        default_factory=dict, description="Urgency indicators"
    )


class EscalationOutput(BaseModel):
    """Output from the Escalation Agent."""

    escalation_id: str = Field(..., description="Escalation record ID")
    assigned_team: str = Field(..., description="Assigned team ID")
    assigned_reviewer: str | None = Field(default=None, description="Assigned reviewer ID")
    priority: PriorityLevel = Field(..., description="Escalation priority")
    sla_minutes: int = Field(..., description="SLA in minutes")
    required_actions: list[str] = Field(
        default_factory=list, description="Required actions"
    )
    reasoning: str = Field(default="", description="Escalation reasoning")
    notify_channels: list[str] = Field(
        default_factory=list, description="Channels to notify"
    )


SYSTEM_PROMPT = """You are an AI escalation manager for content moderation.
Your task is to handle high-priority or complex moderation cases that require escalation.

Consider:
- Severity and potential impact
- SLA requirements
- Team expertise and availability
- Communication and notification needs
- Documentation and compliance

Provide comprehensive escalation plans with clear ownership and timelines.
Always respond with valid JSON matching the expected schema."""


class EscalationAgent(BaseAgent[EscalationInput, EscalationOutput]):
    """Agent that manages escalation of high-priority moderation items.

    This agent determines the appropriate escalation path, assigns teams,
    and sets SLAs for critical moderation cases.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the Escalation Agent.

        Args:
            settings: Application settings.
        """
        config = AgentConfig(
            name="EscalationAgent",
            description="AI agent for managing moderation escalations",
            temperature=0.0,
            max_tokens=800,
        )
        super().__init__(config, settings)

    async def process(self, input_data: EscalationInput) -> EscalationOutput:
        """Process an escalation request.

        Args:
            input_data: Input containing item and escalation context.

        Returns:
            EscalationOutput: Escalation plan.
        """
        item = input_data.item

        user_content = f"""Handle this escalation:

Content Type: {item.content_type.value}
Content Preview: {item.content[:300]}
Priority Score: {item.priority_score}
Priority Level: {item.priority_level}
Reason: {input_data.reason}
Tags: {item.tags}

Available Teams: {json.dumps(input_data.available_teams)}
Escalation History: {json.dumps(input_data.escalation_history)}
Urgency Indicators: {json.dumps(input_data.urgency_indicators)}

Provide:
1. escalation_id: string (UUID)
2. assigned_team: string
3. assigned_reviewer: string or null
4. priority: one of "low", "medium", "high", "critical"
5. sla_minutes: integer
6. required_actions: list of strings
7. reasoning: brief explanation
8. notify_channels: list of strings

Respond with JSON only."""

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self._model.ainvoke(messages)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            try:
                data = json.loads(response.content)
                return EscalationOutput.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback escalation
        return self._fallback_escalate(input_data)

    def _fallback_escalate(self, input_data: EscalationInput) -> EscalationOutput:
        """Fallback escalation when AI is unavailable.

        Args:
            input_data: Input data.

        Returns:
            EscalationOutput: Fallback escalation plan.
        """
        item = input_data.item
        priority = item.priority_level or PriorityLevel.HIGH

        # Determine SLA based on priority
        sla_map = {
            PriorityLevel.CRITICAL: 15,
            PriorityLevel.HIGH: 60,
            PriorityLevel.MEDIUM: 240,
            PriorityLevel.LOW: 1440,
        }
        sla = sla_map.get(priority, 240)

        # Assign to first available team
        teams = input_data.available_teams
        assigned_team = teams[0].get("id", "default_team") if teams else "default_team"

        return EscalationOutput(
            escalation_id=str(item.id),
            assigned_team=assigned_team,
            assigned_reviewer=None,
            priority=priority,
            sla_minutes=sla,
            required_actions=["Review content", "Document decision", "Notify stakeholders"],
            reasoning="Fallback escalation (AI model unavailable)",
            notify_channels=["slack", "email"],
        )

    def create_escalation_record(
        self, input_data: EscalationInput, output: EscalationOutput
    ) -> Escalation:
        """Create an Escalation record from agent output.

        Args:
            input_data: Escalation input.
            output: Agent output.

        Returns:
            Escalation: Complete escalation record.
        """
        return Escalation(
            item_id=input_data.item.id,
            reason=input_data.reason,
            assigned_to=output.assigned_reviewer,
            priority=output.priority,
            metadata={
                "team": output.assigned_team,
                "sla_minutes": output.sla_minutes,
                "required_actions": output.required_actions,
                "notify_channels": output.notify_channels,
            },
        )
