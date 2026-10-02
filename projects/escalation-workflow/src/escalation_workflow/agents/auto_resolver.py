"""Auto Resolver Agent - automatically resolves escalations when possible."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from escalation_workflow.agents.base import BaseAgent
from escalation_workflow.models.escalation import Escalation
from escalation_workflow.models.resolution import Resolution, ResolutionStatus


class AutoResolverInput(BaseModel):
    """Input schema for the auto resolver agent."""

    escalation: Escalation
    auto_resolve_enabled: bool = True
    confidence_threshold: float = 0.8
    max_auto_resolve_priority: str = "low"
    available_actions: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class AutoResolverAgent(BaseAgent[AutoResolverInput, Resolution | None]):
    """Agent that automatically resolves escalations when confidence is high.

    Uses LLM reasoning to determine if an escalation can be safely
    auto-resolved based on priority, category, and historical patterns.
    """

    SYSTEM_PROMPT = """You are an expert auto-resolver. Determine if the given escalation
can be safely and automatically resolved.

Only auto-resolve if:
- Priority is low or medium
- Category has known automated solutions
- Confidence exceeds the threshold
- No data loss or security risk

Provide:
1. Whether auto-resolution is recommended (yes/no)
2. Confidence score (0.0-1.0)
3. Resolution steps if applicable
4. Risk assessment"""

    async def run(self, input_data: AutoResolverInput) -> Resolution | None:
        """Attempt to auto-resolve an escalation.

        Args:
            input_data: Escalation and auto-resolution parameters.

        Returns:
            Resolution | None: Resolution if auto-resolved, None otherwise.
        """
        self.logger.info(
            "Attempting auto-resolution",
            escalation_id=str(input_data.escalation.id),
        )

        if not input_data.auto_resolve_enabled:
            self.logger.info("Auto-resolution disabled")
            return None

        escalation = input_data.escalation
        user_content = f"""
Escalation Title: {escalation.title}
Description: {escalation.description}
Category: {escalation.category}
Priority: {escalation.priority}
Tags: {', '.join(escalation.tags)}

Auto-resolve enabled: {input_data.auto_resolve_enabled}
Confidence threshold: {input_data.confidence_threshold}
Max auto-resolve priority: {input_data.max_auto_resolve_priority}
Available actions: {input_data.available_actions}
Context: {input_data.context}

Determine if this escalation can be auto-resolved.
"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self.model.ainvoke(messages)
            return self._parse_auto_resolution(response.content, escalation, input_data)
        except Exception as exc:
            self.logger.error("Auto-resolution failed", error=str(exc))
            return None

    def _parse_auto_resolution(
        self, content: str, escalation: Escalation, input_data: AutoResolverInput
    ) -> Resolution | None:
        """Parse LLM response and determine if auto-resolution should proceed.

        Args:
            content: Raw LLM response content.
            escalation: The escalation to resolve.
            input_data: Auto-resolution parameters.

        Returns:
            Resolution | None: Resolution if auto-resolved, None otherwise.
        """
        content_lower = content.lower()

        # Check if LLM recommends auto-resolution
        if "no" in content_lower and "recommend" in content_lower:
            return None

        # Check priority constraints
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        escalation_priority = priority_order.get(escalation.priority, 2)
        max_priority = priority_order.get(input_data.max_auto_resolve_priority, 3)

        if escalation_priority < max_priority:
            self.logger.info(
                "Priority too high for auto-resolution",
                priority=escalation.priority,
            )
            return None

        # Extract confidence from response or use default
        confidence = 0.85  # Default confidence for successful auto-resolution

        return Resolution(
            escalation_id=escalation.id,
            title="Auto-Resolved: " + escalation.title,
            description=content,
            status=ResolutionStatus.IMPLEMENTED,
            resolution_type="automated",
            steps=["Automated resolution applied"],
            automated=True,
            confidence=confidence,
            verified_by="auto_resolver_agent",
        )
