"""Landing Page Optimization Agent — analyzes and recommends landing page improvements."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class LandingPageRecommendation(BaseModel):
    """A single landing page optimization recommendation.

    Attributes:
        category: The category (e.g., 'headline', 'cta', 'speed', 'mobile').
        priority: Priority level (high, medium, low).
        issue: Description of the issue found.
        recommendation: Specific actionable recommendation.
        expected_impact: Expected impact on conversion rate.
    """

    category: str
    priority: str = "medium"
    issue: str = ""
    recommendation: str = ""
    expected_impact: str = ""


class LandingPageAnalysisResult(BaseModel):
    """Result of a landing page analysis.

    Attributes:
        url: The analyzed landing page URL.
        recommendations: List of optimization recommendations.
        overall_score: Overall landing page score (0–100).
        total_recommendations: Total number of recommendations.
    """

    url: str
    recommendations: list[LandingPageRecommendation] = Field(default_factory=list)
    overall_score: int = 0
    total_recommendations: int = 0


class LandingPageOptimizationAgent:
    """Agent responsible for landing page analysis and optimization.

    Evaluates landing pages against CRO best practices and provides
    actionable recommendations to improve conversion rates.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Landing Page Optimization Agent.

        Args:
            model: The LLM model to use for analysis.
        """
        self.model = model
        self._llm: Any = None

    def _get_llm(self) -> Any:
        """Lazy-load the LLM client.

        Returns:
            The LangChain LLM instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(model=self.model, temperature=0.3)
        return self._llm

    async def analyze(self, url: str, page_content: str | None = None) -> LandingPageAnalysisResult:
        """Analyze a landing page and generate optimization recommendations.

        Args:
            url: The landing page URL to analyze.
            page_content: Optional pre-fetched page content.

        Returns:
            A LandingPageAnalysisResult with recommendations.

        Raises:
            ValueError: If url is empty.
        """
        if not url.strip():
            raise ValueError("URL cannot be empty")

        logger.info("Analyzing landing page", url=url)

        if page_content is None:
            page_content = await self._fetch_page(url)

        recommendations = await self._generate_recommendations(url, page_content)
        score = self._compute_score(recommendations)

        result = LandingPageAnalysisResult(
            url=url,
            recommendations=recommendations,
            overall_score=score,
            total_recommendations=len(recommendations),
        )

        logger.info("Landing page analysis complete", url=url, score=score)
        return result

    async def _fetch_page(self, url: str) -> str:
        """Fetch the landing page content.

        Args:
            url: The URL to fetch.

        Returns:
            The page content as a string.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                return response.text[:10000]
        except Exception as exc:
            logger.warning("Failed to fetch landing page", url=url, error=str(exc))
            return ""

    async def _generate_recommendations(
        self,
        url: str,
        content: str,
    ) -> list[LandingPageRecommendation]:
        """Generate optimization recommendations using LLM analysis.

        Args:
            url: The landing page URL.
            content: The page content.

        Returns:
            A list of LandingPageRecommendation objects.
        """
        llm = self._get_llm()
        prompt = (
            f"Analyze this landing page for conversion rate optimization:\n"
            f"URL: {url}\n"
            f"Content (first 10000 chars):\n{content}\n\n"
            "Provide recommendations in these categories: headline, cta, speed, mobile, "
            "social_proof, form, navigation, content_clarity.\n\n"
            "For each recommendation, provide:\n"
            "- category: the category\n"
            "- priority: high, medium, or low\n"
            "- issue: what's wrong\n"
            "- recommendation: what to do\n"
            "- expected_impact: expected conversion rate improvement\n\n"
            "Return ONLY a JSON array of objects with these fields."
        )

        try:
            response = await llm.ainvoke(prompt)
            return self._parse_recommendations(response.content)
        except Exception as exc:
            logger.error("Landing page analysis LLM call failed", error=str(exc))
            return self._fallback_recommendations()

    def _parse_recommendations(self, content: str) -> list[LandingPageRecommendation]:
        """Parse the LLM response into recommendation objects.

        Args:
            content: The raw LLM response content.

        Returns:
            A list of LandingPageRecommendation objects.
        """
        import json

        recommendations: list[LandingPageRecommendation] = []
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    recommendations.append(LandingPageRecommendation(**item))
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse LLM response", error=str(exc))

        return recommendations

    def _compute_score(self, recommendations: list[LandingPageRecommendation]) -> int:
        """Compute an overall landing page score.

        Args:
            recommendations: The list of recommendations.

        Returns:
            A score between 0 and 100.
        """
        if not recommendations:
            return 80

        penalty = 0
        for rec in recommendations:
            if rec.priority == "high":
                penalty += 15
            elif rec.priority == "medium":
                penalty += 8
            else:
                penalty += 3

        return max(0, 100 - penalty)

    def _fallback_recommendations(self) -> list[LandingPageRecommendation]:
        """Generate fallback recommendations when LLM is unavailable.

        Returns:
            A list of basic LandingPageRecommendation objects.
        """
        return [
            LandingPageRecommendation(
                category="headline",
                priority="high",
                issue="Headline may not clearly communicate value proposition",
                recommendation=(
                    "Ensure headline matches ad copy and clearly states the primary benefit"
                ),
                expected_impact="10-20% improvement in conversion rate",
            ),
            LandingPageRecommendation(
                category="cta",
                priority="medium",
                issue="CTA button may not be prominent enough",
                recommendation="Use contrasting color for CTA button and place above the fold",
                expected_impact="5-15% improvement in click-through rate",
            ),
        ]
