"""Main resume parsing orchestrator agent."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent
from recruitment_platform.agents.resume_parser.contact_extractor_agent import \
    ContactExtractorAgent
from recruitment_platform.agents.resume_parser.education_extractor_agent import \
    EducationExtractorAgent
from recruitment_platform.agents.resume_parser.experience_extractor_agent import \
    ExperienceExtractorAgent
from recruitment_platform.agents.resume_parser.skills_extractor_agent import \
    SkillsExtractorAgent


class ResumeParserAgent(BaseAgent[dict[str, Any], dict[str, Any]]):
    """Orchestrates the full resume parsing pipeline.

    Coordinates contact, education, experience, and skills extraction
    to produce a structured representation of a resume.
    """

    def __init__(self) -> None:
        """Initialize the resume parser orchestrator."""
        super().__init__(name="resume_parser")
        self._contact_agent = ContactExtractorAgent()
        self._education_agent = EducationExtractorAgent()
        self._experience_agent = ExperienceExtractorAgent()
        self._skills_agent = SkillsExtractorAgent()

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Parse a complete resume into structured data.

        Args:
            input_data: Dictionary containing 'text' key with resume content.

        Returns:
            Structured resume data with all extracted sections.
        """
        contact = await self._contact_agent.process(input_data)
        education = await self._education_agent.process(input_data)
        experience = await self._experience_agent.process(input_data)
        skills = await self._skills_agent.process(input_data)

        return {
            "contact": contact,
            "education": education,
            "experience": experience,
            "skills": skills,
        }
