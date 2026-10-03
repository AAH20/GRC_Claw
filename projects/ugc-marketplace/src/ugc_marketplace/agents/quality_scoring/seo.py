"""SEO scorer agent for quality assessment."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from ugc_marketplace.agents.quality_scoring.base import AgentResult, BaseScoringAgent
from ugc_marketplace.agents.quality_scoring.types import DimensionScore
from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)


class SEOScorerAgent(BaseScoringAgent["DimensionScore"]):
    """Agent that scores content for SEO optimization.

    Analyzes content for SEO best practices including
    keyword usage, structure, and metadata.
    """

    def __init__(self) -> None:
        """Initialize the SEO scorer agent."""
        super().__init__()
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    async def score(
        self, content: str, context: dict[str, Any] | None = None
    ) -> AgentResult[DimensionScore]:
        """Score content for SEO.

        Args:
            content: Content to score.
            context: Optional context with target keywords.

        Returns:
            Agent result with SEO score.
        """
        try:
            score = self._calculate_seo_score(content, context)
            return AgentResult(
                success=True,
                data=score,
                reasoning="SEO score calculated based on content analysis.",
            )
        except Exception as exc:
            logger.error("SEO scoring failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                reasoning="Failed to calculate SEO score.",
            )

    def _calculate_seo_score(
        self, content: str, context: dict[str, Any] | None = None
    ) -> DimensionScore:
        """Calculate SEO score for content.

        Args:
            content: Content to analyze.
            context: Optional context with target keywords.

        Returns:
            Dimension score with SEO metrics.
        """
        from ugc_marketplace.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

        target_keywords = (context or {}).get("target_keywords", [])
        word_count = len(content.split())

        has_headings = bool(re.search(r"^#{1,6}\s", content, re.MULTILINE))
        has_links = bool(re.search(r"\[.*?\]\(.*?\)", content))
        has_images = bool(re.search(r"!\[.*?\]\(.*?\)", content))
        has_meta_description = (context or {}).get("meta_description", "") != ""

        keyword_score = 0.0
        if target_keywords:
            keyword_matches = sum(
                1 for kw in target_keywords if kw.lower() in content.lower()
            )
            keyword_score = keyword_matches / len(target_keywords)

        score_value = 0.3
        if has_headings:
            score_value += 0.15
        if has_links:
            score_value += 0.1
        if has_images:
            score_value += 0.1
        if has_meta_description:
            score_value += 0.1
        if word_count > 300:
            score_value += 0.1
        score_value += keyword_score * 0.15

        score_value = min(score_value, 1.0)

        if score_value >= 0.8:
            level = ScoreLevel.HIGH
        elif score_value >= 0.5:
            level = ScoreLevel.MEDIUM
        else:
            level = ScoreLevel.LOW

        return DimensionScore(
            dimension=ScoreDimension.SEO,
            score=score_value,
            level=level,
            metrics={
                "word_count": word_count,
                "has_headings": has_headings,
                "has_links": has_links,
                "has_images": has_images,
                "keyword_score": keyword_score,
                "target_keywords": target_keywords,
            },
        )
