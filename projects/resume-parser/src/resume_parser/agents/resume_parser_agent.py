"""ResumeParserAgent - Orchestrates the full resume parsing pipeline."""

from __future__ import annotations

import json
import time
import uuid
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from resume_parser.agents.base import BaseAgent
from resume_parser.models import AgentResult, ParsedResume, ParsingStatus

if TYPE_CHECKING:
    from resume_parser.config import Settings
    from resume_parser.integrations import BaseLLMClient

logger = structlog.get_logger(__name__)


class ResumeParserAgent(BaseAgent):
    """Agent that orchestrates the full resume parsing pipeline.

    This agent coordinates the extraction of all resume sections and
    assembles the final ParsedResume object.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        settings: Settings,
        sub_agents: list[BaseAgent] | None = None,
    ) -> None:
        """Initialize the resume parser agent.

        Args:
            llm_client: LLM client for generating responses.
            settings: Application settings.
            sub_agents: Optional list of sub-agents for specialized extraction.
        """
        super().__init__(llm_client, settings)
        self._sub_agents = sub_agents or []

    @property
    def name(self) -> str:
        """Get the agent name.

        Returns:
            str: Agent name.
        """
        return "ResumeParserAgent"

    @property
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        return "Orchestrates full resume parsing by coordinating specialized extraction agents"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        return (
            "You are a resume parsing orchestrator. Your job is to coordinate "
            "the extraction of structured information from resume text. "
            "You will receive resume text and must produce a comprehensive "
            "JSON representation of the candidate's profile."
        )

    def _build_user_prompt(self, text: str, **kwargs: Any) -> str:
        """Build the user prompt for this agent.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            str: User prompt.
        """
        return f"""Parse the following resume and extract all relevant information.

Resume Text:
---
{text}
---

Provide a comprehensive analysis including:
1. Contact information (name, email, phone, links)
2. Professional summary
3. All skills mentioned
4. Work experience history
5. Education history
6. Languages and certifications

Format your response as structured JSON."""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed structured data.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            import re

            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"raw_response": response}

    async def run(self, text: str, **kwargs: Any) -> AgentResult:
        """Execute the full parsing pipeline.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            AgentResult: Result of the parsing pipeline.
        """
        start_time = time.monotonic()
        self._logger.info("pipeline_started", text_length=len(text))

        try:
            # Run sub-agents if available
            agent_results: list[AgentResult] = []
            combined_data: dict[str, Any] = {}

            for agent in self._sub_agents:
                result = await agent.run(text, **kwargs)
                agent_results.append(result)
                if result.success:
                    combined_data.update(result.data)

            # If no sub-agents, do direct parsing
            if not self._sub_agents:
                system_prompt = self._build_system_prompt()
                user_prompt = self._build_user_prompt(text, **kwargs)

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]

                response = await self._llm.agenerate(
                    messages,
                    max_tokens=self._settings.llm_max_tokens,
                    temperature=self._settings.llm_temperature,
                )
                combined_data = self._parse_response(response)

            # Build ParsedResume
            parsed = ParsedResume(
                id=str(uuid.uuid4()),
                resume_id=kwargs.get("resume_id", str(uuid.uuid4())),
                contact=combined_data.get("contact", {}),
                skills=combined_data.get("skills", []),
                experience=combined_data.get("experience", []),
                education=combined_data.get("education", []),
                languages=combined_data.get("languages", []),
                certifications=combined_data.get("certifications", []),
                raw_text=text,
                parsing_metadata={
                    "agent_results": [r.model_dump() for r in agent_results],
                },
                status=ParsingStatus.COMPLETED,
            )

            execution_time = time.monotonic() - start_time
            self._logger.info("pipeline_completed", execution_time=execution_time)

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=parsed.model_dump(),
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            execution_time = time.monotonic() - start_time
            self._logger.error("pipeline_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e),
                execution_time_seconds=execution_time,
            )
