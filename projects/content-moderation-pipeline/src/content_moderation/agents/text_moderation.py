"""Text moderation agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from content_moderation.agents.base import BaseModerationAgent
from content_moderation.models.schemas import ContentType

TEXT_MODERATION_PROMPT = """You are a content moderation AI specializing in text analysis.
Analyze the provided text for policy violations including:
- Hate speech and harassment
- Violence and dangerous content
- Adult/NSFW content
- Spam and misinformation
- Self-harm content
- Illegal activities

Respond with a JSON object containing:
- action: one of "allow", "flag", "block", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of detected violation categories
- reasons: list of human-readable reasons
- policy_violations: list of violated policy IDs (if any)

Text to analyze:
{text}
"""


class TextModerationAgent(BaseModerationAgent):
    """Agent for moderating text content using LLM analysis."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.TEXT

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze text content for policy violations.

        Args:
            content: Text content to analyze.
            context: Additional context including user history, etc.

        Returns:
            Analysis result with action, confidence, categories, and reasons.
        """
        messages = [
            SystemMessage(content=TEXT_MODERATION_PROMPT.format(text=content)),
            HumanMessage(content=f"Analyze this text:\n\n{content}"),
        ]

        response = await self.model.ainvoke(messages)
        self._trace["llm_response"] = response.content

        try:
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            return {
                "action": "flag",
                "confidence": 0.5,
                "categories": ["parse_error"],
                "reasons": ["Could not parse LLM response"],
            }
