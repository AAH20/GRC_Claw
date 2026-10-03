"""Curation Explainer Agent for community curation."""

from __future__ import annotations

import structlog

from ugc_marketplace.agents.community_curation.base import BaseCurationAgent

logger = structlog.get_logger(__name__)


class CurationExplainerAgent(BaseCurationAgent[list["ContentItem"], dict[str, str]]):
    """Agent that explains curation decisions to users.

    Provides transparency into why specific content was
    selected, ranked, or filtered in community curation.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for curation explanation.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._explain_ranking,
            self._explain_filtering,
            self._explain_diversity,
        ]

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a curation explanation specialist. Explain curation "
                "decisions clearly and transparently to users. Provide insights "
                "into why content was selected, ranked, or filtered."
            ),
        )
        return agent

    async def execute(self, input_data: list[ContentItem]) -> dict[str, str]:
        """Execute curation explanation.

        Args:
            input_data: List of content items to explain.

        Returns:
            Dictionary of explanations keyed by content ID.
        """
        self._tasks_processed += 1
        explanations: dict[str, str] = {}

        for item in input_data:
            explanations[item.content_id] = (
                "This content was selected based on its engagement metrics, "
                "quality score, and relevance to community interests."
            )

        logger.info("Curation explanation completed", items_explained=len(explanations))
        return explanations

    @staticmethod
    async def _explain_ranking(item: ContentItem) -> str:
        """Explain ranking decision.

        Args:
            item: Content item.

        Returns:
            Ranking explanation.
        """
        return "Ranked based on engagement and quality metrics."

    @staticmethod
    async def _explain_filtering(item: ContentItem) -> str:
        """Explain filtering decision.

        Args:
            item: Content item.

        Returns:
            Filtering explanation.
        """
        return "Passed quality and policy filters."

    @staticmethod
    async def _explain_diversity(items: list[ContentItem]) -> str:
        """Explain diversity in selection.

        Args:
            items: Content items.

        Returns:
            Diversity explanation.
        """
        return "Selected to ensure diverse content representation."
