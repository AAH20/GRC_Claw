"""Keyword Research Agent — discovers, scores, and expands keyword opportunities."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class KeywordSuggestion(BaseModel):
    """A single keyword suggestion with scoring metadata.

    Attributes:
        keyword: The suggested keyword phrase.
        search_volume: Estimated monthly search volume.
        competition: Competition level (low, medium, high).
        cpc_estimate: Estimated cost-per-click in USD.
        relevance_score: Relevance to the seed topic (0.0–1.0).
        intent: Search intent category (informational, navigational, transactional).
    """

    keyword: str
    search_volume: int = 0
    competition: str = "medium"
    cpc_estimate: float = 0.0
    relevance_score: float = 0.0
    intent: str = "informational"


class KeywordResearchResult(BaseModel):
    """Result of a keyword research operation.

    Attributes:
        seed_keyword: The original seed keyword.
        suggestions: List of keyword suggestions.
        total_suggestions: Total number of suggestions returned.
    """

    seed_keyword: str
    suggestions: list[KeywordSuggestion] = Field(default_factory=list)
    total_suggestions: int = 0


class KeywordResearchAgent:
    """Agent responsible for keyword discovery and expansion.

    Uses LLM-powered analysis to generate keyword suggestions from seed terms,
    score them by relevance and competition, and categorize by search intent.
    """

    def __init__(self, model: str = "gpt-4o", max_keywords: int = 100) -> None:
        """Initialize the Keyword Research Agent.

        Args:
            model: The LLM model to use for keyword generation.
            max_keywords: Maximum number of keywords to return per research call.
        """
        self.model = model
        self.max_keywords = max_keywords
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

    async def research(
        self,
        seed_keyword: str,
        language: str = "en",
        location: str = "US",
    ) -> KeywordResearchResult:
        """Perform keyword research from a seed keyword.

        Args:
            seed_keyword: The seed keyword to expand from.
            language: Target language for keywords.
            location: Target location for keywords.

        Returns:
            A KeywordResearchResult with scored suggestions.

        Raises:
            ValueError: If seed_keyword is empty.
        """
        if not seed_keyword.strip():
            raise ValueError("Seed keyword cannot be empty")

        logger.info(
            "Starting keyword research",
            seed=seed_keyword,
            language=language,
            location=location,
        )

        llm = self._get_llm()
        prompt = self._build_prompt(seed_keyword, language, location)

        try:
            response = await llm.ainvoke(prompt)
            suggestions = self._parse_response(response.content)
        except Exception as exc:
            logger.error("Keyword research LLM call failed", error=str(exc))
            suggestions = self._fallback_suggestions(seed_keyword)

        result = KeywordResearchResult(
            seed_keyword=seed_keyword,
            suggestions=suggestions[: self.max_keywords],
            total_suggestions=len(suggestions),
        )

        logger.info(
            "Keyword research complete",
            seed=seed_keyword,
            count=len(suggestions),
        )
        return result

    def _build_prompt(self, seed: str, language: str, location: str) -> str:
        """Build the LLM prompt for keyword research.

        Args:
            seed: The seed keyword.
            language: Target language.
            location: Target location.

        Returns:
            The formatted prompt string.
        """
        return (
            f"You are a PPC keyword research expert. Given the seed keyword '{seed}', "
            f"generate up to {self.max_keywords} keyword suggestions for {location} "
            f"in {language}.\n\n"
            "For each keyword, provide:\n"
            "- keyword: the keyword phrase\n"
            "- search_volume: estimated monthly searches (integer)\n"
            "- competition: low, medium, or high\n"
            "- cpc_estimate: estimated CPC in USD\n"
            "- relevance_score: 0.0 to 1.0\n"
            "- intent: informational, navigational, or transactional\n\n"
            "Return ONLY a JSON array of objects with these fields."
        )

    def _parse_response(self, content: str) -> list[KeywordSuggestion]:
        """Parse the LLM response into KeywordSuggestion objects.

        Args:
            content: The raw LLM response content.

        Returns:
            A list of parsed KeywordSuggestion objects.
        """
        import json

        suggestions: list[KeywordSuggestion] = []
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    suggestions.append(KeywordSuggestion(**item))
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse LLM response", error=str(exc))

        return suggestions

    def _fallback_suggestions(self, seed: str) -> list[KeywordSuggestion]:
        """Generate fallback suggestions when LLM is unavailable.

        Args:
            seed: The seed keyword.

        Returns:
            A list of basic KeywordSuggestion objects.
        """
        return [
            KeywordSuggestion(
                keyword=seed,
                search_volume=1000,
                competition="medium",
                cpc_estimate=1.5,
                relevance_score=1.0,
                intent="transactional",
            ),
            KeywordSuggestion(
                keyword=f"best {seed}",
                search_volume=500,
                competition="low",
                cpc_estimate=0.8,
                relevance_score=0.9,
                intent="informational",
            ),
            KeywordSuggestion(
                keyword=f"{seed} near me",
                search_volume=300,
                competition="low",
                cpc_estimate=1.2,
                relevance_score=0.85,
                intent="transactional",
            ),
        ]
