"""Keyword Research Agent for discovering high-value SEO keywords."""

from __future__ import annotations

from typing import Any

import structlog

from seo_optimizer.agents.base import AgentResult, BaseAgent
from seo_optimizer.integrations.ahrefs import AhrefsClient
from seo_optimizer.integrations.semrush import SEMrushClient

logger = structlog.get_logger(__name__)


class KeywordResearchAgent(BaseAgent[dict[str, Any]]):
    """Agent for discovering and analyzing SEO keywords.

    Uses SEMrush and Ahrefs data to identify high-value keyword
    opportunities based on search volume, difficulty, and relevance.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Keyword Research Agent.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__("KeywordResearchAgent", config)
        self.semrush = SEMrushClient(config)
        self.ahrefs = AhrefsClient(config)

    async def execute(
        self,
        domain: str,
        seed_keywords: list[str] | None = None,
        country: str = "us",
        max_results: int = 50,
        min_search_volume: int = 100,
        max_difficulty: int = 70,
        **kwargs: Any,
    ) -> AgentResult[dict[str, Any]]:
        """Execute keyword research for a given domain.

        Args:
            domain: Target domain to research keywords for.
            seed_keywords: Optional list of seed keywords to expand from.
            country: Country code for localized results.
            max_results: Maximum number of keywords to return.
            min_search_volume: Minimum search volume threshold.
            max_difficulty: Maximum keyword difficulty threshold.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with keyword data and opportunities.
        """
        self.logger.info(
            "Starting keyword research",
            domain=domain,
            country=country,
            max_results=max_results,
        )

        try:
            keywords_data: dict[str, Any] = {
                "domain": domain,
                "country": country,
                "keywords": [],
                "opportunities": [],
                "total_results": 0,
            }

            # Gather keywords from SEMrush
            if self.semrush.is_enabled:
                semrush_keywords = await self.semrush.get_keyword_ideas(
                    domain=domain,
                    seed_keywords=seed_keywords or [],
                    country=country,
                    limit=max_results,
                )
                keywords_data["keywords"].extend(semrush_keywords)

            # Gather keywords from Ahrefs
            if self.ahrefs.is_enabled:
                ahrefs_keywords = await self.ahrefs.get_keyword_ideas(
                    domain=domain,
                    seed_keywords=seed_keywords or [],
                    country=country,
                    limit=max_results,
                )
                keywords_data["keywords"].extend(ahrefs_keywords)

            # Filter and rank keywords
            filtered = self._filter_keywords(
                keywords_data["keywords"],
                min_search_volume=min_search_volume,
                max_difficulty=max_difficulty,
            )
            keywords_data["keywords"] = filtered[:max_results]
            keywords_data["total_results"] = len(filtered)

            # Identify opportunities
            keywords_data["opportunities"] = self._identify_opportunities(filtered)

            return AgentResult(
                success=True,
                data=keywords_data,
                metadata={
                    "sources": ["semrush", "ahrefs"],
                    "filters_applied": {
                        "min_search_volume": min_search_volume,
                        "max_difficulty": max_difficulty,
                    },
                },
            )

        except Exception as exc:
            self.logger.error("Keyword research failed", error=str(exc))
            return AgentResult(
                success=False,
                error=f"Keyword research failed: {exc}",
            )

    def _filter_keywords(
        self,
        keywords: list[dict[str, Any]],
        min_search_volume: int,
        max_difficulty: int,
    ) -> list[dict[str, Any]]:
        """Filter keywords by volume and difficulty thresholds.

        Args:
            keywords: Raw keyword data from APIs.
            min_search_volume: Minimum search volume.
            max_difficulty: Maximum difficulty score.

        Returns:
            Filtered and sorted keyword list.
        """
        filtered = [
            kw
            for kw in keywords
            if kw.get("search_volume", 0) >= min_search_volume
            and kw.get("difficulty", 100) <= max_difficulty
        ]
        return sorted(filtered, key=lambda k: k.get("search_volume", 0), reverse=True)

    def _identify_opportunities(
        self, keywords: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify high-opportunity keywords.

        Args:
            keywords: Filtered keyword list.

        Returns:
            List of keyword opportunities with scores.
        """
        opportunities = []
        for kw in keywords:
            volume = kw.get("search_volume", 0)
            difficulty = kw.get("difficulty", 100)
            opportunity_score = volume / max(difficulty, 1)

            if opportunity_score > 10:
                opportunities.append(
                    {
                        "keyword": kw.get("keyword"),
                        "search_volume": volume,
                        "difficulty": difficulty,
                        "opportunity_score": round(opportunity_score, 2),
                        "cpc": kw.get("cpc", 0),
                        "serp_features": kw.get("serp_features", []),
                    }
                )

        return sorted(
            opportunities, key=lambda o: o["opportunity_score"], reverse=True
        )[:20]
