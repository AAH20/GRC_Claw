"""Skill Validator Agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from skills_assessor.agents.base import BaseAgent
from skills_assessor.config.settings import get_settings
from skills_assessor.models.schemas import Skill, SkillValidationResult


class SkillValidatorAgent(BaseAgent[list[Skill], list[SkillValidationResult]]):
    """Agent that validates and verifies claimed skills.

    Cross-references skills against known databases, certifications,
    and industry standards to verify authenticity and currency.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Initialize the SkillValidatorAgent.

        Args:
            model: Optional pre-configured chat model.
        """
        super().__init__(model)
        self._settings = get_settings()
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the validation prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.
        """
        system_message = (
            "You are an expert skill validation system. Your task is to validate "
            "and verify claimed skills.\n"
            "\n"
            "For each skill, assess:\n"
            "- is_valid: Whether the skill is recognized and verifiable\n"
            "- confidence: How confident you are in this validation (0.0 to 1.0)\n"
            "- validation_method: The method used to validate "
            '(e.g., "industry_standard", "certification_body", "market_presence")\n'
            "- evidence: List of evidence supporting the validation\n"
            "- warnings: Any warnings about the skill (e.g., outdated, deprecated, niche)\n"
            "\n"
            "Validation Criteria:\n"
            "1. Is the skill recognized in the industry?\n"
            "2. Are there certifications or formal training available?\n"
            "3. Is there market demand for this skill?\n"
            "4. Is the skill current and not deprecated?\n"
            "5. Are there standard proficiency frameworks for this skill?\n"
            "\n"
            "Output format:\n"
            "```json\n"
            "{\n"
            '  "validations": [\n'
            "    {\n"
            '      "skill_name": "python",\n'
            '      "is_valid": true,\n'
            '      "confidence": 0.98,\n'
            '      "validation_method": "industry_standard",\n'
            '      "evidence": ["TIOBE top 3 language", "PSF certifications available", '
            '"Widely used in industry"],\n'
            '      "warnings": []\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "```"
        )

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="examples"),
                HumanMessage(content="Validate these skills:\n\n{skills}"),
            ]
        )

    async def run(self, input_data: list[Skill]) -> list[SkillValidationResult]:
        """Validate the provided skills.

        Args:
            input_data: List of skills to validate.

        Returns:
            list[SkillValidationResult]: Validation results for each skill.
        """
        chain = self._prompt | self._model

        skills_text = "\n".join(f"- {s.name}" for s in input_data)

        response = await chain.ainvoke(
            {
                "skills": skills_text,
                "examples": [],
            }
        )

        raw_content = response.content if hasattr(response, "content") else str(response)
        return self._parse_response(raw_content, input_data)

    def _parse_response(
        self, raw_content: str, skills: list[Skill]
    ) -> list[SkillValidationResult]:
        """Parse the LLM response into SkillValidationResult objects.

        Args:
            raw_content: Raw text response from the LLM.
            skills: Original skills that were validated.

        Returns:
            list[SkillValidationResult]: Parsed validation results.
        """
        json_str = self._extract_json(raw_content)
        if not json_str:
            return []

        try:
            data = json.loads(json_str)
            raw_validations = data.get("validations", [])
        except (json.JSONDecodeError, AttributeError):
            return []

        skill_map = {s.name: s for s in skills}
        results: list[SkillValidationResult] = []

        for item in raw_validations:
            skill_name = item.get("skill_name", "").strip().lower()
            skill = skill_map.get(skill_name)
            if not skill:
                continue

            try:
                result = SkillValidationResult(
                    skill=skill,
                    is_valid=bool(item.get("is_valid", True)),
                    confidence=float(item.get("confidence", 0.5)),
                    validation_method=item.get("validation_method", "unknown"),
                    evidence=item.get("evidence", []),
                    warnings=item.get("warnings", []),
                )
                results.append(result)
            except (ValidationError, ValueError, TypeError):
                continue

        return results

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
