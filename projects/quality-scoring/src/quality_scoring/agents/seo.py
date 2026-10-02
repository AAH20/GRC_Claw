"""SEO scoring agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from langchain_core.language_models import BaseLanguageModel

from quality_scoring.agents.base import AgentResult, BaseScoringAgent
from quality_scoring.config.settings import Settings
from quality_scoring.models.schemas import DimensionScore, ScoreDimension, ScoreLevel

logger = logging.getLogger(__name__)


class SEOScorerAgent(BaseScoringAgent[DimensionScore]):
    """Agent that scores content SEO optimization using technical analysis."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the SEO scorer agent."""
        super().__init__(llm=llm, settings=settings)

    @property
    def agent_name(self) -> str:
        """Return the agent name."""
        return "SEOScorerAgent"

    @property
    def dimension(self) -> str:
        """Return the scoring dimension."""
        return ScoreDimension.SEO.value

    def _analyze_keyword_density(self, text: str) -> dict[str, float]:
        """Analyze keyword density in the content.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with keyword density metrics.
        """
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return {"avg_keyword_density": 0.0, "top_keyword_ratio": 0.0}

        # Simple keyword extraction (most frequent meaningful words)
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "need", "dare", "ought", "used", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through",
            "during", "before", "after", "above", "below", "between",
            "and", "but", "or", "nor", "not", "so", "yet", "both",
            "either", "neither", "each", "every", "all", "any", "few",
            "more", "most", "other", "some", "such", "no", "only",
            "own", "same", "than", "too", "very", "just", "because",
            "if", "when", "while", "that", "this", "these", "those",
            "it", "its", "i", "me", "my", "we", "our", "you", "your",
            "he", "him", "his", "she", "her", "they", "them", "their",
        }

        word_freq: dict[str, int] = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        if not word_freq:
            return {"avg_keyword_density": 0.0, "top_keyword_ratio": 0.0}

        total_words = len(words)
        densities = [count / total_words for count in word_freq.values()]
        top_keyword_ratio = max(densities) if densities else 0.0

        return {
            "avg_keyword_density": sum(densities) / len(densities),
            "top_keyword_ratio": top_keyword_ratio,
        }

    def _analyze_headings(self, text: str) -> dict[str, Any]:
        """Analyze heading structure.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with heading metrics.
        """
        h1_count = len(re.findall(r"^#\s+", text, re.MULTILINE))
        h2_count = len(re.findall(r"^##\s+", text, re.MULTILINE))
        h3_count = len(re.findall(r"^###\s+", text, re.MULTILINE))

        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "has_proper_structure": h1_count == 1 and h2_count >= 1,
        }

    def _analyze_links(self, text: str) -> dict[str, Any]:
        """Analyze internal and external links.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with link metrics.
        """
        # Markdown links
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        # HTML links
        html_links = re.findall(r'<a\s+[^>]*href="([^"]*)"[^>]*>', text, re.IGNORECASE)

        all_links = [link[1] for link in md_links] + html_links

        internal_links = 0
        external_links = 0

        for link in all_links:
            parsed = urlparse(link)
            if not parsed.netloc or parsed.netloc == "":
                internal_links += 1
            else:
                external_links += 1

        return {
            "total_links": len(all_links),
            "internal_links": internal_links,
            "external_links": external_links,
            "has_links": len(all_links) > 0,
        }

    def _analyze_meta_content(self, text: str) -> dict[str, Any]:
        """Analyze meta content indicators.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with meta content metrics.
        """
        # Check for meta description patterns
        has_meta_desc = bool(re.search(r'<meta\s+name="description"', text, re.IGNORECASE))

        # Check for alt text on images
        images = re.findall(r'<img\s+[^>]*>', text, re.IGNORECASE)
        images_with_alt = re.findall(r'<img\s+[^>]*alt="[^"]*"[^>]*>', text, re.IGNORECASE)

        # Check for title tag
        has_title = bool(re.search(r"<title>", text, re.IGNORECASE))

        return {
            "has_meta_description": has_meta_desc,
            "has_title_tag": has_title,
            "image_count": len(images),
            "images_with_alt": len(images_with_alt),
            "alt_text_ratio": len(images_with_alt) / len(images) if images else 1.0,
        }

    def _analyze_content_length(self, text: str) -> dict[str, Any]:
        """Analyze content length for SEO.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with length metrics.
        """
        word_count = len(text.split())

        # SEO optimal: 300-2500 words
        if word_count < 300:
            length_score = word_count / 300 * 50
        elif word_count <= 2500:
            length_score = 100
        else:
            length_score = max(50, 100 - (word_count - 2500) / 100)

        return {
            "word_count": word_count,
            "length_score": length_score,
            "is_optimal_length": 300 <= word_count <= 2500,
        }

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
        """Score content SEO optimization.

        Args:
            content: The content text to score.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResult containing DimensionScore.
        """
        try:
            keyword_metrics = self._analyze_keyword_density(content)
            heading_metrics = self._analyze_headings(content)
            link_metrics = self._analyze_links(content)
            meta_metrics = self._analyze_meta_content(content)
            length_metrics = self._analyze_content_length(content)

            # Weighted scoring
            keyword_score = min(100, keyword_metrics["avg_keyword_density"] * 500)
            heading_score = 100 if heading_metrics["has_proper_structure"] else (
                50 if heading_metrics["h1_count"] > 0 else 20
            )
            link_score = 100 if link_metrics["has_links"] else 30
            meta_score = (
                (30 if meta_metrics["has_meta_description"] else 0)
                + (30 if meta_metrics["has_title_tag"] else 0)
                + (40 * meta_metrics["alt_text_ratio"])
            )
            length_score = length_metrics["length_score"]

            final_score = (
                keyword_score * 0.25
                + heading_score * 0.25
                + link_score * 0.15
                + meta_score * 0.2
                + length_score * 0.15
            )
            final_score = max(0.0, min(100.0, final_score))

            # Confidence based on content length
            word_count = len(content.split())
            confidence = min(1.0, word_count / 300) if word_count > 0 else 0.5

            reasoning_parts = [
                f"Keyword density: {keyword_metrics['avg_keyword_density']:.2%}",
                f"Headings: H1={heading_metrics['h1_count']}, H2={heading_metrics['h2_count']}",
                f"Links: {link_metrics['total_links']} total",
                f"Meta: title={meta_metrics['has_title_tag']}, desc={meta_metrics['has_meta_description']}",
                f"Word count: {length_metrics['word_count']}",
            ]

            dimension_score = DimensionScore(
                dimension=ScoreDimension.SEO,
                score=round(final_score, 2),
                level=self._score_to_level(final_score),
                confidence=round(confidence, 2),
                reasoning="; ".join(reasoning_parts),
                metrics={
                    "keyword_density": round(keyword_metrics["avg_keyword_density"], 4),
                    "top_keyword_ratio": round(keyword_metrics["top_keyword_ratio"], 4),
                    "h1_count": heading_metrics["h1_count"],
                    "h2_count": heading_metrics["h2_count"],
                    "total_links": link_metrics["total_links"],
                    "has_meta_description": meta_metrics["has_meta_description"],
                    "has_title_tag": meta_metrics["has_title_tag"],
                    "alt_text_ratio": round(meta_metrics["alt_text_ratio"], 4),
                    "word_count": length_metrics["word_count"],
                },
            )

            return AgentResult(success=True, data=dimension_score)

        except Exception as exc:
            logger.exception("SEO scoring failed")
            return AgentResult(success=False, error=str(exc))
