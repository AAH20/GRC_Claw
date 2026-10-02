"""Infringement detection agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

from rights_management.agents.base import BaseAgent
from rights_management.models import InfringementDetectionRequest, InfringementDetectionResult

_SYSTEM_PROMPT = """You are a content infringement detection specialist.

Analyze the given content and compare it against reference content to
identify potential copyright or license infringements. Look for:
- Substantial similarity in text, images, or structure
- Unauthorized reproduction or distribution
- License violations
- Missing attribution

Return a JSON object with:
- potential_infringements: list of objects with content_id, similarity_score, description
- risk_score: float between 0 and 1
- recommendations: list of strings with suggested actions
"""


class InfringementDetectorAgent(BaseAgent[InfringementDetectionRequest, InfringementDetectionResult]):
    """Agent that detects potential content infringements."""

    def _build_agent(self):
        """Build the LangChain agent for infringement detection.

        Returns:
            Configured agent instance.
        """
        return create_agent(
            model=self._get_llm(),
            tools=[],
            system_prompt=_SYSTEM_PROMPT,
            debug=self._settings.debug,
        )

    async def run(self, payload: InfringementDetectionRequest) -> InfringementDetectionResult:
        """Detect potential infringements for the given content.

        Args:
            payload: The detection request with content and references.

        Returns:
            An InfringementDetectionResult with findings and risk score.
        """
        try:
            result: dict[str, Any] = await self._get_agent().ainvoke(
                {
                    "input": (
                        f"Content ID: {payload.content_id}\n"
                        f"Content text: {payload.content_text or 'N/A'}\n"
                        f"Content URL: {payload.content_url or 'N/A'}\n"
                        f"Reference content IDs: {payload.reference_content_ids}"
                    )
                }
            )
            output = result.get("output", "")
            return InfringementDetectionResult(
                content_id=payload.content_id,
                potential_infringements=[],
                risk_score=0.0,
                recommendations=[output] if output else [],
            )
        except Exception:  # noqa: BLE001
            return InfringementDetectionResult(
                content_id=payload.content_id,
                potential_infringements=[],
                risk_score=0.0,
                recommendations=["Infringement detection failed"],
            )
