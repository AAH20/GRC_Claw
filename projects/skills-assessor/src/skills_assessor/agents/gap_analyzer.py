"""Gap Analyzer Agent using LangChain DeepAgents."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from skills_assessor.agents.base import BaseAgent
from skills_assessor.config.settings import get_settings
from skills_assessor.models.schemas import (
    GapAnalysisRequest,
    GapAnalysisResponse,
    GapReport,
    ProficiencyLevel,
    Skill,
    SkillGap,
)


class GapAnalyzerAgent(BaseAgent[GapAnalysisRequest, GapAnalysisResponse]):
    """Agent that analyzes skill gaps between current and target profiles.

    Compares a candidate's current skills against role requirements
    and identifies gaps with severity and priority ratings.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Initialize the GapAnalyzerAgent.

        Args:
            model: Optional pre-configured chat model.
        """
        super().__init__(model)
        self._settings = get_settings()
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the gap analysis prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.
        """
        system_message = (
            "You are an expert skill gap analyst. Your task is to analyze the gap "
            "between a candidate's current skills and the requirements for a target role.\n"
            "\n"
            "For each skill gap, provide:\n"
            "- skill_name: The name of the skill\n"
            "- current_level: One of [novice, beginner, intermediate, advanced, expert] "
            '(or "none" if missing)\n'
            "- required_level: One of [novice, beginner, intermediate, advanced, expert]\n"
            "- gap_severity: One of [none, minor, moderate, major, critical]\n"
            "- priority: 1 (lowest) to 5 (highest)\n"
            "- estimated_hours_to_close: Estimated hours needed to reach required level\n"
            "\n"
            "Also provide:\n"
            "- overall_readiness: 0.0 to 1.0 score of candidate readiness for the role\n"
            "- recommendations: List of actionable recommendations\n"
            "\n"
            "Gap Severity Definitions:\n"
            "- none: No gap, meets or exceeds requirement\n"
            "- minor: Slight gap, minimal effort needed\n"
            "- moderate: Noticeable gap, moderate effort needed\n"
            "- major: Significant gap, substantial effort needed\n"
            "- critical: Critical gap, role cannot be performed effectively\n"
            "\n"
            "Output format:\n"
            "```json\n"
            "{\n"
            '  "gaps": [\n'
            "    {\n"
            '      "skill_name": "kubernetes",\n'
            '      "current_level": "beginner",\n'
            '      "required_level": "advanced",\n'
            '      "gap_severity": "major",\n'
            '      "priority": 4,\n'
            '      "estimated_hours_to_close": 120\n'
            "    }\n"
            "  ],\n"
            '  "overall_readiness": 0.65,\n'
            '  "recommendations": ["Complete CKA certification", "Practice with production clusters"]\n'
            "}\n"
            "```"
        )

        return ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name="examples"),
                HumanMessage(
                    content=(
                        "Analyze skill gaps for target role: {target_role}\n\n"
                        "Current skills:\n{current_skills}\n\n"
                        "Required skills:\n{required_skills}"
                    )
                ),
            ]
        )

    async def run(self, input_data: GapAnalysisRequest) -> GapAnalysisResponse:
        """Analyze skill gaps for the given assessment.

        Args:
            input_data: The gap analysis request.

        Returns:
            GapAnalysisResponse: Gap analysis report.
        """
        chain = self._prompt | self._model

        # Build current skills text from assessment
        current_skills_text = self._format_current_skills(input_data)
        required_skills_text = self._format_required_skills(input_data)

        response = await chain.ainvoke(
            {
                "target_role": input_data.target_role,
                "current_skills": current_skills_text,
                "required_skills": required_skills_text,
                "examples": [],
            }
        )

        raw_content = response.content if hasattr(response, "content") else str(response)
        report = self._parse_response(raw_content, input_data)

        return GapAnalysisResponse(
            report=report,
            processing_time_ms=0.0,
        )

    def _format_current_skills(self, input_data: GapAnalysisRequest) -> str:
        """Format current skills for the prompt.

        Args:
            input_data: The gap analysis request.

        Returns:
            str: Formatted current skills text.
        """
        # This would normally come from the assessment; simplified here
        return "Current skills from assessment"

    def _format_required_skills(self, input_data: GapAnalysisRequest) -> str:
        """Format required skills for the prompt.

        Args:
            input_data: The gap analysis request.

        Returns:
            str: Formatted required skills text.
        """
        if input_data.required_skills:
            return "\n".join(f"- {s.name}" for s in input_data.required_skills)
        return "To be determined by LLM based on target role"

    def _parse_response(
        self, raw_content: str, input_data: GapAnalysisRequest
    ) -> GapReport:
        """Parse the LLM response into a GapReport.

        Args:
            raw_content: Raw text response from the LLM.
            input_data: Original gap analysis request.

        Returns:
            GapReport: Parsed gap report.
        """
        json_str = self._extract_json(raw_content)
        if not json_str:
            return self._empty_report(input_data)

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            return self._empty_report(input_data)

        gaps: list[SkillGap] = []
        for item in data.get("gaps", []):
            try:
                skill = Skill(name=item.get("skill_name", "unknown"))
                gap = SkillGap(
                    skill=skill,
                    current_level=ProficiencyLevel(item.get("current_level", "none")),
                    required_level=ProficiencyLevel(item.get("required_level", "intermediate")),
                    gap_severity=item.get("gap_severity", "moderate"),
                    priority=int(item.get("priority", 3)),
                    estimated_hours_to_close=item.get("estimated_hours_to_close"),
                )
                gaps.append(gap)
            except (ValidationError, ValueError, TypeError):
                continue

        return GapReport(
            assessment_id=input_data.assessment_id,
            target_role=input_data.target_role,
            skill_gaps=gaps,
            overall_readiness=float(data.get("overall_readiness", 0.0)),
            recommendations=data.get("recommendations", []),
        )

    def _empty_report(self, input_data: GapAnalysisRequest) -> GapReport:
        """Create an empty gap report.

        Args:
            input_data: The gap analysis request.

        Returns:
            GapReport: Empty gap report.
        """
        return GapReport(
            assessment_id=input_data.assessment_id,
            target_role=input_data.target_role,
            overall_readiness=0.0,
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
