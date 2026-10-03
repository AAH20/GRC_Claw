"""Appeal handler agent for content moderation."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ugc_marketplace.agents.content_moderation.base import BaseModerationAgent
from ugc_marketplace.models.schemas import ContentType

APPEAL_HANDLER_PROMPT = """You are a content moderation appeal review specialist.
Review the appeal against the original moderation decision and determine if the
decision should be upheld or overturned.

Original decision: {original_action}
Appeal reason: {appeal_reason}
Content: {content}

Respond with a JSON object containing:
- action: one of "allow", "flag", "block", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of categories
- reasons: list of reasons for the decision
"""


class AppealHandlerAgent(BaseModerationAgent):
    """Agent for handling moderation appeals."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.TEXT

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze appeal and make a decision.

        Args:
            content: Original content that was moderated.
            context: Must contain 'original_action' and 'appeal_reason'.

        Returns:
            Analysis result with action, confidence, categories, and reasons.
        """
        original_action = context.get("original_action", "flag")
        appeal_reason = context.get("appeal_reason", "")

        messages = [
            SystemMessage(
                content=APPEAL_HANDLER_PROMPT.format(
                    original_action=original_action,
                    appeal_reason=appeal_reason,
                    content=content,
                )
            ),
            HumanMessage(content=f"Review this appeal:\n\nContent: {content}\nReason: {appeal_reason}"),
        ]

        response = await self.model.ainvoke(messages)
        self._trace["llm_response"] = response.content

        try:
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            return {
                "action": "escalate",
                "confidence": 0.5,
                "categories": ["parse_error"],
                "reasons": ["Could not parse LLM response, escalating for human review"],
            }
