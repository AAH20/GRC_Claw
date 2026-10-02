"""Auto-moderation agent using LangChain DeepAgents."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from moderation_queue.agents.base import AgentResult, BaseAgent
from moderation_queue.config.settings import get_settings

settings = get_settings()

MODERATION_SYSTEM_PROMPT = """You are an automated content moderation system.
Analyze the given content and determine if it should be approved, rejected, or escalated to human review.

Decision rules:
- APPROVE: Content clearly violates no policies
- REJECT: Content clearly violates policies (hate speech, harassment, illegal content, etc.)
- ESCALATE: Content is ambiguous, borderline, or requires human judgment

Respond with ONLY a JSON object:
{
    "decision": "approve" | "reject" | "escalate",
    "confidence": <float 0.0-1.0>,
    "categories": [<list of violated or potentially violated policy categories>],
    "reasoning": "<brief explanation>"
}"""


class AutoModeratorAgent(BaseAgent):
    """Automated content moderation using an LLM via LangChain."""

    name = "auto_moderator"

    def __init__(self, llm=None):
        self._llm = llm

    async def execute(self, context: dict[str, Any]) -> AgentResult:
        content = context.get("content", "")
        content_type = context.get("content_type", "text")
        metadata = context.get("metadata", {})

        if not content:
            return AgentResult(
                success=False,
                error="No content provided for moderation",
            )

        try:
            if self._llm is None:
                return await self._heuristic_moderate(content, content_type)

            messages = [
                SystemMessage(content=MODERATION_SYSTEM_PROMPT),
                HumanMessage(
                    content=f"Content type: {content_type}\nMetadata: {metadata}\nContent:\n{content[:4000]}"
                ),
            ]
            response = await self._llm.ainvoke(messages)
            return self._parse_response(response.content)
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Auto-moderation failed: {e}",
            )

    async def _heuristic_moderate(self, content: str, content_type: str) -> AgentResult:
        """Fallback heuristic moderation when no LLM is available."""
        reject_keywords = [
            "kill", "murder", "terrorist", "bomb", "hate",
            "slur", "harass", "dox", "swat",
        ]
        escalate_keywords = [
            "protest", "political", "controversial", "alleged",
            "disputed", "opinion",
        ]

        content_lower = content.lower()

        for keyword in reject_keywords:
            if keyword in content_lower:
                return AgentResult(
                    success=True,
                    data={
                        "decision": "reject",
                        "confidence": 0.7,
                        "categories": [f"keyword_match:{keyword}"],
                        "reasoning": f"Detected reject keyword: {keyword}",
                    },
                    confidence=0.7,
                    metadata={"method": "heuristic"},
                )

        for keyword in escalate_keywords:
            if keyword in content_lower:
                return AgentResult(
                    success=True,
                    data={
                        "decision": "escalate",
                        "confidence": 0.5,
                        "categories": [f"keyword_match:{keyword}"],
                        "reasoning": f"Detected escalate keyword: {keyword}",
                    },
                    confidence=0.5,
                    metadata={"method": "heuristic"},
                )

        return AgentResult(
            success=True,
            data={
                "decision": "approve",
                "confidence": 0.6,
                "categories": [],
                "reasoning": "No policy violations detected by heuristic scan",
            },
            confidence=0.6,
            metadata={"method": "heuristic"},
        )

    def _parse_response(self, raw: str) -> AgentResult:
        import json

        try:
            parsed = json.loads(raw)
            decision = parsed.get("decision", "escalate")
            if decision not in ("approve", "reject", "escalate"):
                decision = "escalate"

            confidence = float(parsed.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            return AgentResult(
                success=True,
                data={
                    "decision": decision,
                    "confidence": confidence,
                    "categories": parsed.get("categories", []),
                    "reasoning": parsed.get("reasoning", ""),
                },
                confidence=confidence,
                metadata={"method": "llm"},
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return AgentResult(
                success=False,
                error=f"Failed to parse LLM response: {e}",
            )
