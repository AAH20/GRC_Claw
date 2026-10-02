"""Content Optimization Agent for improving content SEO performance."""

from __future__ import annotations

from typing import Any

import structlog

from seo_optimizer.agents.base import AgentResult, BaseAgent

logger = structlog.get_logger(__name__)


class ContentOptimizationAgent(BaseAgent[dict[str, Any]]):
    """Agent for analyzing and optimizing content for SEO.

    Evaluates content against SEO best practices including keyword usage,
    readability, structure, and semantic relevance.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Content Optimization Agent.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__("ContentOptimizationAgent", config)

    async def execute(
        self,
        content: str,
        target_keywords: list[str],
        content_type: str = "blog_post",
        **kwargs: Any,
    ) -> AgentResult[dict[str, Any]]:
        """Execute content optimization analysis.

        Args:
            content: The content to analyze and optimize.
            target_keywords: List of target keywords to optimize for.
            content_type: Type of content (blog_post, product_page, etc.).
            **kwargs: Additional parameters.

        Returns:
            AgentResult with optimization recommendations.
        """
        self.logger.info(
            "Starting content optimization",
            content_type=content_type,
            target_keywords=target_keywords,
            content_length=len(content),
        )

        try:
            analysis: dict[str, Any] = {
                "content_type": content_type,
                "target_keywords": target_keywords,
                "overall_score": 0,
                "readability": {},
                "keyword_analysis": {},
                "structure_analysis": {},
                "recommendations": [],
                "optimized_content": None,
            }

            # Analyze readability
            analysis["readability"] = self._analyze_readability(content)

            # Analyze keyword usage
            analysis["keyword_analysis"] = self._analyze_keywords(
                content, target_keywords
            )

            # Analyze content structure
            analysis["structure_analysis"] = self._analyze_structure(content)

            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)

            # Calculate overall score
            analysis["overall_score"] = self._calculate_overall_score(analysis)

            return AgentResult(
                success=True,
                data=analysis,
                metadata={
                    "content_length": len(content),
                    "word_count": len(content.split()),
                },
            )

        except Exception as exc:
            self.logger.error("Content optimization failed", error=str(exc))
            return AgentResult(
                success=False,
                error=f"Content optimization failed: {exc}",
            )

    def _analyze_readability(self, content: str) -> dict[str, Any]:
        """Analyze content readability metrics.

        Args:
            content: The content to analyze.

        Returns:
            Readability metrics dictionary.
        """
        sentences = content.split(". ")
        words = content.split()
        syllables = sum(self._count_syllables(word) for word in words)

        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_syllables_per_word = syllables / max(len(words), 1)

        # Flesch Reading Ease score
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))

        return {
            "flesch_reading_ease": round(flesch_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len([p for p in content.split("\n\n") if p.strip()]),
        }

    def _analyze_keywords(
        self, content: str, target_keywords: list[str]
    ) -> dict[str, Any]:
        """Analyze keyword usage in content.

        Args:
            content: The content to analyze.
            target_keywords: List of target keywords.

        Returns:
            Keyword analysis dictionary.
        """
        content_lower = content.lower()
        words = content_lower.split()
        total_words = max(len(words), 1)

        keyword_stats = {}
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            density = (count * len(keyword_lower.split())) / total_words * 100

            keyword_stats[keyword] = {
                "count": count,
                "density_percent": round(density, 2),
                "in_title": False,  # Would need title extraction
                "in_headings": False,  # Would need heading extraction
                "in_first_100_words": keyword_lower in " ".join(words[:100]),
            }

        return {
            "keywords": keyword_stats,
            "total_keyword_density": round(
                sum(k["density_percent"] for k in keyword_stats.values()), 2
            ),
            "primary_keyword": target_keywords[0] if target_keywords else None,
        }

    def _analyze_structure(self, content: str) -> dict[str, Any]:
        """Analyze content structure (headings, lists, etc.).

        Args:
            content: The content to analyze.

        Returns:
            Structure analysis dictionary.
        """
        lines = content.split("\n")
        headings = [line for line in lines if line.strip().startswith("#")]
        lists = [line for line in lines if line.strip().startswith(("-", "*", "1."))]

        return {
            "heading_count": len(headings),
            "h1_count": len([h for h in headings if h.startswith("# ")]),
            "h2_count": len([h for h in headings if h.startswith("## ")]),
            "h3_count": len([h for h in headings if h.startswith("### ")]),
            "list_items_count": len(lists),
            "has_introduction": len(content) > 0,
            "has_conclusion": any(
                word in content[-200:].lower()
                for word in ["conclusion", "summary", "in summary", "to conclude"]
            ),
        }

    def _generate_recommendations(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate SEO recommendations based on analysis.

        Args:
            analysis: The content analysis data.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        readability = analysis.get("readability", {})
        if readability.get("flesch_reading_ease", 0) < 60:
            recommendations.append(
                {
                    "category": "readability",
                    "priority": "high",
                    "issue": "Content readability is low",
                    "recommendation": "Simplify sentence structure and use shorter words",
                }
            )

        keyword_analysis = analysis.get("keyword_analysis", {})
        for keyword, stats in keyword_analysis.get("keywords", {}).items():
            if stats["density_percent"] < 0.5:
                recommendations.append(
                    {
                        "category": "keywords",
                        "priority": "medium",
                        "issue": f"Low keyword density for '{keyword}'",
                        "recommendation": f"Increase usage of '{keyword}' naturally in content",
                    }
                )
            elif stats["density_percent"] > 2.5:
                recommendations.append(
                    {
                        "category": "keywords",
                        "priority": "high",
                        "issue": f"Keyword stuffing detected for '{keyword}'",
                        "recommendation": f"Reduce usage of '{keyword}' to avoid penalties",
                    }
                )

        structure = analysis.get("structure_analysis", {})
        if structure.get("h1_count", 0) == 0:
            recommendations.append(
                {
                    "category": "structure",
                    "priority": "high",
                    "issue": "Missing H1 heading",
                    "recommendation": "Add a clear H1 heading with the primary keyword",
                }
            )

        return recommendations

    def _calculate_overall_score(self, analysis: dict[str, Any]) -> int:
        """Calculate overall SEO content score.

        Args:
            analysis: The content analysis data.

        Returns:
            Overall score from 0-100.
        """
        score = 50  # Base score

        readability = analysis.get("readability", {})
        flesch = readability.get("flesch_reading_ease", 0)
        if flesch >= 60:
            score += 15
        elif flesch >= 40:
            score += 5

        keyword_analysis = analysis.get("keyword_analysis", {})
        for stats in keyword_analysis.get("keywords", {}).values():
            density = stats.get("density_percent", 0)
            if 0.5 <= density <= 2.5:
                score += 10

        structure = analysis.get("structure_analysis", {})
        if structure.get("h1_count", 0) > 0:
            score += 10
        if structure.get("h2_count", 0) >= 2:
            score += 5

        return min(100, score)

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Estimate syllable count for a word.

        Args:
            word: The word to count syllables for.

        Returns:
            Estimated syllable count.
        """
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        if word.endswith("e") and count > 1:
            count -= 1

        return max(1, count)
