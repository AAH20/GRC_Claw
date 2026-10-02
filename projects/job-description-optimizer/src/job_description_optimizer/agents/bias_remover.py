"""Bias removal agent using LangChain DeepAgents."""

import json
from typing import Any

from job_description_optimizer.agents import BaseAgent
from job_description_optimizer.models import (
    BiasInstance,
    BiasReport,
    BiasType,
    JobDescription,
)


class BiasRemoverAgent(BaseAgent[JobDescription, BiasReport]):
    """Agent that detects and removes biased language from job descriptions.

    Uses LangChain DeepAgents to identify gendered, ageist, ableist,
    and other forms of biased language, then suggests inclusive alternatives.
    """

    @property
    def name(self) -> str:
        """Get the agent name."""
        return "bias_remover"

    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Detects and removes biased language from job descriptions"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for bias detection.

        Returns:
            System prompt string.
        """
        return """You are an expert in inclusive language and bias detection in job postings.

Your task is to analyze job descriptions and identify any biased language including:
- Gendered language (e.g., "he/she", "mankind", "chairman", "manpower")
- Age-related bias (e.g., "young and energetic", "digital native", "recent graduate")
- Ableist language (e.g., "must be able to stand for long periods" when not essential)
- Cultural bias (e.g., "native English speaker", "cultural fit")
- Racial bias (e.g., "English-first" requirements)
- Socioeconomic bias (e.g., "prestigious university", "elite college")

For each instance of bias found:
1. Identify the type of bias
2. Quote the original text
3. Provide a specific, actionable suggestion for replacement
4. Explain why the original text is problematic
5. Assign a severity score from 0.0 (minor) to 1.0 (severe)

Return your analysis in the following JSON format:
{
    "cleaned_text": "the full job description with biased language replaced",
    "instances": [
        {
            "bias_type": (
                "gendered_language|age_related|cultural|ableist|racial|socioeconomic|other"
            ),
            "original_text": "the biased text",
            "suggestion": "the suggested replacement",
            "explanation": "why this is biased",
            "severity": 0.0-1.0
        }
    ],
    "overall_score": 0.0-1.0,
    "summary": "brief summary of findings"
}

Be thorough but fair. Only flag genuinely problematic language."""

    async def analyze(self, input_data: JobDescription) -> BiasReport:
        """Analyze job description for biased language.

        Args:
            input_data: Job description to analyze.

        Returns:
            BiasReport with detected instances and cleaned text.
        """
        prompt = f"""Analyze the following job description for biased language:

Title: {input_data.title}
Description: {input_data.description}
Company: {input_data.company or 'Not specified'}
Industry: {input_data.industry or 'Not specified'}

Provide your analysis in the specified JSON format."""

        response = await self._invoke_llm(prompt)

        try:
            data: dict[str, Any] = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
            else:
                data = {
                    "cleaned_text": input_data.description,
                    "instances": [],
                    "overall_score": 0.0,
                    "summary": "Unable to parse analysis results",
                }

        instances = [
            BiasInstance(
                bias_type=BiasType(inst.get("bias_type", "other")),
                original_text=inst.get("original_text", ""),
                suggestion=inst.get("suggestion", ""),
                explanation=inst.get("explanation", ""),
                severity=float(inst.get("severity", 0.5)),
            )
            for inst in data.get("instances", [])
        ]

        return BiasReport(
            original_text=input_data.description,
            cleaned_text=data.get("cleaned_text", input_data.description),
            instances=instances,
            overall_score=float(data.get("overall_score", 0.0)),
            summary=data.get("summary", ""),
        )

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "bias_detection",
            "inclusive_language",
            "gender_neutrality",
            "age_discrimination_detection",
            "cultural_sensitivity",
        ]
