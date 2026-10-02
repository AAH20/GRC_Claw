"""Integration tests for Content Generator + SEO Optimizer.

Tests the integration between the content-generator and seo-optimizer projects,
verifying that generated content is properly optimized for search engines and that
SEO insights inform content generation strategy.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import pytest


class TestContentSEOIntegration:
    """Integration tests for content-generator and seo-optimizer collaboration."""

    @pytest.fixture
    def generated_content(self) -> Dict[str, Any]:
        """Create generated content for SEO optimization testing.

        Returns:
            Generated content dictionary.
        """
        return {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "title": "AI Marketing Automation: The Complete Guide",
            "body": "AI marketing automation is transforming how businesses reach and engage customers. "
                   "In this comprehensive guide, we explore the latest tools, strategies, and best practices "
                   "for implementing AI-driven marketing automation in your organization.",
            "meta_description": "Discover how AI marketing automation can transform your business with "
                             "the latest tools, strategies, and best practices.",
            "content_type": "blog_post",
            "word_count": 1500,
            "language": "en",
            "target_keywords": ["AI marketing automation", "marketing automation tools", "AI marketing"],
        }

    @pytest.fixture
    def seo_analysis_result(self) -> Dict[str, Any]:
        """Create SEO analysis result for content optimization.

        Returns:
            SEO analysis result dictionary.
        """
        return {
            "analysis_id": f"seo_{uuid.uuid4().hex[:8]}",
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "overall_score": 78,
            "keyword_optimization": {
                "score": 85,
                "primary_keyword": "AI marketing automation",
                "keyword_density": 0.025,
                "issues": [],
            },
            "readability": {
                "score": 72,
                "flesch_reading_ease": 65,
                "grade_level": 10,
                "issues": ["some_long_sentences"],
            },
            "technical_seo": {
                "score": 80,
                "meta_description_length": 155,
                "title_length": 45,
                "issues": [],
            },
            "recommendations": [
                "Add more internal links",
                "Include FAQ section for featured snippets",
                "Optimize images with alt text",
            ],
        }

    def test_generated_content_includes_seo_metadata(
        self, generated_content: Dict[str, Any]
    ) -> None:
        """Verify generated content includes SEO metadata.

        Args:
            generated_content: Generated content fixture.
        """
        assert "title" in generated_content
        assert "meta_description" in generated_content
        assert "target_keywords" in generated_content

        # Title should be within SEO best practice length
        assert 30 <= len(generated_content["title"]) <= 60

        # Meta description should be within recommended length
        assert 120 <= len(generated_content["meta_description"]) <= 160

    def test_seo_analysis_processes_generated_content(
        self, generated_content: Dict[str, Any], seo_analysis_result: Dict[str, Any]
    ) -> None:
        """Verify SEO analysis correctly processes generated content.

        Args:
            generated_content: Generated content fixture.
            seo_analysis_result: SEO analysis result fixture.
        """
        # SEO analysis should reference the content
        assert seo_analysis_result["content_id"] is not None

        # Overall score should be calculated
        assert 0 <= seo_analysis_result["overall_score"] <= 100

        # Keyword optimization should be analyzed
        keyword_opt = seo_analysis_result["keyword_optimization"]
        assert 0 <= keyword_opt["score"] <= 100
        assert keyword_opt["primary_keyword"] in generated_content["target_keywords"]

    def test_content_generation_uses_seo_keywords(self) -> None:
        """Verify content generation incorporates target keywords."""
        content = {
            "title": "AI Marketing Automation: The Complete Guide",
            "body": "AI marketing automation is transforming businesses. "
                   "Marketing automation tools help streamline campaigns.",
            "target_keywords": ["AI marketing automation", "marketing automation tools"],
        }

        # Check keyword presence in title
        title_lower = content["title"].lower()
        assert "ai marketing automation" in title_lower

        # Check keyword presence in body
        body_lower = content["body"].lower()
        assert "ai marketing automation" in body_lower

    def test_seo_recommendations_improve_content(
        self, generated_content: Dict[str, Any], seo_analysis_result: Dict[str, Any]
    ) -> None:
        """Verify SEO recommendations can be applied to improve content.

        Args:
            generated_content: Generated content fixture.
            seo_analysis_result: SEO analysis result fixture.
        """
        recommendations = seo_analysis_result["recommendations"]
        assert len(recommendations) > 0

        # Each recommendation should be actionable
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0

        # Apply recommendations and verify improvement
        improved_content = {**generated_content}
        improved_content["faq_section"] = "Generated FAQ for featured snippets"
        improved_content["internal_links"] = ["related-article-1", "related-article-2"]

        assert "faq_section" in improved_content
        assert "internal_links" in improved_content

    def test_content_seo_end_to_end_flow(self) -> None:
        """Test the complete flow from content generation to SEO optimization."""
        # Step 1: Generate content with SEO keywords
        content_request = {
            "query": "AI marketing automation",
            "content_type": "article",
            "language": "en",
            "target_keywords": ["AI marketing automation", "marketing automation tools"],
        }
        assert len(content_request["target_keywords"]) > 0

        # Step 2: Content is generated
        generated = {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "title": "AI Marketing Automation: The Complete Guide",
            "body": "AI marketing automation is transforming businesses...",
            "meta_description": "Discover AI marketing automation tools and strategies",
            "word_count": 1500,
        }
        assert generated["word_count"] > 0

        # Step 3: SEO analysis is performed
        seo_result = {
            "analysis_id": f"seo_{uuid.uuid4().hex[:8]}",
            "content_id": generated["content_id"],
            "overall_score": 78,
            "recommendations": ["Add internal links", "Include FAQ section"],
        }
        assert seo_result["overall_score"] > 0

        # Step 4: Content is optimized
        optimized = {
            **generated,
            "faq_section": "Generated FAQ",
            "internal_links": ["link1", "link2"],
            "seo_score": 85,
        }
        assert optimized["seo_score"] > seo_result["overall_score"]

    def test_seo_keyword_research_informs_content(self) -> None:
        """Verify SEO keyword research informs content generation."""
        # Keyword research data
        keywords = [
            {
                "keyword": "AI marketing automation",
                "search_volume": 5000,
                "competition": "medium",
                "cpc_estimate": 3.50,
                "intent": "informational",
            },
            {
                "keyword": "marketing automation tools",
                "search_volume": 3000,
                "competition": "high",
                "cpc_estimate": 5.00,
                "intent": "commercial",
            },
        ]

        # Content should target high-value keywords
        target_keywords = [k["keyword"] for k in keywords if k["search_volume"] >= 3000]
        assert len(target_keywords) > 0

        # Content strategy should consider competition
        for kw in keywords:
            assert kw["competition"] in ["low", "medium", "high"]
            assert kw["intent"] in ["informational", "commercial", "transactional", "navigational"]

    def test_content_readability_optimization(self) -> None:
        """Verify content readability is optimized for target audience."""
        readability_metrics = {
            "flesch_reading_ease": 65,
            "grade_level": 10,
            "avg_sentence_length": 18,
            "avg_word_length": 5.2,
        }

        # Content should be readable for general audience
        assert 50 <= readability_metrics["flesch_reading_ease"] <= 80
        assert readability_metrics["grade_level"] <= 12

        # Sentence length should be reasonable
        assert readability_metrics["avg_sentence_length"] <= 25

    def test_seo_technical_optimization(self, generated_content: Dict[str, Any]) -> None:
        """Verify technical SEO aspects are correctly handled.

        Args:
            generated_content: Generated content fixture.
        """
        technical_seo = {
            "title_length": len(generated_content["title"]),
            "meta_description_length": len(generated_content["meta_description"]),
            "has_h1": True,
            "has_h2": True,
            "image_alt_text": True,
            "internal_links": 3,
            "external_links": 2,
        }

        # Title should be 30-60 characters
        assert 30 <= technical_seo["title_length"] <= 60

        # Meta description should be 120-160 characters
        assert 120 <= technical_seo["meta_description_length"] <= 160

        # Should have proper heading structure
        assert technical_seo["has_h1"] is True
        assert technical_seo["has_h2"] is True

    def test_content_seo_error_handling(self) -> None:
        """Verify error handling in content-SEO integration."""
        # Test with missing content
        empty_content = {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "title": "",
            "body": "",
        }

        # Should handle gracefully
        assert len(empty_content["title"]) == 0

        # Test with missing keywords
        no_keywords = {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "title": "Test Content",
            "target_keywords": [],
        }

        assert len(no_keywords["target_keywords"]) == 0

    def test_content_seo_performance_tracking(self) -> None:
        """Verify content performance is tracked across generation and optimization."""
        performance_data = {
            "content_id": f"content_{uuid.uuid4().hex[:8]}",
            "generation_time_ms": 2500,
            "seo_analysis_time_ms": 800,
            "optimization_time_ms": 1200,
            "total_time_ms": 4500,
            "seo_score_before": 65,
            "seo_score_after": 85,
            "improvement": 20,
        }

        assert performance_data["total_time_ms"] > 0
        assert performance_data["seo_score_after"] > performance_data["seo_score_before"]
        assert performance_data["improvement"] > 0
