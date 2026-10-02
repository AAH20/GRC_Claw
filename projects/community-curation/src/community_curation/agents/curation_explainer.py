"""Curation explanation agent implementation."""

from __future__ import annotations

import structlog
from typing import Any

from community_curation.agents.base import BaseCurationAgent
from community_curation.models import CurationResult, RankedContent, Trend, TopicCluster, QualityAssessment

logger = structlog.get_logger(__name__)


class CurationExplainerAgent(
    BaseCurationAgent[
        tuple[list[RankedContent], list[Trend], list[TopicCluster], list[QualityAssessment]],
        str,
    ]
):
    """Agent that generates human-readable explanations for curation decisions."""

    def __init__(self) -> None:
        """Initialize the curation explainer agent."""
        super().__init__(
            name="CurationExplainerAgent",
            description="Generates human-readable explanations for content curation decisions",
        )

    async def run(
        self,
        input_data: tuple[list[RankedContent], list[Trend], list[TopicCluster], list[QualityAssessment]],
    ) -> str:
        """Generate explanation for curation results.

        Args:
            input_data: Tuple of (ranked_content, trends, clusters, quality_assessments).

        Returns:
            Human-readable explanation string.
        """
        ranked_content, trends, clusters, quality_assessments = input_data

        if not self.is_available:
            logger.warning("agent_unavailable", agent=self.name)
            return self._fallback_explanation(ranked_content, trends, clusters, quality_assessments)

        sections: list[str] = []

        # Overview
        total_items = len(ranked_content)
        spam_count = sum(1 for q in quality_assessments if q.is_spam)
        low_quality_count = sum(1 for q in quality_assessments if q.is_low_quality)
        filtered_count = spam_count + low_quality_count

        sections.append(
            f"Curation Analysis: {total_items} items processed, "
            f"{filtered_count} filtered ({spam_count} spam, {low_quality_count} low quality), "
            f"{total_items - filtered_count} items curated."
        )

        # Top content
        if ranked_content:
            top_items = ranked_content[:3]
            top_desc = ", ".join(
                f"#{item.rank} '{item.content.title[:50]}...' (score: {item.ranking_score:.2f})"
                for item in top_items
            )
            sections.append(f"Top ranked content: {top_desc}")

        # Trends
        if trends:
            trend_names = ", ".join(trend.name for trend in trends[:5])
            sections.append(f"Detected trends: {trend_names}")

            # Highlight fastest growing trend
            if trends:
                fastest = max(trends, key=lambda t: t.velocity)
                sections.append(
                    f"Fastest growing trend: '{fastest.name}' with velocity {fastest.velocity:.2f} items/hour"
                )

        # Clusters
        if clusters:
            cluster_names = ", ".join(cluster.name for cluster in clusters[:5])
            sections.append(f"Topic clusters: {cluster_names}")

            # Most coherent cluster
            most_coherent = max(clusters, key=lambda c: c.coherence_score)
            sections.append(
                f"Most coherent cluster: '{most_coherent.name}' "
                f"(coherence: {most_coherent.coherence_score:.2f}, size: {most_coherent.size})"
            )

        # Quality insights
        if quality_assessments:
            avg_quality = sum(q.quality_score for q in quality_assessments) / len(quality_assessments)
            sections.append(f"Average quality score: {avg_quality:.2f}")

            # Most common flags
            all_flags: list[str] = []
            for q in quality_assessments:
                all_flags.extend(q.flags)
            if all_flags:
                from collections import Counter
                common_flags = Counter(all_flags).most_common(3)
                flag_desc = ", ".join(f"{flag} ({count})" for flag, count in common_flags)
                sections.append(f"Common quality flags: {flag_desc}")

        explanation = "\n\n".join(sections)
        logger.info("explanation_generated", length=len(explanation))
        return explanation

    def _fallback_explanation(
        self,
        ranked_content: list[RankedContent],
        trends: list[Trend],
        clusters: list[TopicCluster],
        quality_assessments: list[QualityAssessment],
    ) -> str:
        """Generate fallback explanation when agent is unavailable.

        Args:
            ranked_content: Ranked content items.
            trends: Detected trends.
            clusters: Topic clusters.
            quality_assessments: Quality assessments.

        Returns:
            Fallback explanation string.
        """
        parts = [
            f"Curation complete: {len(ranked_content)} items ranked, "
            f"{len(trends)} trends detected, {len(clusters)} clusters formed, "
            f"{len(quality_assessments)} quality assessments.",
        ]
        if ranked_content:
            parts.append(f"Top item: {ranked_content[0].content.title}")
        if trends:
            parts.append(f"Top trend: {trends[0].name}")
        return "\n\n".join(parts)
