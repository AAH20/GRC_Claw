"""Parsing service for orchestrating resume parsing operations."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog

from resume_parser.agents import (
    BaseAgent,
    ContactExtractorAgent,
    EducationExtractorAgent,
    ExperienceExtractorAgent,
    ResumeParserAgent,
    SkillsExtractorAgent,
)
from resume_parser.models import (
    AgentResult,
    ParsedResume,
    ParseResponse,
    ParsingStatus,
)
from resume_parser.utils import clean_text, generate_id

if TYPE_CHECKING:
    from resume_parser.config import Settings
    from resume_parser.integrations import BaseLLMClient
    from resume_parser.integrations.storage import BaseStorage

logger = structlog.get_logger(__name__)


class ParsingService:
    """Service for orchestrating resume parsing operations.

    Coordinates agents, storage, and result assembly.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        storage: BaseStorage,
        settings: Settings,
    ) -> None:
        """Initialize the parsing service.

        Args:
            llm_client: LLM client for agent execution.
            storage: Storage backend for persisting results.
            settings: Application settings.
        """
        self._llm = llm_client
        self._storage = storage
        self._settings = settings
        self._logger = logger.bind(service="ParsingService")

    def _create_agents(self) -> dict[str, BaseAgent]:
        """Create all agent instances.

        Returns:
            dict[str, BaseAgent]: Dictionary of agent instances.
        """
        return {
            "resume_parser": ResumeParserAgent(self._llm, self._settings),
            "contact_extractor": ContactExtractorAgent(self._llm, self._settings),
            "skills_extractor": SkillsExtractorAgent(self._llm, self._settings),
            "experience_extractor": ExperienceExtractorAgent(self._llm, self._settings),
            "education_extractor": EducationExtractorAgent(self._llm, self._settings),
        }

    async def parse_text(
        self,
        text: str,
        use_agents: list[str] | None = None,
    ) -> ParseResponse:
        """Parse resume text and return structured data.

        Args:
            text: Resume text to parse.
            use_agents: Optional list of specific agents to use.

        Returns:
            ParseResponse: Parsing result with structured data.
        """
        start_time = time.monotonic()
        text = clean_text(text)

        agents = self._create_agents()

        # Determine which agents to run
        if use_agents:
            selected = [agents[name] for name in use_agents if name in agents]
        else:
            selected = [agents["resume_parser"]]

        # Run agents
        agent_results: list[AgentResult] = []
        combined_data: dict[str, Any] = {}

        for agent in selected:
            result = await agent.run(text)
            agent_results.append(result)
            if result.success:
                combined_data.update(result.data)

        # Build ParsedResume
        resume_id = generate_id()
        parsed_resume = ParsedResume(
            id=resume_id,
            resume_id=resume_id,
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

        # Save to storage
        await self._storage.save(parsed_resume)

        total_time = time.monotonic() - start_time

        return ParseResponse(
            success=True,
            resume_id=resume_id,
            parsed_resume=parsed_resume,
            agent_results=agent_results,
            total_execution_time_seconds=total_time,
        )

    async def get_resume(self, resume_id: str) -> ParsedResume | None:
        """Retrieve a parsed resume by ID.

        Args:
            resume_id: Resume identifier.

        Returns:
            ParsedResume | None: Parsed resume or None if not found.
        """
        return await self._storage.get(resume_id)

    async def list_resumes(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ParsedResume]:
        """List parsed resumes.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            list[ParsedResume]: List of parsed resumes.
        """
        return await self._storage.list_all(limit=limit, offset=offset)

    async def delete_resume(self, resume_id: str) -> bool:
        """Delete a parsed resume.

        Args:
            resume_id: Resume identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        return await self._storage.delete(resume_id)
