"""License detection agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from rights_management.agents.base import BaseAgent
from rights_management.models import (
    LicenseDetectionRequest,
    LicenseDetectionResult,
    LicenseType,
)

_SYSTEM_PROMPT = """You are a content license detection specialist.

Given content metadata and optionally its text or URL, determine the most
likely license that applies to the content. Consider embedded metadata,
watermarks, copyright notices, and textual clues.

Return a JSON object with:
- detected_license: one of {license_types} or null
- confidence: float between 0 and 1
- evidence: list of strings explaining the reasoning
- matched_license_id: string or null
"""


class LicenseDetectorAgent(BaseAgent[LicenseDetectionRequest, LicenseDetectionResult]):
    """Agent that detects the license associated with a piece of content."""

    def _build_agent(self) -> AgentExecutor:
        """Build the LangChain ReAct agent for license detection.

        Returns:
            Configured AgentExecutor instance.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _SYSTEM_PROMPT.format(license_types=", ".join(lt.value for lt in LicenseType))),
                ("human", "{input}"),
            ]
        )
        agent = create_react_agent(self._llm, tools=[], prompt=prompt)
        return AgentExecutor(agent=agent, tools=[], verbose=self._settings.debug)

    async def run(self, payload: LicenseDetectionRequest) -> LicenseDetectionResult:
        """Detect the license for the given content.

        Args:
            payload: The detection request containing content information.

        Returns:
            A LicenseDetectionResult with the detected license and confidence.
        """
        try:
            result: dict[str, Any] = await self._agent.ainvoke(
                {
                    "input": (
                        f"Content ID: {payload.content_id}\n"
                        f"Content text: {payload.content_text or 'N/A'}\n"
                        f"Content URL: {payload.content_url or 'N/A'}\n"
                        f"Metadata: {payload.metadata}"
                    )
                }
            )
            output = result.get("output", "")
            return LicenseDetectionResult(
                content_id=payload.content_id,
                detected_license=None,
                confidence=0.0,
                evidence=[output] if output else [],
            )
        except Exception:
            return LicenseDetectionResult(
                content_id=payload.content_id,
                detected_license=None,
                confidence=0.0,
                evidence=["License detection failed"],
            )
