"""Readability scoring agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from quality_scoring.agents.base import AgentResult, BaseScoringAgent
from quality_scoring.config.settings import Settings
from quality_scoring.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

logger = logging.getLogger(__name__)


class ReadabilityMetrics(BaseModel):
    """Metrics used for readability scoring."""

    flesch_reading_ease: float = Field(..., ge=0.0, le=100.0)
    flesch_kincaid_grade: float = Field(..., ge=0.0)
    avg_sentence_length: float = Field(..., ge=0.0)
    avg_word_length: float = Field(..., ge=0.0)
    complex_word_ratio: float = Field(..., ge=0.0, le=1.0)
    long_sentence_ratio: float = Field(..., ge=0.0, le=1.0)


class ReadabilityScorerAgent(BaseScoringAgent[DimensionScore]):
    """Agent that scores content readability using linguistic analysis."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the readability scorer agent."""
        super().__init__(llm=llm, settings=settings)

    @property
    def agent_name(self) -> str:
        """Return the agent name."""
        return "ReadabilityScorerAgent"

    @property
    def dimension(self) -> str:
        """Return the scoring dimension."""
        return ScoreDimension.READABILITY.value

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for an English word.

        Args:
            word: The word to count syllables for.

        Returns:
            Estimated syllable count.
        """
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        word = re.sub(r"[^a-z]", "", word)
        if not word:
            return 1

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Silent e adjustment
        if word.endswith("e") and count > 1:
            count -= 1

        return max(1, count)

    def _compute_flesch_reading_ease(self, text: str) -> float:
        """Compute Flesch Reading Ease score.

        Args:
            text: The text to analyze.

        Returns:
            Flesch Reading Ease score (0-100).
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        words = re.findall(r"\b[a-zA-Z]+\b", text)

        if not sentences or not words:
            return 50.0

        total_syllables = sum(self._count_syllables(w) for w in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)

        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0.0, min(100.0, score))

    def _compute_flesch_kincaid_grade(self, text: str) -> float:
        """Compute Flesch-Kincaid Grade Level.

        Args:
            text: The text to analyze.

        Returns:
            Grade level (e.g., 8.0 = 8th grade).
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        words = re.findall(r"\b[a-zA-Z]+\b", text)

        if not sentences or not words:
            return 8.0

        total_syllables = sum(self._count_syllables(w) for w in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)

        # Flesch-Kincaid Grade Level formula
        grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        return max(0.0, grade)

    def _compute_metrics(self, text: str) -> ReadabilityMetrics:
        """Compute all readability metrics.

        Args:
            text: The text to analyze.

        Returns:
            ReadabilityMetrics with all computed values.
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        words = re.findall(r"\b[a-zA-Z]+\b", text)

        if not sentences or not words:
            return ReadabilityMetrics(
                flesch_reading_ease=50.0,
                flesch_kincaid_grade=8.0,
                avg_sentence_length=0.0,
                avg_word_length=0.0,
                complex_word_ratio=0.0,
                long_sentence_ratio=0.0,
            )

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Complex words: 3+ syllables
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        complex_word_ratio = complex_words / len(words)

        # Long sentences: 25+ words
        long_sentences = sum(1 for s in sentences if len(s.split()) >= 25)
        long_sentence_ratio = long_sentences / len(sentences)

        flesch = self._compute_flesch_reading_ease(text)
        fk_grade = self._compute_flesch_kincaid_grade(text)

        return ReadabilityMetrics(
            flesch_reading_ease=flesch,
            flesch_kincaid_grade=fk_grade,
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            complex_word_ratio=complex_word_ratio,
            long_sentence_ratio=long_sentence_ratio,
        )

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
        """Score content readability.

        Args:
            content: The content text to score.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResult containing DimensionScore.
        """
        try:
            metrics = self._compute_metrics(content)

            # Weighted scoring based on Flesch Reading Ease (primary) and other factors
            flesch_score = metrics.flesch_reading_ease

            # Penalize for long sentences and complex words
            sentence_penalty = metrics.long_sentence_ratio * 10
            complexity_penalty = metrics.complex_word_ratio * 15

            final_score = max(0.0, min(100.0, flesch_score - sentence_penalty - complexity_penalty))

            # Confidence based on content length (longer = more reliable)
            word_count = len(content.split())
            confidence = min(1.0, word_count / 200) if word_count > 0 else 0.5

            reasoning_parts = [
                f"Flesch Reading Ease: {metrics.flesch_reading_ease:.1f}",
                f"Flesch-Kincaid Grade: {metrics.flesch_kincaid_grade:.1f}",
                f"Avg sentence length: {metrics.avg_sentence_length:.1f} words",
                f"Complex word ratio: {metrics.complex_word_ratio:.1%}",
            ]

            dimension_score = DimensionScore(
                dimension=ScoreDimension.READABILITY,
                score=round(final_score, 2),
                level=self._score_to_level(final_score),
                confidence=round(confidence, 2),
                reasoning="; ".join(reasoning_parts),
                metrics={
                    "flesch_reading_ease": round(metrics.flesch_reading_ease, 2),
                    "flesch_kincaid_grade": round(metrics.flesch_kincaid_grade, 2),
                    "avg_sentence_length": round(metrics.avg_sentence_length, 2),
                    "avg_word_length": round(metrics.avg_word_length, 2),
                    "complex_word_ratio": round(metrics.complex_word_ratio, 4),
                    "long_sentence_ratio": round(metrics.long_sentence_ratio, 4),
                },
            )

            return AgentResult(success=True, data=dimension_score)

        except Exception as exc:
            logger.exception("Readability scoring failed")
            return AgentResult(success=False, error=str(exc))
