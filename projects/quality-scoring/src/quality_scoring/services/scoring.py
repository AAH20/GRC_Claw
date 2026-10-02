"""Business logic services for quality scoring."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from quality_scoring.agents import (
    EngagementScorerAgent,
    ImprovementSuggesterAgent,
    OriginalityScorerAgent,
    ReadabilityScorerAgent,
    SEOScorerAgent,
)
from quality_scoring.config.settings import Settings
from quality_scoring.integrations import CacheClient, LLMClient
from quality_scoring.models.schemas import (
    BenchmarkComparison,
    BenchmarkData,
    ContentInput,
    ContentType,
    DimensionScore,
    ImprovementPlan,
    QualityScore,
    ScoreDimension,
    ScoreLevel,
)

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for orchestrating content quality scoring."""

    # Dimension weights for overall score calculation
    DIMENSION_WEIGHTS: dict[ScoreDimension, float] = {
        ScoreDimension.READABILITY: 0.25,
        ScoreDimension.ORIGINALITY: 0.25,
        ScoreDimension.ENGAGEMENT: 0.25,
        ScoreDimension.SEO: 0.25,
    }

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the scoring service.

        Args:
            settings: Application settings.
        """
        self.settings = settings or Settings()
        self.llm_client = LLMClient(self.settings)
        self.cache = CacheClient(ttl_seconds=3600)

        # Initialize agents
        llm = self.llm_client.get_llm()
        self.agents: dict[ScoreDimension, Any] = {
            ScoreDimension.READABILITY: ReadabilityScorerAgent(llm, self.settings),
            ScoreDimension.ORIGINALITY: OriginalityScorerAgent(llm, self.settings),
            ScoreDimension.ENGAGEMENT: EngagementScorerAgent(llm, self.settings),
            ScoreDimension.SEO: SEOScorerAgent(llm, self.settings),
        }
        self.improvement_agent = ImprovementSuggesterAgent(llm, self.settings)

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

    def _compute_overall_score(self, dimensions: list[DimensionScore]) -> float:
        """Compute weighted overall score from dimension scores.

        Args:
            dimensions: List of dimension scores.

        Returns:
            Weighted overall score.
        """
        if not dimensions:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for dim in dimensions:
            weight = self.DIMENSION_WEIGHTS.get(dim.dimension, 0.25)
            weighted_sum += dim.score * weight
            total_weight += weight

        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

    def _estimate_reading_time(self, text: str) -> float:
        """Estimate reading time in minutes.

        Args:
            text: The content text.

        Returns:
            Estimated reading time in minutes.
        """
        word_count = len(text.split())
        # Average reading speed: 200-250 WPM
        return round(word_count / 225, 2)

    async def score_content(
        self,
        content_input: ContentInput,
        dimensions: list[ScoreDimension] | None = None,
    ) -> QualityScore:
        """Score content quality across specified dimensions.

        Args:
            content_input: The content to score.
            dimensions: Specific dimensions to score (all if None).

        Returns:
            Complete QualityScore with all requested dimensions.
        """
        start_time = time.time()
        score_id = str(uuid.uuid4())

        # Check cache
        cache_key = f"score:{hash(content_input.content)}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Returning cached score for content")
            return cached

        # Determine which dimensions to score
        dims_to_score = dimensions or list(ScoreDimension)

        # Run agents concurrently
        import asyncio

        tasks = []
        for dim in dims_to_score:
            agent = self.agents.get(dim)
            if agent:
                tasks.append(agent.score(content_input.content))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        dimension_scores: list[DimensionScore] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Agent failed: %s", str(result))
                continue
            if result.success and result.data:
                dimension_scores.append(result.data)

        # Compute overall score
        overall_score = self._compute_overall_score(dimension_scores)
        overall_level = self._score_to_level(overall_score)

        processing_time = (time.time() - start_time) * 1000

        quality_score = QualityScore(
            id=score_id,
            content_type=content_input.content_type,
            overall_score=overall_score,
            overall_level=overall_level,
            dimensions=dimension_scores,
            word_count=len(content_input.content.split()),
            reading_time_minutes=self._estimate_reading_time(content_input.content),
            processing_time_ms=round(processing_time, 2),
            metadata={
                "title": content_input.title,
                "url": content_input.url,
                "language": content_input.language,
                **content_input.metadata,
            },
        )

        # Cache the result
        self.cache.set(cache_key, quality_score)

        return quality_score

    async def get_improvements(
        self,
        content: str,
        score_id: str,
        dimension_scores: list[DimensionScore],
    ) -> ImprovementPlan:
        """Generate improvement suggestions for content.

        Args:
            content: The original content text.
            score_id: The quality score ID.
            dimension_scores: Dimension scores to base suggestions on.

        Returns:
            ImprovementPlan with actionable suggestions.
        """
        result = await self.improvement_agent.score(
            content, dimension_scores=dimension_scores, score_id=score_id
        )

        if result.success and result.data:
            return result.data

        # Return empty plan on failure
        from datetime import datetime

        return ImprovementPlan(
            id=str(uuid.uuid4()),
            score_id=score_id,
            suggestions=[],
            total_expected_improvement=0.0,
            created_at=datetime.utcnow(),
        )


class BenchmarkService:
    """Service for benchmark comparisons."""

    # Simulated benchmark data (in production, load from database)
    BENCHMARKS: dict[ContentType, dict[ScoreDimension, dict[str, float]]] = {
        ContentType.ARTICLE: {
            ScoreDimension.READABILITY: {

                "mean": 65.0,

                "median": 67.0,

                "p25": 50.0,

                "p75": 80.0,

                "p90": 90.0,

                "sample_size": 1000,

            },
            ScoreDimension.ORIGINALITY: {

                "mean": 70.0,

                "median": 72.0,

                "p25": 55.0,

                "p75": 85.0,

                "p90": 92.0,

                "sample_size": 1000,

            },
            ScoreDimension.ENGAGEMENT: {

                "mean": 60.0,

                "median": 62.0,

                "p25": 45.0,

                "p75": 75.0,

                "p90": 85.0,

                "sample_size": 1000,

            },
            ScoreDimension.SEO: {

                "mean": 55.0,

                "median": 57.0,

                "p25": 40.0,

                "p75": 70.0,

                "p90": 82.0,

                "sample_size": 1000,

            }
        },
        ContentType.BLOG_POST: {
            ScoreDimension.READABILITY: {

                "mean": 68.0,

                "median": 70.0,

                "p25": 52.0,

                "p75": 82.0,

                "p90": 91.0,

                "sample_size": 800,

            },
            ScoreDimension.ORIGINALITY: {

                "mean": 72.0,

                "median": 74.0,

                "p25": 58.0,

                "p75": 86.0,

                "p90": 93.0,

                "sample_size": 800,

            },
            ScoreDimension.ENGAGEMENT: {

                "mean": 65.0,

                "median": 67.0,

                "p25": 50.0,

                "p75": 78.0,

                "p90": 88.0,

                "sample_size": 800,

            },
            ScoreDimension.SEO: {

                "mean": 58.0,

                "median": 60.0,

                "p25": 42.0,

                "p75": 72.0,

                "p90": 84.0,

                "sample_size": 800,

            }
        },
        ContentType.GENERAL: {
            ScoreDimension.READABILITY: {

                "mean": 60.0,

                "median": 62.0,

                "p25": 45.0,

                "p75": 75.0,

                "p90": 85.0,

                "sample_size": 2000,

            },
            ScoreDimension.ORIGINALITY: {

                "mean": 65.0,

                "median": 67.0,

                "p25": 50.0,

                "p75": 80.0,

                "p90": 90.0,

                "sample_size": 2000,

            },
            ScoreDimension.ENGAGEMENT: {

                "mean": 55.0,

                "median": 57.0,

                "p25": 40.0,

                "p75": 70.0,

                "p90": 82.0,

                "sample_size": 2000,

            },
            ScoreDimension.SEO: {

                "mean": 50.0,

                "median": 52.0,

                "p25": 35.0,

                "p75": 65.0,

                "p90": 78.0,

                "sample_size": 2000,

            }
        },
    }

    def __init__(self) -> None:
        """Initialize the benchmark service."""
        pass

    def _compute_percentile(self, score: float, benchmark: dict[str, float]) -> float:
        """Compute approximate percentile for a score.

        Args:
            score: The content score.
            benchmark: Benchmark statistics.

        Returns:
            Approximate percentile (0-100).
        """
        if score <= benchmark["p25"]:
            return 25.0 * (score / benchmark["p25"]) if benchmark["p25"] > 0 else 0.0
        if score <= benchmark["median"]:
            return (
        25.0 + 25.0 * ((score - benchmark["p25"]) / (benchmark["median"] - benchmark["p25"]))
    )
        if score <= benchmark["p75"]:
            return (
        50.0 + 25.0 * ((score - benchmark["median"]) / (benchmark["p75"] - benchmark["median"]))
    )
        if score <= benchmark["p90"]:
            return (
        75.0 + 15.0 * ((score - benchmark["p75"]) / (benchmark["p90"] - benchmark["p75"]))
    )
        return min(99.0, 90.0 + 9.0 * ((score - benchmark["p90"]) / (100.0 - benchmark["p90"])))

    def compare(
        self,
        score_id: str,
        content_type: ContentType,
        dimension_scores: list[DimensionScore],
    ) -> BenchmarkComparison:
        """Compare content scores against benchmarks.

        Args:
            score_id: The quality score ID.
            content_type: The content type.
            dimension_scores: Dimension scores to compare.

        Returns:
            BenchmarkComparison with percentile rankings.
        """
        # Get benchmark data for content type (fallback to GENERAL)
        type_benchmarks = self.BENCHMARKS.get(content_type, self.BENCHMARKS[ContentType.GENERAL])

        comparisons: list[BenchmarkData] = []
        percentiles: list[float] = []

        for dim_score in dimension_scores:
            bench = (
        type_benchmarks.get(dim_score.dimension, type_benchmarks[ScoreDimension.READABILITY])
    )
            percentile = self._compute_percentile(dim_score.score, bench)
            percentiles.append(percentile)

            comparisons.append(
                BenchmarkData(
                    content_type=content_type,
                    dimension=dim_score.dimension,
                    mean=bench["mean"],
                    median=bench["median"],
                    p25=bench["p25"],
                    p75=bench["p75"],
                    p90=bench["p90"],
                    sample_size=int(bench["sample_size"]),
                )
            )

        overall_percentile = sum(percentiles) / len(percentiles) if percentiles else 50.0

        # Generate summary
        if overall_percentile >= 75:
            summary = (
                f"Content performs in the top {100 - overall_percentile:.0f}% "
                f"for {content_type.value} content."
            )
        elif overall_percentile >= 50:
            summary = f"Content performs above average for {content_type.value} content."
        elif overall_percentile >= 25:
            summary = (
                f"Content performs below average for {content_type.value} content. "
                f"Improvements recommended."
            )
        else:
            summary = (
                f"Content performs in the bottom quartile for {content_type.value} content. "
                f"Significant improvements needed."
            )

        from datetime import datetime

        return BenchmarkComparison(
            id=str(uuid.uuid4()),
            score_id=score_id,
            content_type=content_type,
            comparisons=comparisons,
            percentile_overall=round(overall_percentile, 2),
            summary=summary,
            created_at=datetime.utcnow(),
        )
