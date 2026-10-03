"""Priority Router Agent - assesses and routes escalations by priority."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from escalation_workflow.agents.base import BaseAgent
from escalation_workflow.models.priority import (PriorityAssessment,
                                                 PriorityLevel)
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from escalation_workflow.models.escalation import Escalation


class PriorityRouterInput(BaseModel):
    """Input schema for the priority router agent."""

    escalation: Escalation
    context: dict[str, Any] = Field(default_factory=dict)


class PriorityRouterAgent(BaseAgent[PriorityRouterInput, PriorityAssessment]):
    """Agent that assesses escalation priority using LLM reasoning.

    Analyzes escalation content, context, and metadata to determine
    the appropriate priority level with confidence scoring.
    """

    SYSTEM_PROMPT = """You are an expert escalation priority router. Analyze the given escalation
and determine the appropriate priority level (critical, high, medium, low).

Consider these factors:
- Business impact and urgency
- Number of affected users or systems
- Data sensitivity and compliance implications
- Time sensitivity and deadlines
- Available context and historical patterns

Provide a confidence score (0.0-1.0) and clear reasoning for your assessment.
Return the recommended SLA in minutes based on the priority level."""

    async def run(self, input_data: PriorityRouterInput) -> PriorityAssessment:
        """Assess and route an escalation by priority.

        Args:
            input_data: The escalation and context to assess.

        Returns:
            PriorityAssessment: The assessed priority with confidence and reasoning.
        """
        self.logger.info(
            "Assessing priority for escalation",
            escalation_id=str(input_data.escalation.id),
        )

        escalation = input_data.escalation
        user_content = f"""
Escalation Title: {escalation.title}
Description: {escalation.description}
Category: {escalation.category}
Source: {escalation.source}
Tags: {', '.join(escalation.tags)}
Metadata: {input_data.context}

Assess the priority and provide:
1. Priority level (critical, high, medium, low)
2. Confidence score (0.0-1.0)
3. Reasoning for the assessment
4. Recommended SLA in minutes
"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self.model.ainvoke(messages)
            return self._parse_response(response.content, escalation.id)
        except Exception as exc:
            self.logger.error("Priority assessment failed", error=str(exc))
            return self._fallback_assessment(escalation.id)

    def _parse_response(self, content: str, escalation_id: Any) -> PriorityAssessment:
        """Parse the LLM response into a PriorityAssessment.

        Args:
            content: Raw LLM response content.
            escalation_id: The escalation identifier.

        Returns:
            PriorityAssessment: Parsed assessment result.
        """
        content_lower = content.lower()

        if "critical" in content_lower:
            priority = PriorityLevel.CRITICAL
            sla = 15
        elif "high" in content_lower:
            priority = PriorityLevel.HIGH
            sla = 30
        elif "low" in content_lower:
            priority = PriorityLevel.LOW
            sla = 480
        else:
            priority = PriorityLevel.MEDIUM
            sla = 120

        return PriorityAssessment(
            escalation_id=escalation_id,
            assessed_priority=priority,
            confidence=0.85,
            reasoning=content,
            recommended_sla_minutes=sla,
        )

    def _fallback_assessment(self, escalation_id: Any) -> PriorityAssessment:
        """Provide a fallback assessment when LLM fails.

        Args:
            escalation_id: The escalation identifier.

        Returns:
            PriorityAssessment: Default medium priority assessment.
        """
        return PriorityAssessment(
            escalation_id=escalation_id,
            assessed_priority=PriorityLevel.MEDIUM,
            confidence=0.5,
            reasoning="Fallback assessment due to LLM failure",
            recommended_sla_minutes=120,
        )
