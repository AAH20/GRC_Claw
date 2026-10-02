"""Proficiency Scorer Agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from skills_assessor.agents.base import BaseAgent
from skills_assessor.config.settings import get_settings
from skills_assessor.models.schemas import (
    ProficiencyLevel,
    ScoringRequest,
    ScoringResponse,
    Skill,
    SkillProficiency,
)


class ProficiencyScorerAgent(BaseAgent[ScoringRequest, ScoringResponse]):
    """Agent that scores skill proficiency levels using LLM analysis.

    Evaluates each skill against proficiency criteria and assigns
    a level from novice to expert with confidence scoring.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Initialize the ProficiencyScorerAgent.

        Args:
            model: Optional pre-configured chat model.
        """
        super().__init__(model)
        self._settings = get_settings()
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the scoring prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.
        """
        system_message = """You are an expert skill proficiency assessor. Your task is to evaluate skill proficiency levels.

For each skill, assess:
- level: One of [novice, beginner, intermediate, advanced, expert]
- confidence: How confident you are in this assessment (0.0 to 1.0)
- years_experience: Estimated years of experience (null if unknown)
- evidence: List of evidence supporting the assessment
- notes: Additional notes about the assessment

Proficiency Level Definitions:
- Novice: Basic understanding, limited practical experience
- Beginner: Can perform basic tasks with guidance
- Intermediate: Can work independently on standard tasks
- Advanced: Deep understanding, can handle complex scenarios
- Expert: Mastery level, can teach others and innovate

Output format:
```json
{
  "proficiencies": [
    {
      "skill_name": "python",
      "level": "advanced",
      "confidence": 0.85,
      "years_experience": 5.0,
      "evidence": ["Built production systems", "Led team of 5 developers"],
      "notes": "Strong practical experience"
    }
  ]
}
```"""

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="examples"),
                HumanMessage(
                    content="Score proficiency for these skills:\n\n{skills}\n\nContext: {context}"
                ),
            ]
        )

    async def run(self, input_data: ScoringRequest) -> ScoringResponse:
        """Score proficiency levels for the provided skills.

        Args:
            input_data: The scoring request containing skills and context.

        Returns:
            ScoringResponse: Proficiency scores for each skill.
        """
        chain = self._prompt | self._model

        skills_text = "\n".join(f"- {s.name}" for s in input_data.skills)
        context = input_data.candidate_context or "No additional context provided."

        response = await chain.ainvoke(
            {
                "skills": skills_text,
                "context": context,
                "examples": [],
            }
        )

        raw_content = response.content if hasattr(response, "content") else str(response)
        proficiencies = self._parse_response(raw_content, input_data.skills)

        overall_score = (
            sum(p.confidence for p in proficiencies) / len(proficiencies)
            if proficiencies
            else 0.0
        )

        return ScoringResponse(
            proficiencies=proficiencies,
            overall_score=overall_score,
            processing_time_ms=0.0,
        )

    def _parse_response(
        self, raw_content: str, skills: list[Skill]
    ) -> list[SkillProficiency]:
        """Parse the LLM response into SkillProficiency objects.

        Args:
            raw_content: Raw text response from the LLM.
            skills: Original skills that were scored.

        Returns:
            list[SkillProficiency]: Parsed proficiency assessments.
        """
        json_str = self._extract_json(raw_content)
        if not json_str:
            return []

        try:
            data = json.loads(json_str)
            raw_profs = data.get("proficiencies", [])
        except (json.JSONDecodeError, AttributeError):
            return []

        skill_map = {s.name: s for s in skills}
        proficiencies: list[SkillProficiency] = []

        for item in raw_profs:
            skill_name = item.get("skill_name", "").strip().lower()
            skill = skill_map.get(skill_name)
            if not skill:
                continue

            try:
                proficiency = SkillProficiency(
                    skill=skill,
                    level=ProficiencyLevel(item.get("level", "beginner")),
                    confidence=float(item.get("confidence", 0.5)),
                    years_experience=item.get("years_experience"),
                    evidence=item.get("evidence", []),
                    notes=item.get("notes"),
                )
                proficiencies.append(proficiency)
            except (ValidationError, ValueError, TypeError):
                continue

        return proficiencies

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON string from text that may contain markdown formatting.

        Args:
            text: Raw text potentially containing JSON.

        Returns:
            str | None: Extracted JSON string or None if not found.
        """
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            return text[start:end].strip()

        text = text.strip()
        if text.startswith("{") or text.startswith("["):
            return text

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]

        return None
