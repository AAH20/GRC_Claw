"""External service integrations for skills-assessor."""

from skills_assessor.integrations.llm_client import LLMClient
from skills_assessor.integrations.skill_database import SkillDatabase

__all__ = ["LLMClient", "SkillDatabase"]
