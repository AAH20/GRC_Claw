"""Improvement suggester agent for quality assessment."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from ugc_marketplace.agents.quality_scoring.base import (AgentResult,
                                                         BaseScoringAgent)
from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)


class ImprovementSuggesterAgent(BaseScoringAgent["ImprovementPlan"]):
    """Agent that suggests content improvements.

    Analyzes content quality and provides actionable
    suggestions for improvement.
    """

    def __init__(self) -> None:
        """Initialize the improvement suggester agent."""
        super().__init__()
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    async def score(
        self, content: str, context: dict[str, Any] | None = None
    ) -> AgentResult[ImprovementPlan]:
        """Generate improvement suggestions for content.

        Args:
            content: Content to analyze.
            context: Optional context.

        Returns:
            Agent result with improvement plan.
        """
        try:
            plan = self._generate_improvements(content)
            return AgentResult(
                success=True,
                data=plan,
                reasoning="Improvement suggestions generated based on content analysis.",
            )
        except Exception as exc:
            logger.error("Improvement suggestion failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                reasoning="Failed to generate improvement suggestions.",
            )

    def _generate_improvements(self, content: str) -> ImprovementPlan:
        """Generate improvement suggestions.

        Args:
            content: Content to analyze.

        Returns:
            Improvement plan with suggestions.
        """
        from ugc_marketplace.models.schemas import (ImprovementPlan,
                                                    ImprovementSuggestion)

        suggestions: list[ImprovementSuggestion] = []

        word_count = len(content.split())
        if word_count < 100:
            suggestions.append(
                ImprovementSuggestion(
                    id=uuid.uuid4(),
                    category="length",
                    title="Increase Content Length",
                    description="Content is relatively short. Consider expanding with more detail and examples.",
                    priority="medium",
                )
            )

        if "?" not in content:
            suggestions.append(
                ImprovementSuggestion(
                    id=uuid.uuid4(),
                    category="engagement",
                    title="Add Questions",
                    description="Including questions can boost engagement and encourage comments.",
                    priority="high",
                )
            )

        if not any(word in content.lower() for word in ["you", "your"]):
            suggestions.append(
                ImprovementSuggestion(
                    id=uuid.uuid4(),
                    category="tone",
                    title="Use Second Person",
                    description="Using 'you' and 'your' can make content more relatable and engaging.",
                    priority="medium",
                )
            )

        return ImprovementPlan(
            id=uuid.uuid4(),
            suggestions=suggestions,
            overall_score=0.6,
        )
