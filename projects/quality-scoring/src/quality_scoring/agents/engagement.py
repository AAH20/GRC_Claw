"""Engagement scoring agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from quality_scoring.agents.base import AgentResult, BaseScoringAgent
from quality_scoring.config.settings import Settings
from quality_scoring.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

logger = logging.getLogger(__name__)


class EngagementScorerAgent(BaseScoringAgent[DimensionScore]):
    """Agent that scores content engagement using linguistic and structural analysis."""

    # Engagement indicators
    QUESTION_PATTERN = (
        r"\b(what|why|how|when|where|who|which|can|could|would|should|is|are|do|does|did)\b[^.!?]*\?"
    )
    POWER_WORDS = [
        "you", "your", "free", "new", "now", "today", "instantly",
        "exclusive", "proven", "guaranteed", "discover", "unlock",
        "secret", "breakthrough", "revolutionary", "ultimate",
    ]
    EMOTIONAL_TRIGGERS = [
        "amazing", "incredible", "shocking", "surprising", "stunning",
        "remarkable", "extraordinary", "unbelievable", "astonishing",
        "devastating", "thrilling", "heartwarming", "inspiring",
    ]

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the engagement scorer agent."""
        super().__init__(llm=llm, settings=settings)

    @property
    def agent_name(self) -> str:
        """Return the agent name."""
        return "EngagementScorerAgent"

    @property
    def dimension(self) -> str:
        """Return the scoring dimension."""
        return ScoreDimension.ENGAGEMENT.value

    def _count_questions(self, text: str) -> int:
        """Count questions in the text.

        Args:
            text: The text to analyze.

        Returns:
            Number of questions found.
        """
        return len(re.findall(self.QUESTION_PATTERN, text, re.IGNORECASE))

    def _count_power_words(self, text: str) -> int:
        """Count power words in the text.

        Args:
            text: The text to analyze.

        Returns:
            Number of power words found.
        """
        text_lower = text.lower()
        count = 0
        for word in self.POWER_WORDS:
            count += len(re.findall(rf"\b{word}\b", text_lower))
        return count

    def _count_emotional_triggers(self, text: str) -> int:
        """Count emotional trigger words.

        Args:
            text: The text to analyze.

        Returns:
            Number of emotional triggers found.
        """
        text_lower = text.lower()
        count = 0
        for word in self.EMOTIONAL_TRIGGERS:
            count += len(re.findall(rf"\b{word}\b", text_lower))
        return count

    def _compute_cta_presence(self, text: str) -> float:
        """Check for call-to-action presence.

        Args:
            text: The text to analyze.

        Returns:
            CTA score (0-1).
        """
        cta_patterns = [
            r"\b(click here|sign up|subscribe|join|try|start|get|download|register)\b",
            r"\b(learn more|read more|find out|discover|explore)\b",
            r"\b(call now|contact us|reach out|get in touch)\b",
        ]
        text_lower = text.lower()
        matches = sum(
            len(re.findall(pattern, text_lower)) for pattern in cta_patterns
        )
        return min(1.0, matches / 3)

    def _compute_structural_engagement(self, text: str) -> float:
        """Compute structural engagement factors.

        Args:
            text: The text to analyze.

        Returns:
            Structural engagement score (0-1).
        """
        score = 0.0

        # Paragraphs (shorter paragraphs = more engaging)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if paragraphs:
            avg_para_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if avg_para_length <= 50:
                score += 0.3
            elif avg_para_length <= 100:
                score += 0.15

        # Lists (bullet points / numbered lists)
        list_items = len(re.findall(r"^\s*[-•*]\s", text, re.MULTILINE))
        numbered_items = len(re.findall(r"^\s*\d+\.\s", text, re.MULTILINE))
        if list_items + numbered_items >= 3:
            score += 0.3
        elif list_items + numbered_items >= 1:
            score += 0.15

        # Headers
        headers = len(re.findall(r"^#{1,6}\s", text, re.MULTILINE))
        if headers >= 2:
            score += 0.2
        elif headers >= 1:
            score += 0.1

        # Bold/emphasis
        emphasis = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", text))
        if emphasis >= 2:
            score += 0.2
        elif emphasis >= 1:
            score += 0.1

        return min(1.0, score)

    def _score_to_level(self, score: float) -> ScoreLevel:
        """Convert numeric score to qualitative level.

        Args:
            score: Numeric score (0-100).

        Returns:
            Qualitative score level.
        """
        if score >= 80:
            return ScoreLevel.EXCELLENT
        if score >= 60:
            return ScoreLevel.GOOD
        if score >= 40:
            return ScoreLevel.AVERAGE
        if score >= 20:
            return ScoreLevel.BELOW_AVERAGE
        return ScoreLevel.POOR

    async def score(self, content: str, **kwargs: Any) -> AgentResult[DimensionScore]:
        """Score content engagement.

        Args:
            content: The content text to score.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResult containing DimensionScore.
        """
        try:
            word_count = len(content.split())
            if word_count == 0:
                return AgentResult(
                    success=False,
                    error="Cannot score empty content",
                )

            questions = self._count_questions(content)
            power_words = self._count_power_words(content)
            emotional_triggers = self._count_emotional_triggers(content)
            cta_score = self._compute_cta_presence(content)
            structural_score = self._compute_structural_engagement(content)

            # Normalize metrics per 100 words
            questions_per_100 = (questions / word_count) * 100
            power_per_100 = (power_words / word_count) * 100
            emotional_per_100 = (emotional_triggers / word_count) * 100

            # Weighted scoring
            question_score = min(100, questions_per_100 * 10)
            power_score = min(100, power_per_100 * 5)
            emotional_score = min(100, emotional_per_100 * 8)
            cta_normalized = cta_score * 100
            structural_normalized = structural_score * 100

            final_score = (
                question_score * 0.2
                + power_score * 0.2
                + emotional_score * 0.15
                + cta_normalized * 0.2
                + structural_normalized * 0.25
            )
            final_score = max(0.0, min(100.0, final_score))

            # Confidence based on content length
            confidence = min(1.0, word_count / 200) if word_count > 0 else 0.5

            reasoning_parts = [
                f"Questions: {questions}",
                f"Power words: {power_words}",
                f"Emotional triggers: {emotional_triggers}",
                f"CTA presence: {cta_score:.1%}",
                f"Structural engagement: {structural_score:.1%}",
            ]

            dimension_score = DimensionScore(
                dimension=ScoreDimension.ENGAGEMENT,
                score=round(final_score, 2),
                level=self._score_to_level(final_score),
                confidence=round(confidence, 2),
                reasoning="; ".join(reasoning_parts),
                metrics={
                    "question_count": questions,
                    "power_word_count": power_words,
                    "emotional_trigger_count": emotional_triggers,
                    "cta_score": round(cta_score, 4),
                    "structural_score": round(structural_score, 4),
                },
            )

            return AgentResult(success=True, data=dimension_score)

        except Exception as exc:
            logger.exception("Engagement scoring failed")
            return AgentResult(success=False, error=str(exc))
