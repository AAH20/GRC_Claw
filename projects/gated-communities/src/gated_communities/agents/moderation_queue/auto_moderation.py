"""Auto-Moderation Agent for automated content moderation."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from moderation_queue.agents.base import AgentConfig, BaseAgent
from moderation_queue.models import ModerationItem, ModerationStatus


class AutoModerationInput(BaseModel):
    """Input for the Auto-Moderation Agent."""

    item: ModerationItem = Field(..., description="Moderation item to process")
    rules: dict[str, Any] = Field(
        default_factory=dict, description="Moderation rules configuration"
    )
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")


class AutoModerationOutput(BaseModel):
    """Output from the Auto-Moderation Agent."""

    action: str = Field(..., description="Moderation action: approve, reject, or escalate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    categories: list[str] = Field(
        default_factory=list, description="Violation categories detected"
    )
    reasoning: str = Field(default="", description="Decision reasoning")
    suggested_status: ModerationStatus = Field(
        ..., description="Suggested moderation status"
    )


SYSTEM_PROMPT = """You are an AI content moderator.
Your task is to analyze content and determine if it violates community guidelines.

Check for:
- Hate speech and harassment
- Spam and scams
- Adult content
- Violence and dangerous content
- Misinformation
- Intellectual property violations

Provide a decision with confidence level.
If confidence is below threshold, escalate to human review.
Always respond with valid JSON matching the expected schema."""


class AutoModerationAgent(BaseAgent[AutoModerationInput, AutoModerationOutput]):
    """Agent that automatically moderates content using AI.

    This agent analyzes content against community guidelines and makes
    moderation decisions. Low-confidence decisions are escalated to humans.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the Auto-Moderation Agent.

        Args:
            settings: Application settings.
        """
        config = AgentConfig(
            name="AutoModerationAgent",
            description="AI agent for automated content moderation",
            temperature=0.0,
            max_tokens=500,
        )
        super().__init__(config, settings)

    async def process(self, input_data: AutoModerationInput) -> AutoModerationOutput:
        """Process a moderation item for automated decision.

        Args:
            input_data: Input containing the item and rules.

        Returns:
            AutoModerationOutput: Moderation decision.
        """
        item = input_data.item
        threshold = input_data.threshold

        user_content = f"""Analyze this content for moderation:

Content Type: {item.content_type.value}
Content: {item.content[:1000]}
Author ID: {item.author_id}
Tags: {item.tags}
Rules: {json.dumps(input_data.rules)}

Provide:
1. action: "approve", "reject", or "escalate"
2. confidence: float (0.0-1.0)
3. categories: list of violation categories (empty if approved)
4. reasoning: brief explanation
5. suggested_status: one of "approved", "rejected", "auto_moderated", "escalated"

Respond with JSON only."""

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self._model.ainvoke(messages)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            try:
                data = json.loads(response.content)
                output = AutoModerationOutput.model_validate(data)
                # Apply threshold logic
                if output.confidence < threshold:
                    output.action = "escalate"
                    output.suggested_status = ModerationStatus.ESCALATED
                    output.reasoning += " (Escalated due to low confidence)"
                return output
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: escalate if AI is unavailable
        return AutoModerationOutput(
            action="escalate",
            confidence=0.0,
            categories=[],
            reasoning="AI model unavailable, escalating to human review",
            suggested_status=ModerationStatus.ESCALATED,
        )

    def should_auto_moderate(self, confidence: float, threshold: float) -> bool:
        """Check if item should be auto-moderated based on confidence.

        Args:
            confidence: AI confidence score.
            threshold: Minimum confidence threshold.

        Returns:
            bool: True if item can be auto-moderated.
        """
        return confidence >= threshold
