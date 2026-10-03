"""Video moderation agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ugc_marketplace.agents.content_moderation.base import BaseModerationAgent
from ugc_marketplace.models.schemas import ContentType

VIDEO_MODERATION_PROMPT = """You are a content moderation AI specializing in video analysis.
Analyze the provided video for policy violations including:
- Adult/NSFW content
- Violence and dangerous acts
- Hate speech and symbols
- Copyright infringement
- Illegal activities

Respond with a JSON object containing:
- action: one of "allow", "flag", "block", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of detected violation categories
- reasons: list of human-readable reasons
- policy_violations: list of violated policy IDs (if any)

Video to analyze: {video_url}
"""


class VideoModerationAgent(BaseModerationAgent):
    """Agent for moderating video content using LLM analysis."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.VIDEO

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze video content for policy violations.

        Args:
            content: Video URL or path.
            context: Additional context.

        Returns:
            Analysis result with action, confidence, categories, and reasons.
        """
        messages = [
            SystemMessage(content=VIDEO_MODERATION_PROMPT.format(video_url=content)),
            HumanMessage(content=f"Analyze this video: {content}"),
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
