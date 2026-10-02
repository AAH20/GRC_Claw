"""Tone analysis agent using LangChain DeepAgents."""

import json
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from job_description_optimizer.agents import BaseAgent
from job_description_optimizer.config import Settings
from job_description_optimizer.models import JobDescription, ToneReport, ToneType


class ToneAnalyzerAgent(BaseAgent[JobDescription, ToneReport]):
    """Agent that analyzes and improves the tone of job descriptions.

    Uses LangChain DeepAgents to evaluate tone, inclusivity,
    and provide suggestions for improvement.
    """

    @property
    def name(self) -> str:
        """Get the agent name."""
        return "tone_analyzer"

    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Analyzes and improves the tone of job descriptions"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for tone analysis.

        Returns:
            System prompt string.
        """
        return """You are an expert in organizational psychology and inclusive communication.

Your task is to analyze the tone of job descriptions and evaluate how they will be
perceived by diverse candidates. Focus on:

1. **Tone Detection**: Identify the primary tone(s) from: formal, casual, professional,
   friendly, authoritative, inclusive, enthusiastic, neutral
2. **Inclusivity Assessment**: Evaluate how welcoming the language is to underrepresented
   groups, including people with disabilities, different cultural backgrounds, and
   non-traditional career paths
3. **Engagement Level**: Assess how engaging and motivating the description is
4. **Authenticity**: Evaluate whether the tone feels genuine or corporate/artificial
5. **Improvement Suggestions**: Provide specific suggestions to make the tone more
   inclusive and engaging

Return your analysis in the following JSON format:
{
    "detected_tones": ["tone1", "tone2"],
    "primary_tone": "primary_tone",
    "tone_scores": {
        "formal": 0.0-1.0,
        "casual": 0.0-1.0,
        "professional": 0.0-1.0,
        "friendly": 0.0-1.0,
        "authoritative": 0.0-1.0,
        "inclusive": 0.0-1.0,
        "enthusiastic": 0.0-1.0,
        "neutral": 0.0-1.0
    },
    "inclusivity_score": 0.0-1.0,
    "suggestions": ["suggestion1", "suggestion2"],
    "improved_text": "the job description with improved tone (optional)"
}

Be constructive and specific in your feedback."""

    async def analyze(self, input_data: JobDescription) -> ToneReport:
        """Analyze the tone of a job description.

        Args:
            input_data: Job description to analyze.

        Returns:
            ToneReport with tone analysis and improvement suggestions.
        """
        prompt = f"""Analyze the tone of the following job description:

Title: {input_data.title}
Description: {input_data.description}
Company: {input_data.company or 'Not specified'}
Industry: {input_data.industry or 'Not specified'}
Employment Type: {input_data.employment_type or 'Not specified'}

Provide your analysis in the specified JSON format."""

        response = await self._invoke_llm(prompt)

        try:
            data: dict[str, Any] = json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
            else:
                data = {
                    "detected_tones": ["neutral"],
                    "primary_tone": "neutral",
                    "tone_scores": {},
                    "inclusivity_score": 0.5,
                    "suggestions": ["Unable to parse tone analysis results"],
                    "improved_text": None,
                }

        detected_tones = [
            ToneType(t) for t in data.get("detected_tones", ["neutral"])
        ]
        primary_tone = ToneType(data.get("primary_tone", "neutral"))

        return ToneReport(
            original_text=input_data.description,
            detected_tones=detected_tones,
            primary_tone=primary_tone,
            tone_scores=data.get("tone_scores", {}),
            inclusivity_score=float(data.get("inclusivity_score", 0.5)),
            suggestions=data.get("suggestions", []),
            improved_text=data.get("improved_text"),
        )

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "tone_detection",
            "inclusivity_assessment",
            "engagement_analysis",
            "authenticity_evaluation",
            "communication_optimization",
        ]
