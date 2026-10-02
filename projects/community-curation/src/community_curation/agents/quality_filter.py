"""Quality filtering agent implementation."""

from __future__ import annotations

import structlog
from typing import Any

from community_curation.agents.base import BaseCurationAgent
from community_curation.config.settings import get_settings
from community_curation.models import ContentItem, QualityAssessment

logger = structlog.get_logger(__name__)


class QualityFilterAgent(BaseCurationAgent[list[ContentItem], list[QualityAssessment]]):
    """Agent that filters content based on quality signals and spam detection."""

    def __init__(self) -> None:
        """Initialize the quality filter agent."""
        super().__init__(
            name="QualityFilterAgent",
            description="Filters low-quality and spam content from community submissions",
        )
        self.settings = get_settings()

    def _detect_spam(self, item: ContentItem) -> tuple[bool, list[str]]:
        """Detect if content is spam.

        Args:
            item: Content item to check.

        Returns:
            Tuple of (is_spam, flags).
        """
        flags: list[str] = []

        # Check for excessive capitalization
        if item.title:
            upper_ratio = sum(1 for c in item.title if c.isupper()) / max(len(item.title), 1)
            if upper_ratio > 0.7:
                flags.append("excessive_capitalization")

        # Check for repetitive characters
        if any(c * 4 in item.title for c in "abcdefghijklmnopqrstuvwxyz"):
            flags.append("repetitive_characters")

        # Check for suspicious metadata
        metadata = item.metadata
        if metadata.get("is_spam", False):
            flags.append("platform_spam_flag")
        if metadata.get("deleted", False):
            flags.append("deleted_content")
        if metadata.get("removed", False):
            flags.append("removed_content")

        # Check URL patterns
        if item.url:
            suspicious_patterns = ["bit.ly", "tinyurl", "spam", "click here"]
            if any(pattern in item.url.lower() for pattern in suspicious_patterns):
                flags.append("suspicious_url")

        # Very short content with high engagement (possible spam)
        if len(item.body) < 10 and item.score > 100:
            flags.append("suspicious_engagement_pattern")

        return len(flags) > 0, flags

    def _assess_quality(self, item: ContentItem) -> tuple[float, list[str]]:
        """Assess content quality.

        Args:
            item: Content item to assess.

        Returns:
            Tuple of (quality_score, reasons).
        """
        score = 1.0
        reasons: list[str] = []

        # Length-based quality
        body_length = len(item.body)
        if body_length < 20:
            score -= 0.3
            reasons.append("very_short_content")
        elif body_length < 50:
            score -= 0.1
            reasons.append("short_content")
        elif body_length > 200:
            score += 0.1
            reasons.append("detailed_content")

        # Engagement quality
        if item.score < 0:
            score -= 0.2
            reasons.append("negative_score")

        # Comment-to-score ratio (healthy discussion indicator)
        if item.score > 0:
            ratio = item.comment_count / item.score
            if ratio > 0.5:
                score += 0.1
                reasons.append("healthy_discussion")
            elif ratio < 0.01 and item.score > 50:
                score -= 0.1
                reasons.append("low_engagement_ratio")

        # Metadata quality signals
        metadata = item.metadata
        if metadata.get("verified_author", False):
            score += 0.1
            reasons.append("verified_author")
        if metadata.get("award_count", 0) > 0:
            score += 0.1
            reasons.append("community_awarded")

        # Source reliability
        if item.source in ("reddit", "hacker_news"):
            score += 0.05
            reasons.append("reliable_source")

        return max(0.0, min(1.0, score)), reasons

    async def run(self, input_data: list[ContentItem]) -> list[QualityAssessment]:
        """Filter content by quality.

        Args:
            input_data: List of content items to filter.

        Returns:
            List of quality assessments.
        """
        if not self.is_available:
            logger.warning("agent_unavailable", agent=self.name)
            return self._fallback_filter(input_data)

        threshold = self.settings.quality_threshold
        assessments: list[QualityAssessment] = []

        for item in input_data:
            is_spam, spam_flags = self._detect_spam(item)
            quality_score, quality_reasons = self._assess_quality(item)

            all_flags = spam_flags + quality_reasons
            is_low_quality = quality_score < threshold

            if is_spam:
                quality_score = 0.0

            assessments.append(
                QualityAssessment(
                    content_id=item.id,
                    quality_score=round(quality_score, 4),
                    is_spam=is_spam,
                    is_low_quality=is_low_quality,
                    flags=all_flags,
                    reasons=quality_reasons,
                )
            )

        logger.info(
            "quality_filtered",
            total=len(assessments),
            spam_count=sum(1 for a in assessments if a.is_spam),
            low_quality_count=sum(1 for a in assessments if a.is_low_quality),
        )
        return assessments

    def _fallback_filter(self, items: list[ContentItem]) -> list[QualityAssessment]:
        """Fallback quality filtering when agent is unavailable.

        Args:
            items: Content items to filter.

        Returns:
            List of quality assessments.
        """
        assessments = []
        for item in items:
            is_spam, flags = self._detect_spam(item)
            score = 0.5 if not is_spam else 0.0
            assessments.append(
                QualityAssessment(
                    content_id=item.id,
                    quality_score=score,
                    is_spam=is_spam,
                    is_low_quality=score < 0.5,
                    flags=flags,
                    reasons=["fallback_filtering"],
                )
            )
        return assessments
