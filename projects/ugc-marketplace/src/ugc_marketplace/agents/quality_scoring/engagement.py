"""Engagement scorer agent for quality assessment."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from ugc_marketplace.agents.quality_scoring.base import AgentResult, BaseScoringAgent
from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)


class EngagementScorerAgent(BaseScoringAgent["DimensionScore"]):
    """Agent that scores content engagement potential.

    Analyzes content for factors that drive engagement including
    emotional appeal, shareability, and call-to-action effectiveness.
    """

    def __init__(self) -> None:
        """Initialize the engagement scorer agent."""
        super().__init__()
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    async def score(self, content: str, context: dict[str, Any] | None = None) -> AgentResult["DimensionScore"]:
        """Score content engagement potential.

        Args:
            content: Content to score.
            context: Optional context.

        Returns:
            Agent result with engagement score.
        """
        try:
            score = self._calculate_engagement_score(content)
            return AgentResult(
                success=True,
                data=score,
                reasoning="Engagement score calculated based on content analysis.",
            )
        except Exception as exc:
            logger.error("Engagement scoring failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                reasoning="Failed to calculate engagement score.",
            )

    def _calculate_engagement_score(self, content: str) -> "DimensionScore":
        """Calculate engagement score for content.

        Args:
            content: Content to analyze.

        Returns:
            Dimension score with engagement metrics.
        """
        from ugc_marketplace.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

        word_count = len(content.split())
        has_question = "?" in content
        has_cta = bool(re.search(r"\b(click|subscribe|follow|share|comment|like)\b", content, re.IGNORECASE))
        has_emotion = bool(re.search(r"\b(amazing|incredible|shocking|surprising|exciting)\b", content, re.IGNORECASE))

        score_value = 0.5
        if has_question:
            score_value += 0.15
        if has_cta:
            score_value += 0.15
        if has_emotion:
            score_value += 0.1
        if word_count > 50:
            score_value += 0.1

        score_value = min(score_value, 1.0)

        if score_value >= 0.8:
            level = ScoreLevel.HIGH
        elif score_value >= 0.5:
            level = ScoreLevel.MEDIUM
        else:
            level = ScoreLevel.LOW

        return DimensionScore(
            dimension=ScoreDimension.ENGAGEMENT,
            score=score_value,
            level=level,
            metrics={
                "word_count": word_count,
                "has_question": has_question,
                "has_cta": has_cta,
                "has_emotion": has_emotion,
            },
        )
