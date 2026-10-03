"""Originality scorer agent for quality assessment."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from ugc_marketplace.agents.quality_scoring.base import AgentResult, BaseScoringAgent
from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)


class OriginalityScorerAgent(BaseScoringAgent["DimensionScore"]):
    """Agent that scores content originality.

    Analyzes content for uniqueness, creativity, and
    originality indicators.
    """

    def __init__(self) -> None:
        """Initialize the originality scorer agent."""
        super().__init__()
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    async def score(self, content: str, context: dict[str, Any] | None = None) -> AgentResult["DimensionScore"]:
        """Score content originality.

        Args:
            content: Content to score.
            context: Optional context.

        Returns:
            Agent result with originality score.
        """
        try:
            score = self._calculate_originality_score(content)
            return AgentResult(
                success=True,
                data=score,
                reasoning="Originality score calculated based on content analysis.",
            )
        except Exception as exc:
            logger.error("Originality scoring failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                reasoning="Failed to calculate originality score.",
            )

    def _calculate_originality_score(self, content: str) -> "DimensionScore":
        """Calculate originality score for content.

        Args:
            content: Content to analyze.

        Returns:
            Dimension score with originality metrics.
        """
        from ugc_marketplace.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

        content_hash = hashlib.md5(content.encode()).hexdigest()
        unique_words = set(content.lower().split())
        total_words = len(content.split())
        uniqueness_ratio = len(unique_words) / total_words if total_words > 0 else 0

        has_perspective = bool(re.search(r"\b(I think|in my opinion|my perspective|I believe)\b", content, re.IGNORECASE))
        has_examples = bool(re.search(r"\b(for example|for instance|such as)\b", content, re.IGNORECASE))
        has_data = bool(re.search(r"\b(\d+%|\d+ percent|study|research|data)\b", content, re.IGNORECASE))

        score_value = uniqueness_ratio * 0.5
        if has_perspective:
            score_value += 0.2
        if has_examples:
            score_value += 0.15
        if has_data:
            score_value += 0.15

        score_value = min(score_value, 1.0)

        if score_value >= 0.8:
            level = ScoreLevel.HIGH
        elif score_value >= 0.5:
            level = ScoreLevel.MEDIUM
        else:
            level = ScoreLevel.LOW

        return DimensionScore(
            dimension=ScoreDimension.ORIGINALITY,
            score=score_value,
            level=level,
            metrics={
                "content_hash": content_hash,
                "uniqueness_ratio": uniqueness_ratio,
                "has_perspective": has_perspective,
                "has_examples": has_examples,
                "has_data": has_data,
            },
        )
