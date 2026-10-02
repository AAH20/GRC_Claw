"""Originality scoring agent using LangChain DeepAgents."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from quality_scoring.agents.base import AgentResult, BaseScoringAgent
from quality_scoring.config.settings import Settings
from quality_scoring.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

logger = logging.getLogger(__name__)


class OriginalityScorerAgent(BaseScoringAgent[DimensionScore]):
    """Agent that scores content originality using text analysis and LLM evaluation."""

    # Common phrases that reduce originality
    CLICHE_PATTERNS = [
        r"\b(at the end of the day)\b",
        r"\b(in today's world)\b",
        r"\b(when all is said and done)\b",
        r"\b(the fact of the matter is)\b",
        r"\b(it goes without saying)\b",
        r"\b(first and foremost)\b",
        r"\b(last but not least)\b",
        r"\b(in this day and age)\b",
        r"\b(think outside the box)\b",
        r"\b(game changer)\b",
        r"\b(cutting edge)\b",
        r"\b(best kept secret)\b",
        r"\b(little known fact)\b",
        r"\b(it is what it is)\b",
    ]

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the originality scorer agent."""
        super().__init__(llm=llm, settings=settings)

    @property
    def agent_name(self) -> str:
        """Return the agent name."""
        return "OriginalityScorerAgent"

    @property
    def dimension(self) -> str:
        """Return the scoring dimension."""
        return ScoreDimension.ORIGINALITY.value

    def _compute_lexical_diversity(self, text: str) -> float:
        """Compute type-token ratio (lexical diversity).

        Args:
            text: The text to analyze.

        Returns:
            Lexical diversity score (0-1).
        """
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return 0.0

        unique_words = set(words)
        return len(unique_words) / len(words)

    def _count_cliches(self, text: str) -> int:
        """Count cliché phrases in the text.

        Args:
            text: The text to analyze.

        Returns:
            Number of cliché phrases found.
        """
        text_lower = text.lower()
        count = 0
        for pattern in self.CLICHE_PATTERNS:
            count += len(re.findall(pattern, text_lower))
        return count

    def _compute_sentence_variety(self, text: str) -> float:
        """Compute sentence structure variety.

        Args:
            text: The text to analyze.

        Returns:
            Sentence variety score (0-1).
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(sentences) <= 1:
            return 0.5

        # Analyze sentence starters
        starters = []
        for sentence in sentences:
            words = sentence.split()
            if words:
                starters.append(words[0].lower())

        unique_starters = len(set(starters))
        return min(1.0, unique_starters / len(sentences))

    def _compute_content_hash(self, text: str) -> str:
        """Compute a hash of normalized content for deduplication.

        Args:
            text: The text to hash.

        Returns:
            SHA-256 hash of normalized content.
        """
        normalized = re.sub(r"\s+", " ", text.lower().strip())
        return hashlib.sha256(normalized.encode()).hexdigest()

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
        """Score content originality.

        Args:
            content: The content text to score.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResult containing DimensionScore.
        """
        try:
            lexical_diversity = self._compute_lexical_diversity(content)
            cliche_count = self._count_cliches(content)
            sentence_variety = self._compute_sentence_variety(content)

            # Base score from lexical diversity (0-100)
            diversity_score = lexical_diversity * 100

            # Cliché penalty
            cliche_penalty = min(30, cliche_count * 5)

            # Sentence variety bonus/penalty
            variety_score = sentence_variety * 100

            # Weighted combination
            final_score = (
                diversity_score * 0.4
                + variety_score * 0.3
                + (100 - cliche_penalty) * 0.3
            )
            final_score = max(0.0, min(100.0, final_score))

            # Confidence based on content length
            word_count = len(content.split())
            confidence = min(1.0, word_count / 150) if word_count > 0 else 0.5

            reasoning_parts = [
                f"Lexical diversity: {lexical_diversity:.1%}",
                f"Clichés found: {cliche_count}",
                f"Sentence variety: {sentence_variety:.1%}",
            ]

            dimension_score = DimensionScore(
                dimension=ScoreDimension.ORIGINALITY,
                score=round(final_score, 2),
                level=self._score_to_level(final_score),
                confidence=round(confidence, 2),
                reasoning="; ".join(reasoning_parts),
                metrics={
                    "lexical_diversity": round(lexical_diversity, 4),
                    "cliche_count": cliche_count,
                    "sentence_variety": round(sentence_variety, 4),
                    "content_hash": self._compute_content_hash(content)[:16],
                },
            )

            return AgentResult(success=True, data=dimension_score)

        except Exception as exc:
            logger.exception("Originality scoring failed")
            return AgentResult(success=False, error=str(exc))
