"""Semantic search agent using vector similarity and LLM reasoning."""

from __future__ import annotations

import time
from typing import Any

import structlog
from langchain_core.tools import tool

from content_discovery.agents.base import BaseAgent
from content_discovery.integrations.vector_store import VectorStoreClient
from content_discovery.models import SearchRequest, SearchResponse, SearchResult

logger = structlog.get_logger()


class SemanticSearchAgent(BaseAgent[SearchRequest, SearchResponse]):
    """Agent that performs semantic search using vector similarity.

    Combines vector store lookups with LLM-based re-ranking and
    query understanding to deliver highly relevant search results.
    """

    def __init__(self, vector_store: VectorStoreClient, llm: Any | None = None) -> None:
        """Initialize the semantic search agent.

        Args:
            vector_store: Client for vector similarity search.
            llm: Optional LLM for query understanding and re-ranking.
        """
        self.vector_store = vector_store
        super().__init__(name="semantic_search", llm=llm)

    def _get_tools(self) -> list[Any]:
        """Get tools available to the search agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return [self._search_tool, self._expand_query_tool]

    @tool
    def _search_tool(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the vector store for semantically similar content.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            list[dict[str, Any]]: Raw search results from vector store.
        """
        return self.vector_store.search(query=query, limit=limit)

    @tool
    def _expand_query_tool(self, query: str) -> list[str]:
        """Expand a search query with related terms for better recall.

        Args:
            query: Original search query.

        Returns:
            list[str]: Expanded query variations.
        """
        if self.llm is None:
            return [query]
        try:
            response = self.llm.invoke(
                f"Generate 3 alternative search queries for: {query}. "
                "Return only the queries, one per line."
            )
            lines = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
            return lines[:3]
        except Exception:
            logger.warning("query_expansion_failed", query=query)
            return [query]

    async def execute(self, input_data: SearchRequest) -> SearchResponse:
        """Execute semantic search for the given request.

        Args:
            input_data: Search request with query and parameters.

        Returns:
            SearchResponse: Search results with scores and metadata.
        """
        start = time.monotonic()

        # Perform vector similarity search
        raw_results = await self._perform_vector_search(input_data)

        # Re-rank results using LLM if available
        ranked_results = await self._rerank_results(input_data.query, raw_results)

        # Filter by minimum score
        filtered = [r for r in ranked_results if r.score >= input_data.min_score]

        # Apply pagination
        paginated = filtered[input_data.offset : input_data.offset + input_data.limit]

        elapsed = (time.monotonic() - start) * 1000

        return SearchResponse(
            results=paginated,
            total=len(filtered),
            query=input_data.query,
            took_ms=round(elapsed, 2),
            personalized=False,
        )

    async def _perform_vector_search(self, request: SearchRequest) -> list[SearchResult]:
        """Perform vector similarity search.

        Args:
            request: Search request.

        Returns:
            list[SearchResult]: Raw search results.
        """
        try:
            raw = self.vector_store.search(
                query=request.query,
                limit=request.limit * 3,  # Fetch extra for re-ranking
                filters=request.filters,
            )
            return [
                SearchResult(
                    id=item["id"],
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    url=item.get("url"),
                    score=float(item.get("score", 0.0)),
                    metadata=item.get("metadata", {}),
                    content_type=item.get("content_type", "article"),
                    tags=item.get("tags", []),
                )
                for item in raw
            ]
        except Exception as exc:
            logger.error("vector_search_failed", error=str(exc))
            return []

    async def _rerank_results(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """Re-rank search results using LLM reasoning.

        Args:
            query: Original search query.
            results: Initial search results.

        Returns:
            list[SearchResult]: Re-ranked results.
        """
        if not results or self.llm is None:
            return results

        try:
            result_texts = "\n".join(
                f"ID: {r.id}, Title: {r.title}, Content: {r.content[:200]}"
                for r in results[:20]
            )
            response = self.llm.invoke(
                f"Re-rank these search results for query '{query}' by relevance. "
                f"Return only the IDs in order, one per line:\n{result_texts}"
            )
            ordered_ids = [
                line.strip().replace("ID: ", "")
                for line in response.content.strip().split("\n")
                if line.strip()
            ]
            id_to_result = {r.id: r for r in results}
            reranked = [id_to_result[rid] for rid in ordered_ids if rid in id_to_result]
            # Add any missing results at the end
            for r in results:
                if r not in reranked:
                    reranked.append(r)
            return reranked
        except Exception:
            logger.warning("reranking_failed", query=query)
            return results
