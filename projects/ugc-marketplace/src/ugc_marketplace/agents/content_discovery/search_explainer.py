"""Search explainer agent for content discovery."""

from __future__ import annotations

import time
from typing import Any

import structlog

from ugc_marketplace.agents.content_discovery.base import BaseAgent
from ugc_marketplace.agents.content_discovery.types import (
    SearchExplanation,
    SearchRequest,
    SearchResponse,
)

logger = structlog.get_logger(__name__)


class SearchExplainerAgent(
    BaseAgent[tuple["SearchRequest", "SearchResponse"], "SearchExplanation"]
):
    """Agent that explains search results to users.

    Provides transparency into why specific results were returned,
    helping users understand and refine their searches.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for search explanation.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._analyze_query,
            self._explain_ranking,
            self._suggest_refinements,
        ]

        from deepagents import create_deep_agent

        agent = create_deep_agent(
            tools=tools,
            system_prompt=(
                "You are a search explanation specialist. Analyze search "
                "queries and results to provide clear, helpful explanations "
                "of why specific content was returned. Suggest query "
                "refinements to improve results."
            ),
        )
        return agent

    async def execute(
        self, input_data: tuple[SearchRequest, SearchResponse]
    ) -> SearchExplanation:
        """Execute search explanation.

        Args:
            input_data: Tuple of search request and response.

        Returns:
            Search explanation with analysis and suggestions.
        """
        start_time = time.monotonic()
        result = await self._timed_execute(input_data, "execute")
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Search explanation completed",
            elapsed_ms=elapsed_ms,
        )
        return result

    @staticmethod
    async def _analyze_query(query: str) -> dict[str, Any]:
        """Analyze a search query.

        Args:
            query: Search query string.

        Returns:
            Query analysis data.
        """
        return {"query": query, "analysis": {}}

    @staticmethod
    async def _explain_ranking(results: list[dict[str, Any]]) -> dict[str, Any]:
        """Explain result ranking.

        Args:
            results: Search results.

        Returns:
            Ranking explanation.
        """
        return {"explanations": []}

    @staticmethod
    async def _suggest_refinements(query: str) -> list[str]:
        """Suggest query refinements.

        Args:
            query: Original query.

        Returns:
            List of suggested refinements.
        """
        return []
