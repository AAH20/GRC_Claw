"""Readability scorer agent for quality assessment."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from ugc_marketplace.agents.quality_scoring.base import (AgentResult,
                                                         BaseScoringAgent)
from ugc_marketplace.config import get_settings

logger = logging.getLogger(__name__)


class ReadabilityMetrics(BaseModel):
    """Readability metrics for content."""

    flesch_reading_ease: float = Field(default=0.0, ge=0, le=100)
    flesch_kincaid_grade: float = Field(default=0.0, ge=0, le=20)
    avg_sentence_length: float = Field(default=0.0, ge=0)
    avg_word_length: float = Field(default=0.0, ge=0)
    complex_word_ratio: float = Field(default=0.0, ge=0, le=1)


class ReadabilityScorerAgent(BaseScoringAgent["DimensionScore"]):
    """Agent that scores content readability.

    Analyzes text complexity, sentence structure, and
    overall readability metrics.
    """

    def __init__(self) -> None:
        """Initialize the readability scorer agent."""
        super().__init__()
        self.settings = get_settings()
        self._llm: BaseLanguageModel | None = None

    async def score(
        self, content: str, context: dict[str, Any] | None = None
    ) -> AgentResult[DimensionScore]:
        """Score content readability.

        Args:
            content: Content to score.
            context: Optional context.

        Returns:
            Agent result with readability score.
        """
        try:
            score = self._calculate_readability_score(content)
            return AgentResult(
                success=True,
                data=score,
                reasoning="Readability score calculated based on text analysis.",
            )
        except Exception as exc:
            logger.error("Readability scoring failed", error=str(exc))
            return AgentResult(
                success=False,
                error=str(exc),
                reasoning="Failed to calculate readability score.",
            )

    def _calculate_readability_score(self, content: str) -> DimensionScore:
        """Calculate readability score for content.

        Args:
            content: Content to analyze.

        Returns:
            Dimension score with readability metrics.
        """
        from ugc_marketplace.models.schemas import (DimensionScore,
                                                    ScoreDimension, ScoreLevel)

        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = content.split()

        total_words = len(words)
        total_sentences = len(sentences)
        total_syllables = sum(self._count_syllables(w) for w in words)

        avg_sentence_length = (
            total_words / total_sentences if total_sentences > 0 else 0
        )
        avg_syllables_per_word = total_syllables / total_words if total_words > 0 else 0

        flesch = (
            206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        )
        flesch = max(0, min(100, flesch))

        complex_words = sum(1 for w in words if self._count_syllables(w) > 2)
        complex_ratio = complex_words / total_words if total_words > 0 else 0

        score_value = flesch / 100

        if score_value >= 0.8:
            level = ScoreLevel.HIGH
        elif score_value >= 0.5:
            level = ScoreLevel.MEDIUM
        else:
            level = ScoreLevel.LOW

        return DimensionScore(
            dimension=ScoreDimension.READABILITY,
            score=score_value,
            level=level,
            metrics={
                "flesch_reading_ease": flesch,
                "avg_sentence_length": avg_sentence_length,
                "complex_word_ratio": complex_ratio,
                "total_words": total_words,
                "total_sentences": total_sentences,
            },
        )

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word.

        Args:
            word: Word to analyze.

        Returns:
            Syllable count.
        """
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        if word.endswith("e") and count > 1:
            count -= 1

        return max(1, count)
