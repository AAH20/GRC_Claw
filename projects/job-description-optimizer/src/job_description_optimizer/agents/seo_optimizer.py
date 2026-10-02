"""SEO optimization agent using LangChain DeepAgents."""

import json
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from job_description_optimizer.agents import BaseAgent
from job_description_optimizer.config import Settings
from job_description_optimizer.models import JobDescription, SEOReport


class SEOOptimizerAgent(BaseAgent[JobDescription, SEOReport]):
    """Agent that optimizes job descriptions for search engine visibility.

    Uses LangChain DeepAgents to improve keyword usage, readability,
    and overall SEO performance of job postings.
    """

    @property
    def name(self) -> str:
        """Get the agent name."""
        return "seo_optimizer"

    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Optimizes job descriptions for search engine visibility"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for SEO optimization.

        Returns:
            System prompt string.
        """
        return """You are an expert SEO specialist for job postings and recruitment content.

Your task is to optimize job descriptions for search engine visibility while maintaining
readability and natural language flow. Focus on:

1. **Keyword Optimization**: Identify and strategically place relevant keywords that
   candidates and recruiters commonly search for
2. **Title Optimization**: Suggest SEO-friendly job titles that include key terms
3. **Meta Description**: Create compelling meta descriptions for job listing pages
4. **Readability**: Ensure the text is easy to read with proper structure
5. **Keyword Density**: Maintain optimal keyword density (1-3%) without keyword stuffing

Return your analysis in the following JSON format:
{
    "optimized_text": "the full job description with SEO improvements",
    "title_suggestions": ["suggestion1", "suggestion2", "suggestion3"],
    "meta_description": "a compelling meta description under 160 characters",
    "keyword_density": {
        "keyword1": 0.02,
        "keyword2": 0.015
    },
    "readability_score": 0.0-1.0,
    "seo_score": 0.0-1.0,
    "recommendations": ["recommendation1", "recommendation2"]
}

Balance SEO optimization with natural, engaging language."""

    async def analyze(self, input_data: JobDescription) -> SEOReport:
        """Analyze and optimize job description for SEO.

        Args:
            input_data: Job description to optimize.

        Returns:
            SEOReport with optimization results and recommendations.
        """
        prompt = f"""Optimize the following job description for SEO:

Title: {input_data.title}
Description: {input_data.description}
Company: {input_data.company or 'Not specified'}
Location: {input_data.location or 'Not specified'}
Industry: {input_data.industry or 'Not specified'}
Skills: {', '.join(input_data.skills) if input_data.skills else 'Not specified'}
Employment Type: {input_data.employment_type or 'Not specified'}
Experience Level: {input_data.experience_level or 'Not specified'}

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
                    "title_suggestions": [],
                    "meta_description": None,
                    "keyword_density": {},
                    "readability_score": 0.5,
                    "seo_score": 0.5,
                    "recommendations": ["Unable to parse SEO analysis results"],
                }

        return SEOReport(
            original_text=input_data.description,
            optimized_text=data.get("optimized_text", input_data.description),
            title_suggestions=data.get("title_suggestions", []),
            meta_description=data.get("meta_description"),
            keyword_density=data.get("keyword_density", {}),
            readability_score=float(data.get("readability_score", 0.5)),
            seo_score=float(data.get("seo_score", 0.5)),
            recommendations=data.get("recommendations", []),
        )

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "keyword_optimization",
            "title_optimization",
            "meta_description_generation",
            "readability_analysis",
            "search_visibility",
        ]
