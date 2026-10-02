"""Skill Extractor Agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from skills_assessor.agents.base import BaseAgent
from skills_assessor.config.settings import get_settings
from skills_assessor.models.schemas import ExtractionRequest, ExtractionResponse, Skill, SkillCategory


class SkillExtractorAgent(BaseAgent[ExtractionRequest, ExtractionResponse]):
    """Agent that extracts skills from unstructured text using LLM analysis.

    Uses LangChain DeepAgents patterns to parse resumes, job descriptions,
    LinkedIn profiles, and other text sources to identify and categorize skills.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Initialize the SkillExtractorAgent.

        Args:
            model: Optional pre-configured chat model.
        """
        super().__init__(model)
        self._settings = get_settings()
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the extraction prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.
        """
        system_message = """You are an expert skill extraction system. Your task is to analyze text and extract all relevant skills.

For each skill found, provide:
- name: The skill name (normalized, lowercase)
- category: One of [technical, soft, leadership, domain, tool, language, framework, methodology]
- description: Brief description of the skill
- keywords: Related keywords and technologies
- confidence: How confident you are this is a real skill (0.0 to 1.0)

Rules:
1. Extract both hard skills (technical) and soft skills
2. Normalize skill names (e.g., "React.js" and "React" are the same)
3. Include related keywords for each skill
4. Be thorough but avoid false positives
5. Return results as a JSON array

Output format:
```json
{
  "skills": [
    {
      "name": "python",
      "category": "technical",
      "description": "Python programming language",
      "keywords": ["python3", "python scripting"],
      "confidence": 0.95
    }
  ]
}
```"""

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="examples"),
                HumanMessage(content="Extract skills from the following text:\n\n{text}"),
            ]
        )

    async def run(self, input_data: ExtractionRequest) -> ExtractionResponse:
        """Extract skills from the provided text.

        Args:
            input_data: The extraction request containing text and options.

        Returns:
            ExtractionResponse: Extracted skills with confidence scores.
        """
        chain = self._prompt | self._model

        response = await chain.ainvoke(
            {
                "text": input_data.text,
                "examples": [],
            }
        )

        raw_content = response.content if hasattr(response, "content") else str(response)
        skills = self._parse_response(raw_content, input_data.max_skills)

        avg_confidence = (
            sum(s.confidence for s in skills) / len(skills) if skills else 0.0
        )

        return ExtractionResponse(
            skills=skills,
            total_found=len(skills),
            confidence=avg_confidence,
            processing_time_ms=0.0,  # Set by caller if needed
        )

    def _parse_response(self, raw_content: str, max_skills: int) -> list[Skill]:
        """Parse the LLM response into Skill objects.

        Args:
            raw_content: Raw text response from the LLM.
            max_skills: Maximum number of skills to return.

        Returns:
            list[Skill]: Parsed and validated skills.
        """
        # Try to extract JSON from the response
        json_str = self._extract_json(raw_content)
        if not json_str:
            return []

        try:
            data = json.loads(json_str)
            raw_skills = data.get("skills", [])
        except (json.JSONDecodeError, AttributeError):
            return []

        skills: list[Skill] = []
        for item in raw_skills[:max_skills]:
            try:
                skill = Skill(
                    name=item.get("name", "").strip().lower(),
                    category=SkillCategory(item.get("category", "technical")),
                    description=item.get("description"),
                    keywords=item.get("keywords", []),
                )
                skills.append(skill)
            except (ValidationError, ValueError):
                continue

        return skills

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON string from text that may contain markdown formatting.

        Args:
            text: Raw text potentially containing JSON.

        Returns:
            str | None: Extracted JSON string or None if not found.
        """
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            return text[start:end].strip()

        # Try to find raw JSON
        text = text.strip()
        if text.startswith("{") or text.startswith("["):
            return text

        # Try to find JSON boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]

        return None
