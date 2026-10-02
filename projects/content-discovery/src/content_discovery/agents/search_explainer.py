"""Search explainer agent for generating human-readable explanations of search results."""

from __future__ import annotations

import time
from typing import Any

import structlog
from langchain_core.tools import tool

from content_discovery.agents.base import BaseAgent
from content_discovery.models import SearchExplanation, SearchRequest, SearchResponse

logger = structlog.get_logger()


class SearchExplainerAgent(BaseAgent[tuple[SearchRequest, SearchResponse], SearchExplanation]):
    """Agent that generates human-readable explanations of search results.

    Uses LLM reasoning to explain why certain results were returned,
    what factors influenced ranking, and how to refine queries.
    """

    def __init__(self, llm: Any | None = None) -> None:
        """Initialize the search explainer agent.

        Args:
            llm: LLM for generating explanations.
        """
        super().__init__(name="search_explainer", llm=llm)

    def _get_tools(self) -> list[Any]:
        """Get tools available to the explainer agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return [self._analyze_ranking_factors_tool]

    @tool
    def _analyze_ranking_factors_tool(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[str]:
        """Analyze the factors that influenced result ranking.

        Args:
            query: Search query.
            results: Search results with scores.

        Returns:
            list[str]: Identified ranking factors.
        """
        factors = []
        if not results:
            return ["No results found"]

        scores = [r.get("score", 0) for r in results]
        if scores:
            factors.append(f"Relevance scores range from {min(scores):.2f} to {max(scores):.2f}")

        # Check for metadata patterns
        content_types = set(r.get("metadata", {}).get("content_type", "unknown") for r in results)
        if len(content_types) > 1:
            factors.append(f"Results span multiple content types: {', '.join(content_types)}")

        # Check for tag patterns
        all_tags: set[str] = set()
        for r in results:
            all_tags.update(r.get("metadata", {}).get("tags", []))
        if all_tags:
            factors.append(f"Common topics: {', '.join(list(all_tags)[:5])}")

        return factors

    async def execute(
        self, input_data: tuple[SearchRequest, SearchResponse]
    ) -> SearchExplanation:
        """Generate an explanation for search results.

        Args:
            input_data: Tuple of (SearchRequest, SearchResponse).

        Returns:
            SearchExplanation: Human-readable explanation.
        """
        start = time.monotonic()
        request, response = input_data

        if self.llm is None:
            return self._fallback_explanation(request, response)

        try:
            # Build context for the LLM
            results_text = "\n".join(
                f"Rank {i+1}: {r.title} (score: {r.score:.2f}, type: {r.content_type})"
                for i, r in enumerate(response.results[:10])
            )

            # Generate explanation
            explanation = await self._generate_explanation(request, response, results_text)

            # Analyze ranking factors
            factors = self._analyze_ranking_factors(request, response)

            # Generate query refinement suggestions
            refinements = await self._suggest_refinements(request, response)

            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                "explanation_generated",
                query=request.query,
                elapsed_ms=round(elapsed, 2),
            )

            return SearchExplanation(
                query=request.query,
                explanation=explanation,
                factors=factors,
                confidence=0.85,
                suggested_refinements=refinements,
            )
        except Exception as exc:
            logger.error("explanation_generation_failed", error=str(exc))
            return self._fallback_explanation(request, response)

    async def _generate_explanation(
        self, request: SearchRequest, response: SearchResponse, results_text: str
    ) -> str:
        """Generate the main explanation text.

        Args:
            request: Search request.
            response: Search response.
            results_text: Formatted results text.

        Returns:
            str: Explanation text.
        """
        try:
            prompt = (
                f"Explain these search results for the query '{request.query}' "
                f"in 2-3 sentences. The search found {response.total} results. "
                f"Top results:\n{results_text}\n\n"
                f"Explain why these results were selected and what they have in common."
            )
            result = self.llm.invoke(prompt)
            return result.content.strip()
        except Exception:
            return self._fallback_explanation(request, response).explanation

    def _analyze_ranking_factors(
        self, request: SearchRequest, response: SearchResponse
    ) -> list[str]:
        """Analyze factors that influenced result ranking.

        Args:
            request: Search request.
            response: Search response.

        Returns:
            list[str]: Ranking factors.
        """
        if not response.results:
            return ["No results matched the query"]

        factors = []
        scores = [r.score for r in response.results]
        factors.append(
            f"Relevance scores range from {min(scores):.2f} to {max(scores):.2f}"
        )

        content_types = set(r.content_type for r in response.results)
        if len(content_types) > 1:
            factors.append(f"Results span multiple content types: {', '.join(content_types)}")

        all_tags: set[str] = set()
        for r in response.results:
            all_tags.update(r.tags)
        if all_tags:
            factors.append(f"Common topics: {', '.join(list(all_tags)[:5])}")

        if request.filters:
            factors.append(f"Filters applied: {', '.join(request.filters.keys())}")

        return factors

    async def _suggest_refinements(
        self, request: SearchRequest, response: SearchResponse
    ) -> list[str]:
        """Suggest query refinements.

        Args:
            request: Search request.
            response: Search response.

        Returns:
            list[str]: Suggested query refinements.
        """
        if self.llm is None:
            return []

        try:
            prompt = (
                f"For the search query '{request.query}' which returned "
                f"{response.total} results, suggest 3 alternative query "
                f"formulations that might yield better or different results. "
                f"Return only the queries, one per line."
            )
            result = self.llm.invoke(prompt)
            lines = [
                line.strip()
                for line in result.content.strip().split("\n")
                if line.strip()
            ]
            return lines[:3]
        except Exception:
            return []

    def _fallback_explanation(
        self, request: SearchRequest, response: SearchResponse
    ) -> SearchExplanation:
        """Generate a fallback explanation without LLM.

        Args:
            request: Search request.
            response: Search response.

        Returns:
            SearchExplanation: Basic explanation.
        """
        if not response.results:
            explanation = (
                f"No results found for '{request.query}'. "
                "Try broadening your search terms."
            )
        else:
            explanation = (
                f"Found {response.total} results for '{request.query}'. "
                f"Results are ranked by semantic relevance to your query."
            )

        return SearchExplanation(
            query=request.query,
            explanation=explanation,
            factors=self._analyze_ranking_factors(request, response),
            confidence=0.5,
            suggested_refinements=[],
        )
