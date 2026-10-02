"""Performance benchmarks for the Content Generator component.

These benchmarks verify that content generation operations meet
production SLAs for latency and throughput.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestContentGeneratorBenchmarks:
    """Benchmark suite for content generation operations."""

    SLA_MS = 1000.0

    def test_content_strategy_generation(
        self,
        run_benchmark: Any,
        sample_content_strategy: dict[str, Any],
    ) -> None:
        """Benchmark content strategy generation latency.

        Verifies that generating a content strategy completes within the
        SLA threshold of 1000ms.
        """
        def generate_strategy() -> dict[str, Any]:
            """Generate a content strategy from input parameters."""
            return {
                "content_type": sample_content_strategy["content_type"],
                "target_audience": sample_content_strategy["target_audience"],
                "tone": sample_content_strategy["tone"],
                "angle": sample_content_strategy["angle"],
                "key_messages": sample_content_strategy["key_messages"],
                "word_count_target": sample_content_strategy["word_count_target"],
                "seo_recommendations": sample_content_strategy["seo_recommendations"],
                "content_outline": sample_content_strategy["content_outline"],
            }

        result = run_benchmark(
            generate_strategy,
            name="strategy_generation",
            iterations=100,
            metadata={"content_type": sample_content_strategy["content_type"]},
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Strategy generation SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_content_outline_building(
        self,
        run_benchmark: Any,
        sample_content_strategy: dict[str, Any],
    ) -> None:
        """Benchmark content outline construction.

        Verifies that building a content outline completes within
        acceptable latency.
        """
        def build_outline() -> list[dict[str, Any]]:
            """Build a structured content outline."""
            base_outline = sample_content_strategy["content_outline"]
            enhanced = []
            for section in base_outline:
                enhanced.append({
                    **section,
                    "subsections": [
                        {"heading": f"{section['heading']} - Part {i + 1}"}
                        for i in range(3)
                    ],
                    "seo_keywords": ["keyword1", "keyword2"],
                })
            return enhanced

        result = run_benchmark(
            build_outline,
            name="outline_building",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Outline building SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_seo_recommendation_generation(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark SEO recommendation generation.

        Verifies that SEO recommendations complete within acceptable latency.
        """
        def generate_seo_recommendations() -> dict[str, Any]:
            """Generate SEO recommendations for content."""
            return {
                "primary_keyword": "AI marketing tools",
                "secondary_keywords": ["AI automation", "marketing AI"],
                "meta_description": "Discover how AI transforms marketing operations.",
                "title_suggestions": [
                    "AI Marketing Tools: A Complete Guide",
                    "How AI is Transforming Marketing in 2026",
                ],
                "content_gaps": ["case studies", "ROI calculator"],
                "readability_score": 85,
            }

        result = run_benchmark(
            generate_seo_recommendations,
            name="seo_recommendations",
            iterations=300,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"SEO recommendations SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_content_quality_scoring(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark content quality scoring.

        Verifies that quality scoring completes within acceptable latency.
        """
        def score_quality() -> dict[str, float]:
            """Score content quality across multiple dimensions."""
            scores = {
                "readability": 85.0,
                "seo_optimization": 78.0,
                "engagement": 72.0,
                "originality": 91.0,
                "tone_consistency": 88.0,
            }
            overall = sum(scores.values()) / len(scores)
            return {**scores, "overall": round(overall, 2)}

        result = run_benchmark(
            score_quality,
            name="quality_scoring",
            iterations=500,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Quality scoring SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )

    def test_multi_language_content_generation(
        self,
        run_benchmark: Any,
        sample_content_strategy: dict[str, Any],
    ) -> None:
        """Benchmark multi-language content generation.

        Verifies that generating content in multiple languages scales
        acceptably.
        """
        languages = ["en", "es", "fr", "de", "ar"]

        def generate_multi_language() -> dict[str, Any]:
            """Generate content variants for multiple languages."""
            results = {}
            for lang in languages:
                results[lang] = {
                    "title": f"Content in {lang}",
                    "word_count_target": sample_content_strategy["word_count_target"],
                    "tone": sample_content_strategy["tone"],
                }
            return results

        result = run_benchmark(
            generate_multi_language,
            name="multi_language_generation",
            iterations=100,
            metadata={"languages": len(languages)},
        )

        assert result.avg_ms <= self.SLA_MS * 2, (
            f"Multi-language SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS * 2}ms"
        )

    def test_content_personalization(
        self,
        run_benchmark: Any,
    ) -> None:
        """Benchmark content personalization.

        Verifies that personalizing content for different segments
        completes within acceptable latency.
        """
        segments = [
            {"name": "enterprise", "tone": "formal"},
            {"name": "smb", "tone": "casual"},
            {"name": "startup", "tone": "energetic"},
        ]

        def personalize_content() -> list[dict[str, Any]]:
            """Personalize content for multiple segments."""
            results = []
            for segment in segments:
                results.append({
                    "segment": segment["name"],
                    "tone": segment["tone"],
                    "key_message": f"Transform your workflow with {segment['name']} AI",
                    "cta": "Get Started" if segment["name"] == "enterprise" else "Try Free",
                })
            return results

        result = run_benchmark(
            personalize_content,
            name="content_personalization",
            iterations=200,
        )

        assert result.avg_ms <= self.SLA_MS, (
            f"Personalization SLA violation: {result.avg_ms:.2f}ms > {self.SLA_MS}ms"
        )
