"""Appeal handler agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from content_moderation.agents.base import BaseModerationAgent
from content_moderation.models.schemas import ContentType

APPEAL_REVIEW_PROMPT = """You are an appeal review AI for content moderation decisions.
Review the appeal and determine if the original moderation decision should be upheld or overturned.

Original moderation result:
{original_result}

Appeal details:
- User ID: {user_id}
- Reason: {reason}
- Evidence: {evidence}

Consider:
1. Was the original decision correct based on the content?
2. Does the appeal provide valid reasoning or evidence?
3. Are there mitigating circumstances?
4. Should the decision be escalated to a human reviewer?

Respond with a JSON object containing:
- action: one of "approve", "reject", "escalate"
- confidence: float between 0.0 and 1.0
- categories: list of relevant categories
- reasons: list of human-readable reasons for the decision
- reviewer_notes: notes for the moderation team
"""


class AppealHandlerAgent(BaseModerationAgent):
    """Agent for handling and reviewing moderation appeals."""

    @property
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        return ContentType.TEXT

    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Review an appeal against a moderation decision.

        Args:
            content: The original content that was moderated.
            context: Must contain 'original_result', 'user_id', 'reason', 'evidence'.

        Returns:
            Appeal review result with decision and reasoning.
        """
        original_result = context.get("original_result", {})
        user_id = context.get("user_id", "unknown")
        reason = context.get("reason", "")
        evidence = context.get("evidence", {})

        messages = [
            SystemMessage(
                content=APPEAL_REVIEW_PROMPT.format(
                    original_result=json.dumps(original_result, default=str),
                    user_id=user_id,
                    reason=reason,
                    evidence=json.dumps(evidence),
                )
            ),
            HumanMessage(content=f"Review this appeal for content: {content}"),
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
                "reasons": ["Could not parse LLM response, escalating to human"],
                "reviewer_notes": "Automated review failed, manual review required",
            }
