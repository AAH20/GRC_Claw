"""Review Analyzer Agent for fetching and analyzing employer reviews."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from employer_branding.agents.base import BaseAgent
from employer_branding.models import Review, ReviewFetchRequest, ReviewSource, SentimentLabel


class ReviewAnalyzerAgent(BaseAgent[list[Review]]):
    """Agent that fetches and analyzes employer reviews from various sources.

    Retrieves reviews from platforms like Glassdoor, Indeed, and LinkedIn,
    then performs sentiment analysis and extracts key insights.
    """

    def __init__(self) -> None:
        """Initialize the review analyzer agent."""
        super().__init__()
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template for review analysis.

        Returns:
            Configured ChatPromptTemplate.
        """
        system_message = """You are an expert review analysis engine.
Analyze employer reviews and return a JSON array of review objects:
[
    {
        "rating": float between 0 and 5,
        "title": "review title or null",
        "content": "review content",
        "pros": "pros mentioned or null",
        "cons": "cons mentioned or null",
        "sentiment": "very_positive|positive|neutral|negative|very_negative",
        "sentiment_score": float between -1 and 1,
        "is_recommended": boolean or null
    }
]

Extract structured information accurately from each review."""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content="{input}"),
        ])

    async def run(self, request: ReviewFetchRequest) -> list[Review]:
        """Fetch and analyze reviews for a company.

        Args:
            request: Review fetch request with company and source.

        Returns:
            List of analyzed Review objects.

        Raises:
            ValueError: If request parameters are invalid.
            RuntimeError: If fetching or analysis fails.
        """
        self.logger.info(
            "fetching_reviews",
            company=request.company_name,
            source=request.source.value,
            limit=request.limit,
        )

        try:
            raw_reviews = await self._fetch_reviews(request)
            analyzed_reviews = await self._analyze_reviews(raw_reviews, request.source)

            self.logger.info(
                "reviews_analyzed",
                company=request.company_name,
                count=len(analyzed_reviews),
            )
            return analyzed_reviews

        except Exception as exc:
            self.logger.error("review_analysis_failed", error=str(exc))
            raise RuntimeError(f"Failed to analyze reviews: {exc}") from exc

    async def _fetch_reviews(self, request: ReviewFetchRequest) -> list[dict[str, Any]]:
        """Fetch raw reviews from the specified source.

        In production, this would call external APIs (Glassdoor, Indeed, etc.).
        For now, returns mock data for demonstration.

        Args:
            request: Review fetch request.

        Returns:
            List of raw review dictionaries.
        """
        # Mock data for demonstration - in production, call actual APIs
        return [
            {
                "rating": 4.5,
                "title": "Great place to work",
                "content": "Excellent work-life balance and supportive management.",
                "pros": "Good benefits, flexible hours",
                "cons": "Limited career growth",
                "date": "2024-01-15",
            },
            {
                "rating": 3.0,
                "title": "Decent company",
                "content": "Average experience, nothing exceptional but stable.",
                "pros": "Stable job, good colleagues",
                "cons": "Bureaucratic processes",
                "date": "2024-01-10",
            },
        ]

    async def _analyze_reviews(
        self, raw_reviews: list[dict[str, Any]], source: ReviewSource
    ) -> list[Review]:
        """Analyze raw reviews using the LLM.

        Args:
            raw_reviews: List of raw review dictionaries.
            source: Review source platform.

        Returns:
            List of analyzed Review objects.
        """
        import json

        if not raw_reviews:
            return []

        prompt = f"Analyze these reviews from {source.value}:\n\n{json.dumps(raw_reviews, indent=2)}"
        response = await self._model.ainvoke(prompt)
        raw_content = response.content if hasattr(response, "content") else str(response)

        parsed = self._parse_response(raw_content)

        reviews: list[Review] = []
        for item in parsed:
            review = Review(
                source=source,
                rating=item.get("rating", 0.0),
                title=item.get("title"),
                content=item.get("content", ""),
                pros=item.get("pros"),
                cons=item.get("cons"),
                sentiment=SentimentLabel(item["sentiment"]) if item.get("sentiment") else None,
                sentiment_score=item.get("sentiment_score"),
                is_recommended=item.get("is_recommended"),
                metadata={"raw_data": item},
            )
            reviews.append(review)

        return reviews

    def _parse_response(self, raw_content: str) -> list[dict[str, Any]]:
        """Parse the LLM response into a list of review dictionaries.

        Args:
            raw_content: Raw response content from the model.

        Returns:
            List of parsed review dictionaries.

        Raises:
            ValueError: If response cannot be parsed.
        """
        import json

        content = raw_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse review analysis response: {exc}") from exc

        if not isinstance(parsed, list):
            raise ValueError("Expected JSON array in response")

        return parsed
