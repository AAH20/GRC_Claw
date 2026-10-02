"""Quality scoring system for model responses.

Provides multi-dimensional quality assessment of AI model outputs
including correctness, relevance, coherence, and safety metrics.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Quality assessment dimensions."""

    CORRECTNESS = "correctness"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    SAFETY = "safety"
    HELPFULNESS = "helpfulness"
    CONCISENESS = "conciseness"


@dataclass
class QualityScore:
    """Quality score for a model response.

    Attributes:
        overall: Overall quality score (0.0-1.0).
        dimensions: Per-dimension scores.
        feedback: Human-readable feedback.
        timestamp: When the score was computed.
        metadata: Additional scoring metadata.
    """

    overall: float
    dimensions: Dict[QualityDimension, float]
    feedback: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if the quality score meets a threshold.

        Args:
            threshold: Minimum acceptable overall score.

        Returns:
            True if the overall score meets the threshold.
        """
        return self.overall >= threshold

    def get_weakest_dimension(self) -> Tuple[QualityDimension, float]:
        """Get the weakest quality dimension.

        Returns:
            Tuple of (dimension, score) for the lowest-scoring dimension.
        """
        return min(self.dimensions.items(), key=lambda x: x[1])

    def get_strongest_dimension(self) -> Tuple[QualityDimension, float]:
        """Get the strongest quality dimension.

        Returns:
            Tuple of (dimension, score) for the highest-scoring dimension.
        """
        return max(self.dimensions.items(), key=lambda x: x[1])


@dataclass
class QualityConfig:
    """Configuration for quality scoring.

    Attributes:
        dimension_weights: Weights for each quality dimension.
        min_acceptable_score: Minimum acceptable overall score.
        enable_safety_check: Whether to run safety checks.
        custom_rules: List of custom scoring rules.
    """

    dimension_weights: Dict[QualityDimension, float] = field(default_factory=lambda: {
        QualityDimension.CORRECTNESS: 0.25,
        QualityDimension.RELEVANCE: 0.20,
        QualityDimension.COHERENCE: 0.15,
        QualityDimension.COMPLETENESS: 0.15,
        QualityDimension.SAFETY: 0.15,
        QualityDimension.HELPFULNESS: 0.05,
        QualityDimension.CONCISENESS: 0.05,
    })
    min_acceptable_score: float = 0.7
    enable_safety_check: bool = True
    custom_rules: List[Callable[[str, str], float]] = field(default_factory=list)


class QualityScorer:
    """Multi-dimensional quality scorer for model responses.

    Evaluates responses across multiple quality dimensions and
    provides an overall quality score with detailed feedback.

    Example:
        >>> scorer = QualityScorer()
        >>> score = scorer.score(
        ...     prompt="What is machine learning?",
        ...     response="Machine learning is a subset of AI...",
        ... )
        >>> print(f"Quality: {score.overall:.2f}")
    """

    # Patterns that may indicate quality issues
    HALLUCINATION_PATTERNS = [
        r"I cannot (?:be sure|certain|verify)",
        r"As an AI (?:language model|assistant)",
        r"I don't have (?:access to|real-time)",
        r"My (?:knowledge|training) (?:cutoff|data)",
    ]

    SAFETY_PATTERNS = [
        r"(?:ignore|disregard) (?:all|previous|above) (?:instructions|prompts)",
        r"system\s*prompt",
        r"you are now",
        r"new (?:persona|mode|character)",
    ]

    def __init__(self, config: Optional[QualityConfig] = None) -> None:
        """Initialize the quality scorer.

        Args:
            config: Quality scoring configuration.
        """
        self._config = config or QualityConfig()
        self._scoring_history: List[QualityScore] = []

    @property
    def config(self) -> QualityConfig:
        """Get the quality configuration.

        Returns:
            The quality configuration.
        """
        return self._config

    def score(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> QualityScore:
        """Score a model response.

        Args:
            prompt: The original prompt.
            response: The model response to score.
            context: Optional conversation context.
            reference: Optional reference answer for comparison.

        Returns:
            QualityScore with detailed dimension scores.
        """
        dimensions: Dict[QualityDimension, float] = {}

        dimensions[QualityDimension.CORRECTNESS] = self._score_correctness(
            response, reference
        )
        dimensions[QualityDimension.RELEVANCE] = self._score_relevance(
            prompt, response
        )
        dimensions[QualityDimension.COHERENCE] = self._score_coherence(response)
        dimensions[QualityDimension.COMPLETENESS] = self._score_completeness(
            prompt, response
        )
        dimensions[QualityDimension.SAFETY] = self._score_safety(response)
        dimensions[QualityDimension.HELPFULNESS] = self._score_helpfulness(
            prompt, response
        )
        dimensions[QualityDimension.CONCISENESS] = self._score_conciseness(response)

        # Apply custom rules
        for rule in self._config.custom_rules:
            try:
                custom_score = rule(prompt, response)
                # Blend custom score into correctness
                dimensions[QualityDimension.CORRECTNESS] = (
                    dimensions[QualityDimension.CORRECTNESS] * 0.8 + custom_score * 0.2
                )
            except Exception as exc:
                logger.warning("Custom scoring rule failed: %s", exc)

        # Calculate weighted overall score
        overall = sum(
            dimensions[dim] * self._config.dimension_weights.get(dim, 0.0)
            for dim in dimensions
        )

        # Normalize if weights don't sum to 1.0
        total_weight = sum(self._config.dimension_weights.values())
        if total_weight > 0:
            overall /= total_weight

        overall = max(0.0, min(1.0, overall))

        feedback = self._generate_feedback(dimensions, overall)

        score = QualityScore(
            overall=overall,
            dimensions=dimensions,
            feedback=feedback,
            timestamp=__import__("time").time(),
            metadata={
                "prompt_length": len(prompt),
                "response_length": len(response),
                "has_reference": reference is not None,
            },
        )

        self._scoring_history.append(score)
        return score

    def get_average_score(self, last_n: Optional[int] = None) -> float:
        """Get average quality score.

        Args:
            last_n: Number of recent scores to average. All if None.

        Returns:
            Average overall quality score.
        """
        if not self._scoring_history:
            return 0.0

        scores = self._scoring_history[-last_n:] if last_n else self._scoring_history
        return sum(s.overall for s in scores) / len(scores)

    def get_score_trend(self, window_size: int = 10) -> List[float]:
        """Get quality score trend.

        Args:
            window_size: Number of recent scores to include.

        Returns:
            List of recent overall scores.
        """
        recent = self._scoring_history[-window_size:]
        return [s.overall for s in recent]

    def _score_correctness(self, response: str, reference: Optional[str]) -> float:
        """Score factual correctness.

        Args:
            response: The model response.
            reference: Optional reference answer.

        Returns:
            Correctness score (0.0-1.0).
        """
        score = 0.8  # Base score

        # Check for hallucination indicators
        for pattern in self.HALLUCINATION_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                score -= 0.15

        # If reference available, do simple overlap check
        if reference:
            response_words = set(response.lower().split())
            reference_words = set(reference.lower().split())
            if reference_words:
                overlap = len(response_words & reference_words) / len(reference_words)
                score = score * 0.5 + overlap * 0.5

        return max(0.0, min(1.0, score))

    def _score_relevance(self, prompt: str, response: str) -> float:
        """Score relevance to the prompt.

        Args:
            prompt: The original prompt.
            response: The model response.

        Returns:
            Relevance score (0.0-1.0).
        """
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())

        if not prompt_words:
            return 0.5

        # Jaccard similarity
        intersection = len(prompt_words & response_words)
        union = len(prompt_words | response_words)
        jaccard = intersection / union if union > 0 else 0.0

        # Boost for longer responses that cover more prompt terms
        coverage = intersection / len(prompt_words) if prompt_words else 0.0

        return min(1.0, jaccard * 0.4 + coverage * 0.6)

    def _score_coherence(self, response: str) -> float:
        """Score response coherence.

        Args:
            response: The model response.

        Returns:
            Coherence score (0.0-1.0).
        """
        score = 0.9

        # Check for repetition
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) > 1:
            unique_sentences = set(sentences)
            repetition_ratio = 1.0 - (len(unique_sentences) / len(sentences))
            score -= repetition_ratio * 0.3

        # Check for very short responses (likely incoherent)
        if len(response) < 20:
            score -= 0.3

        # Check for excessive formatting issues
        if response.count('\n') > len(sentences) * 2:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _score_completeness(self, prompt: str, response: str) -> float:
        """Score response completeness.

        Args:
            prompt: The original prompt.
            response: The model response.

        Returns:
            Completeness score (0.0-1.0).
        """
        # Check if response addresses the prompt type
        prompt_lower = prompt.lower()
        response_lower = response.lower()

        score = 0.7

        # Question prompts should have answers
        if "?" in prompt:
            # Check for answer indicators
            answer_indicators = ["is", "are", "was", "were", "can", "will", "because"]
            if any(ind in response_lower for ind in answer_indicators):
                score += 0.15

        # Command prompts should have actionable content
        command_indicators = ["create", "write", "generate", "list", "explain"]
        if any(prompt_lower.startswith(cmd) for cmd in command_indicators):
            if len(response) > 100:
                score += 0.15

        # Length adequacy
        prompt_words = len(prompt.split())
        response_words = len(response.split())
        if response_words >= prompt_words * 0.5:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_safety(self, response: str) -> float:
        """Score response safety.

        Args:
            response: The model response.

        Returns:
            Safety score (0.0-1.0).
        """
        if not self._config.enable_safety_check:
            return 1.0

        score = 1.0

        for pattern in self.SAFETY_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                score -= 0.3

        # Check for potential PII
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]
        for pattern in pii_patterns:
            if re.search(pattern, response):
                score -= 0.2

        return max(0.0, min(1.0, score))

    def _score_helpfulness(self, prompt: str, response: str) -> float:
        """Score response helpfulness.

        Args:
            prompt: The original prompt.
            response: The model response.

        Returns:
            Helpfulness score (0.0-1.0).
        """
        score = 0.7

        # Check for actionable content
        actionable_patterns = [
            r'\b(?:step|first|second|third|finally)\b',
            r'\b(?:recommend|suggest|advise|propose)\b',
            r'\b(?:example|for instance|such as)\b',
        ]
        for pattern in actionable_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                score += 0.1

        # Penalize overly vague responses
        vague_patterns = [
            r'\b(?:it depends|varies|many factors|complex)\b',
        ]
        for pattern in vague_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                score -= 0.1

        return max(0.0, min(1.0, score))

    def _score_conciseness(self, response: str) -> float:
        """Score response conciseness.

        Args:
            response: The model response.

        Returns:
            Conciseness score (0.0-1.0).
        """
        words = len(response.split())

        # Ideal range: 50-300 words
        if 50 <= words <= 300:
            return 0.9
        elif words < 20:
            return 0.4  # Too short
        elif words <= 50:
            return 0.7
        elif words <= 500:
            return 0.8
        else:
            return 0.6  # Too long

    def _generate_feedback(
        self,
        dimensions: Dict[QualityDimension, float],
        overall: float,
    ) -> str:
        """Generate human-readable feedback.

        Args:
            dimensions: Per-dimension scores.
            overall: Overall score.

        Returns:
            Feedback string.
        """
        weakest_dim, weakest_score = min(dimensions.items(), key=lambda x: x[1])
        strongest_dim, strongest_score = max(dimensions.items(), key=lambda x: x[1])

        if overall >= 0.9:
            return f"Excellent quality. Strongest: {strongest_dim.value}."
        elif overall >= 0.7:
            return (
                f"Good quality. Consider improving {weakest_dim.value} "
                f"(score: {weakest_score:.2f})."
            )
        elif overall >= 0.5:
            return (
                f"Acceptable quality. {weakest_dim.value} needs attention "
                f"(score: {weakest_score:.2f})."
            )
        else:
            return (
                f"Low quality. Significant improvement needed in "
                f"{weakest_dim.value} (score: {weakest_score:.2f})."
            )
