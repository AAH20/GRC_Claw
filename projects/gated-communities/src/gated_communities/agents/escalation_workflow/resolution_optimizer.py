"""Resolution Optimizer Agent - optimizes resolution strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from escalation_workflow.agents.base import BaseAgent
from escalation_workflow.models.resolution import ResolutionCreate
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from escalation_workflow.models.escalation import Escalation


class ResolutionOptimizerInput(BaseModel):
    """Input schema for the resolution optimizer agent."""

    escalation: Escalation
    previous_resolutions: list[dict[str, Any]] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class ResolutionOptimizerAgent(BaseAgent[ResolutionOptimizerInput, ResolutionCreate]):
    """Agent that optimizes resolution strategies using LLM reasoning.

    Analyzes escalation details, historical resolutions, and available
    tools to propose optimal resolution strategies.
    """

    SYSTEM_PROMPT = """You are an expert resolution optimizer. Analyze the escalation and
propose the most effective resolution strategy.

Consider:
- Root cause analysis
- Historical resolution patterns
- Available tools and automation capabilities
- Risk assessment of proposed solutions
- Estimated time to resolve

Provide a structured resolution plan with clear steps."""

    async def run(self, input_data: ResolutionOptimizerInput) -> ResolutionCreate:
        """Generate an optimized resolution strategy.

        Args:
            input_data: Escalation details and context for optimization.

        Returns:
            ResolutionCreate: Optimized resolution proposal.
        """
        self.logger.info(
            "Optimizing resolution for escalation",
            escalation_id=str(input_data.escalation.id),
        )

        escalation = input_data.escalation
        user_content = f"""
Escalation Title: {escalation.title}
Description: {escalation.description}
Category: {escalation.category}
Priority: {escalation.priority}
Tags: {', '.join(escalation.tags)}

Previous Resolutions: {input_data.previous_resolutions}
Available Tools: {input_data.available_tools}
Context: {input_data.context}

Propose an optimized resolution strategy with:
1. Clear root cause analysis
2. Step-by-step resolution plan
3. Automation opportunities
4. Risk assessment
"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self.model.ainvoke(messages)
            return self._parse_resolution(response.content, escalation.id)
        except Exception as exc:
            self.logger.error("Resolution optimization failed", error=str(exc))
            return self._fallback_resolution(escalation.id)

    def _parse_resolution(self, content: str, escalation_id: Any) -> ResolutionCreate:
        """Parse LLM response into a ResolutionCreate.

        Args:
            content: Raw LLM response content.
            escalation_id: The escalation identifier.

        Returns:
            ResolutionCreate: Parsed resolution proposal.
        """
        return ResolutionCreate(
            escalation_id=escalation_id,
            title="AI-Optimized Resolution",
            description=content,
            resolution_type="hybrid",
            steps=[content],
            automated=False,
            confidence=0.75,
        )

    def _fallback_resolution(self, escalation_id: Any) -> ResolutionCreate:
        """Provide a fallback resolution when LLM fails.

        Args:
            escalation_id: The escalation identifier.

        Returns:
            ResolutionCreate: Default resolution proposal.
        """
        return ResolutionCreate(
            escalation_id=escalation_id,
            title="Manual Resolution Required",
            description="Automated resolution optimization failed. Manual intervention required.",
            resolution_type="manual",
            steps=[
                "Review escalation details",
                "Assign to specialist",
                "Develop resolution plan",
            ],
            automated=False,
            confidence=0.3,
        )
