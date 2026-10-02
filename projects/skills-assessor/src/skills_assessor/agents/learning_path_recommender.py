"""Learning Path Recommender Agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from skills_assessor.agents.base import BaseAgent
from skills_assessor.config.settings import get_settings
from skills_assessor.models.schemas import (
    LearningPath,
    LearningPathRequest,
    LearningPathResponse,
    LearningResource,
    LearningStep,
    ProficiencyLevel,
    Skill,
)


class LearningPathRecommenderAgent(BaseAgent[LearningPathRequest, LearningPathResponse]):
    """Agent that generates personalized learning paths based on skill gaps.

    Creates structured learning plans with steps, resources, and milestones
    to help candidates close skill gaps and reach target proficiency levels.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Initialize the LearningPathRecommenderAgent.

        Args:
            model: Optional pre-configured chat model.
        """
        super().__init__(model)
        self._settings = get_settings()
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the learning path prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.
        """
        system_message = (
            "You are an expert learning path designer. Your task is to create "
            "personalized learning paths to help candidates close skill gaps.\n"

For the learning path, provide:
- title: A descriptive title for the learning path
- description: Overview of what the path covers
- difficulty: One of [beginner, intermediate, advanced]
- steps: Ordered list of learning steps

Each step should include:
- order: Step number (1-indexed)
- title: Step title
- description: What this step covers
- skill_target: The skill being developed
- proficiency_goal: Target proficiency level [novice, beginner, intermediate, advanced, expert]
- estimated_hours: Time to complete this step
- resources: List of learning resources
- milestones: Achievable milestones for this step

Each resource should include:
- title: Resource title
- type: One of [course, article, video, book, tutorial, documentation, project, other]
- url: Resource URL (null if unknown)
- provider: Provider name (null if unknown)
- is_free: Whether the resource is free
- estimated_hours: Time to complete (null if unknown)

Output format:
```json
{
  "title": "Full Stack Developer Learning Path",
  "description": "A comprehensive path to become a full stack developer",
  "difficulty": "intermediate",
  "steps": [
    {
      "order": 1,
      "title": "Master Python Fundamentals",
      "description": "Learn Python programming from scratch",
      "skill_target": "python",
      "proficiency_goal": "intermediate",
      "estimated_hours": 40,
      "resources": [
        {
          "title": "Python for Everybody",
          "type": "course",
          "url": "https://example.com/python-course",
          "provider": "Coursera",
          "is_free": true,
          "estimated_hours": 30
        }
      ],
      "milestones": ["Complete 10 Python projects", "Pass Python assessment"]
    }
  ]
}
```"""

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="examples"),
                HumanMessage(
                    content=(
                        "Create a learning path for target role: {target_role}\n\n"
                        "Skill gaps to address:\n{skill_gaps}\n\n"
                        "Maximum steps: {max_steps}"
                    )
                ),
            ]
        )

    async def run(self, input_data: LearningPathRequest) -> LearningPathResponse:
        """Generate a learning path for the given assessment.

        Args:
            input_data: The learning path request.

        Returns:
            LearningPathResponse: Generated learning path.
        """
        chain = self._prompt | self._model

        skill_gaps_text = self._format_skill_gaps(input_data)

        response = await chain.ainvoke(
            {
                "target_role": input_data.target_role,
                "skill_gaps": skill_gaps_text,
                "max_steps": input_data.max_steps,
                "examples": [],
            }
        )

        raw_content = response.content if hasattr(response, "content") else str(response)
        learning_path = self._parse_response(raw_content, input_data)

        return LearningPathResponse(
            learning_path=learning_path,
            processing_time_ms=0.0,
        )

    def _format_skill_gaps(self, input_data: LearningPathRequest) -> str:
        """Format skill gaps for the prompt.

        Args:
            input_data: The learning path request.

        Returns:
            str: Formatted skill gaps text.
        """
        return f"Target role: {input_data.target_role}"

    def _parse_response(
        self, raw_content: str, input_data: LearningPathRequest
    ) -> LearningPath:
        """Parse the LLM response into a LearningPath.

        Args:
            raw_content: Raw text response from the LLM.
            input_data: Original learning path request.

        Returns:
            LearningPath: Parsed learning path.
        """
        json_str = self._extract_json(raw_content)
        if not json_str:
            return self._empty_learning_path(input_data)

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            return self._empty_learning_path(input_data)

        steps: list[LearningStep] = []
        for item in data.get("steps", []):
            try:
                resources = [
                    LearningResource(
                        title=r.get("title", "Unknown"),
                        type=r.get("type", "other"),
                        url=r.get("url"),
                        provider=r.get("provider"),
                        is_free=bool(r.get("is_free", True)),
                        estimated_hours=r.get("estimated_hours"),
                    )
                    for r in item.get("resources", [])
                ]

                step = LearningStep(
                    order=int(item.get("order", len(steps) + 1)),
                    title=item.get("title", "Unknown"),
                    description=item.get("description"),
                    skill_target=Skill(name=item.get("skill_target", "unknown")),
                    proficiency_goal=ProficiencyLevel(
                        item.get("proficiency_goal", "intermediate")
                    ),
                    estimated_hours=float(item.get("estimated_hours", 0)),
                    resources=resources,
                    milestones=item.get("milestones", []),
                )
                steps.append(step)
            except (ValidationError, ValueError, TypeError):
                continue

        total_hours = sum(s.estimated_hours for s in steps)

        return LearningPath(
            assessment_id=input_data.assessment_id,
            candidate_id="",
            target_role=input_data.target_role,
            title=data.get("title", "Learning Path"),
            description=data.get("description"),
            steps=steps,
            total_estimated_hours=total_hours,
            difficulty=data.get("difficulty", "intermediate"),
        )

    def _empty_learning_path(self, input_data: LearningPathRequest) -> LearningPath:
        """Create an empty learning path.

        Args:
            input_data: The learning path request.

        Returns:
            LearningPath: Empty learning path.
        """
        return LearningPath(
            assessment_id=input_data.assessment_id,
            candidate_id="",
            target_role=input_data.target_role,
            title="Learning Path",
        )

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
