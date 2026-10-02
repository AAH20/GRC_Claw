"""Keyword optimization agent using LangChain DeepAgents."""

import json
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from job_description_optimizer.agents import BaseAgent
from job_description_optimizer.config import Settings
from job_description_optimizer.models import JobDescription, KeywordReport


class KeywordOptimizerAgent(BaseAgent[JobDescription, KeywordReport]):
    """Agent that optimizes keyword usage in job descriptions.

    Uses LangChain DeepAgents to identify missing keywords,
    analyze keyword density, and suggest industry-relevant terms.
    """

    @property
    def name(self) -> str:
        """Get the agent name."""
        return "keyword_optimizer"

    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Optimizes keyword usage for better searchability and relevance"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for keyword optimization.

        Returns:
            System prompt string.
        """
        return """You are an expert in recruitment SEO and talent acquisition keyword optimization.

Your task is to analyze job descriptions for keyword optimization to improve:
1. **Search Visibility**: Keywords candidates use when searching for jobs
2. **ATS Matching**: Keywords that applicant tracking systems use for matching
3. **Industry Relevance**: Current industry-standard terminology
4. **Keyword Density**: Optimal usage without stuffing (aim for 1-3% density)

For the given job description:
1. Extract all relevant keywords currently present
2. Identify important keywords that are MISSING
3. Suggest additional relevant keywords based on the role, industry, and skills
4. Analyze keyword density for key terms
5. Provide an optimized version with better keyword placement

Return your analysis in the following JSON format:
{
    "optimized_text": "the job description with optimized keywords",
    "extracted_keywords": ["keyword1", "keyword2"],
    "suggested_keywords": ["suggested1", "suggested2"],
    "missing_keywords": ["missing1", "missing2"],
    "keyword_density": {
        "keyword1": 0.02,
        "keyword2": 0.015
    },
    "industry_relevance": 0.0-1.0,
    "recommendations": ["recommendation1", "recommendation2"]
}

Focus on keywords that are commonly used in job searches and ATS systems."""

    async def analyze(self, input_data: JobDescription) -> KeywordReport:
        """Analyze and optimize keywords in a job description.

        Args:
            input_data: Job description to analyze.

        Returns:
            KeywordReport with keyword analysis and optimization suggestions.
        """
        prompt = f"""Optimize keywords in the following job description:

Title: {input_data.title}
Description: {input_data.description}
Company: {input_data.company or 'Not specified'}
Industry: {input_data.industry or 'Not specified'}
Skills: {', '.join(input_data.skills) if input_data.skills else 'Not specified'}
Responsibilities: {', '.join(input_data.responsibilities) if input_data.responsibilities else 'Not specified'}
Qualifications: {', '.join(input_data.qualifications) if input_data.qualifications else 'Not specified'}
Experience Level: {input_data.experience_level or 'Not specified'}
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
                    "optimized_text": input_data.description,
                    "extracted_keywords": [],
                    "suggested_keywords": [],
                    "missing_keywords": [],
                    "keyword_density": {},
                    "industry_relevance": 0.5,
                    "recommendations": ["Unable to parse keyword analysis results"],
                }

        return KeywordReport(
            original_text=input_data.description,
            optimized_text=data.get("optimized_text", input_data.description),
            extracted_keywords=data.get("extracted_keywords", []),
            suggested_keywords=data.get("suggested_keywords", []),
            missing_keywords=data.get("missing_keywords", []),
            keyword_density=data.get("keyword_density", {}),
            industry_relevance=float(data.get("industry_relevance", 0.5)),
            recommendations=data.get("recommendations", []),
        )

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "keyword_extraction",
            "keyword_suggestion",
            "density_analysis",
            "industry_terminology",
            "search_optimization",
        ]
