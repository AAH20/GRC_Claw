"""Image moderation agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from content_moderation.agents.base import BaseModerationAgent
from content_moderation.models.schemas import ContentType

IMAGE_MODERATION_PROMPT = """You are a content moderation AI specializing in image analysis.
Analyze the provided image for policy violations including:
- Adult/NSFW content
- Violence and gore
- Hate symbols and imagery
- Dangerous activities
- Self-harm content
- Illegal items or activities

Respond with a JSON object containing:
- action: one of "allow", "flag", "block", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of detected violation categories
- reasons: list of human-readable reasons
- policy_violations: list of violated policy IDs (if any)

Image URL to analyze:
{image_url}
"""


class ImageModerationAgent(BaseModerationAgent):
    """Agent for moderating image content using multimodal LLM analysis."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.IMAGE

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze image content for policy violations.

        Args:
            content: Image URL or base64-encoded image data.
            context: Additional context.

        Returns:
            Analysis result with action, confidence, categories, and reasons.
        """
        messages = [
            SystemMessage(content=IMAGE_MODERATION_PROMPT.format(image_url=content)),
            HumanMessage(content=f"Analyze this image: {content}"),
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
