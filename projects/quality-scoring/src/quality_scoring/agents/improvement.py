"""Improvement suggester agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from quality_scoring.agents.base import AgentResult, BaseScoringAgent
from quality_scoring.config.settings import Settings
from quality_scoring.models.schemas import (
    DimensionScore,
    ImprovementPlan,
    ImprovementSuggestion,
    ScoreDimension,
)

logger = logging.getLogger(__name__)


class ImprovementSuggesterAgent(BaseScoringAgent[ImprovementPlan]):
    """Agent that generates improvement suggestions based on quality scores."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the improvement suggester agent."""
        super().__init__(llm=llm, settings=settings)

    @property
    def agent_name(self) -> str:
        """Return the agent name."""
        return "ImprovementSuggesterAgent"

    @property
    def dimension(self) -> str:
        """Return the scoring dimension."""
        return "improvement"

    def _generate_readability_suggestions(
        self, score: DimensionScore
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions for readability improvements.

        Args:
            score: The readability dimension score.

        Returns:
            List of improvement suggestions.
        """
        suggestions = []
        metrics = score.metrics

        if metrics.get("avg_sentence_length", 0) > 20:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.READABILITY,
                    priority="high",
                    title="Shorten Long Sentences",
                    description="Break down complex sentences into shorter, more digestible ones.",
                    current_state=(
                        f"Average sentence length is {metrics['avg_sentence_length']:.1f} words"
                    ),
                    target_state="Average sentence length of 15-20 words",
                    expected_impact=15.0,
                    examples=[
                        "Split compound sentences at conjunctions",
                        "Use bullet points for lists",
                        "Remove unnecessary clauses",
                    ],
                )
            )

        if metrics.get("complex_word_ratio", 0) > 0.15:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.READABILITY,
                    priority="medium",
                    title="Simplify Vocabulary",
                    description="Replace complex words with simpler alternatives.",
                    current_state=f"Complex word ratio is {metrics['complex_word_ratio']:.1%}",
                    target_state="Complex word ratio below 10%",
                    expected_impact=10.0,
                    examples=[
                        "Use 'use' instead of 'utilize'",
                        "Use 'help' instead of 'facilitate'",
                        "Use 'start' instead of 'commence'",
                    ],
                )
            )

        if metrics.get("flesch_kincaid_grade", 0) > 10:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.READABILITY,
                    priority="medium",
                    title="Lower Reading Level",
                    description="Aim for a lower grade level to reach a broader audience.",
                    current_state=f"Current grade level: {metrics['flesch_kincaid_grade']:.1f}",
                    target_state="Grade level 8-9 for general audience",
                    expected_impact=12.0,
                    examples=[
                        "Use active voice",
                        "Avoid jargon and technical terms",
                        "Use concrete examples",
                    ],
                )
            )

        return suggestions

    def _generate_originality_suggestions(
        self, score: DimensionScore
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions for originality improvements.

        Args:
            score: The originality dimension score.

        Returns:
            List of improvement suggestions.
        """
        suggestions = []
        metrics = score.metrics

        if metrics.get("lexical_diversity", 1.0) < 0.5:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ORIGINALITY,
                    priority="high",
                    title="Increase Vocabulary Variety",
                    description="Use a wider range of vocabulary to avoid repetition.",
                    current_state=f"Lexical diversity is {metrics['lexical_diversity']:.1%}",
                    target_state="Lexical diversity above 60%",
                    expected_impact=15.0,
                    examples=[
                        "Use synonyms and varied expressions",
                        "Avoid repeating the same sentence structures",
                        "Introduce new terminology where appropriate",
                    ],
                )
            )

        if metrics.get("cliche_count", 0) > 0:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ORIGINALITY,
                    priority="high",
                    title="Remove Clichés",
                    description="Replace overused phrases with fresh, original expressions.",
                    current_state=f"Found {metrics['cliche_count']} cliché phrases",
                    target_state="No clichés in the content",
                    expected_impact=10.0,
                    examples=[
                        "Replace 'at the end of the day' with a specific conclusion",
                        "Replace 'think outside the box' with concrete creative approaches",
                        "Replace 'game changer' with specific impact description",
                    ],
                )
            )

        if metrics.get("sentence_variety", 1.0) < 0.6:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ORIGINALITY,
                    priority="medium",
                    title="Vary Sentence Structure",
                    description="Use different sentence starters and structures.",
                    current_state=f"Sentence variety is {metrics['sentence_variety']:.1%}",
                    target_state="Sentence variety above 70%",
                    expected_impact=8.0,
                    examples=[
                        "Start some sentences with adverbs",
                        "Use questions to engage readers",
                        "Vary between short and long sentences",
                    ],
                )
            )

        return suggestions

    def _generate_engagement_suggestions(
        self, score: DimensionScore
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions for engagement improvements.

        Args:
            score: The engagement dimension score.

        Returns:
            List of improvement suggestions.
        """
        suggestions = []
        metrics = score.metrics

        if metrics.get("question_count", 0) == 0:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ENGAGEMENT,
                    priority="high",
                    title="Add Engaging Questions",
                    description="Include rhetorical or direct questions to engage readers.",
                    current_state="No questions found in content",
                    target_state="At least 2-3 questions per 500 words",
                    expected_impact=12.0,
                    examples=[
                        "What does this mean for your business?",
                        "Have you ever wondered why...?",
                        "How can you apply this to your situation?",
                    ],
                )
            )

        if metrics.get("power_word_count", 0) < 3:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ENGAGEMENT,
                    priority="medium",
                    title="Use Power Words",
                    description="Incorporate compelling words that drive action.",
                    current_state=f"Only {metrics['power_word_count']} power words found",
                    target_state="5+ power words per 500 words",
                    expected_impact=10.0,
                    examples=[
                        "Use 'exclusive', 'proven', 'guaranteed'",
                        "Include 'discover', 'unlock', 'secret'",
                        "Add 'instantly', 'free', 'new'",
                    ],
                )
            )

        if metrics.get("cta_score", 1.0) < 0.5:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ENGAGEMENT,
                    priority="high",
                    title="Add Clear Call-to-Action",
                    description="Include a clear next step for readers.",
                    current_state="No clear CTA detected",
                    target_state="At least one clear CTA per content piece",
                    expected_impact=15.0,
                    examples=[
                        "Sign up for our newsletter",
                        "Download the free guide",
                        "Start your free trial today",
                    ],
                )
            )

        if metrics.get("structural_score", 1.0) < 0.5:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.ENGAGEMENT,
                    priority="medium",
                    title="Improve Content Structure",
                    description="Use formatting to improve readability and engagement.",
                    current_state="Limited structural elements",
                    target_state="Use headers, lists, and emphasis",
                    expected_impact=8.0,
                    examples=[
                        "Add H2/H3 subheadings",
                        "Use bullet points for lists",
                        "Bold key phrases and takeaways",
                    ],
                )
            )

        return suggestions

    def _generate_seo_suggestions(
        self, score: DimensionScore
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions for SEO improvements.

        Args:
            score: The SEO dimension score.

        Returns:
            List of improvement suggestions.
        """
        suggestions = []
        metrics = score.metrics

        if metrics.get("h1_count", 0) != 1:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.SEO,
                    priority="high",
                    title="Fix H1 Tag Structure",
                    description="Ensure exactly one H1 tag that includes the primary keyword.",
                    current_state=f"Found {metrics['h1_count']} H1 tags",
                    target_state="Exactly 1 H1 tag with primary keyword",
                    expected_impact=15.0,
                    examples=[
                        "Use the main keyword in the H1",
                        "Keep H1 under 70 characters",
                        "Make H1 descriptive and compelling",
                    ],
                )
            )

        if metrics.get("h2_count", 0) < 2:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.SEO,
                    priority="medium",
                    title="Add Subheadings",
                    description="Use H2 and H3 tags to structure content.",
                    current_state=f"Only {metrics['h2_count']} H2 tags found",
                    target_state="At least 3-5 H2 tags for longer content",
                    expected_impact=10.0,
                    examples=[
                        "Use H2 for main sections",
                        "Use H3 for subsections",
                        "Include keywords in subheadings",
                    ],
                )
            )

        if metrics.get("total_links", 0) < 2:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.SEO,
                    priority="medium",
                    title="Add Internal and External Links",
                    description="Include relevant links to improve SEO and user experience.",
                    current_state=f"Only {metrics['total_links']} links found",
                    target_state="3-5 relevant links per article",
                    expected_impact=8.0,
                    examples=[
                        "Link to related articles on your site",
                        "Reference authoritative external sources",
                        "Use descriptive anchor text",
                    ],
                )
            )

        if not metrics.get("has_meta_description", False):
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.SEO,
                    priority="high",
                    title="Add Meta Description",
                    description="Include a compelling meta description for search engines.",
                    current_state="No meta description found",
                    target_state="Meta description of 150-160 characters",
                    expected_impact=12.0,
                    examples=[
                        "Include primary keyword",
                        "Make it compelling and click-worthy",
                        "Keep it under 160 characters",
                    ],
                )
            )

        if metrics.get("alt_text_ratio", 1.0) < 1.0:
            suggestions.append(
                ImprovementSuggestion(
                    id=str(uuid.uuid4()),
                    dimension=ScoreDimension.SEO,
                    priority="medium",
                    title="Add Alt Text to Images",
                    description="Describe all images with descriptive alt text.",
                    current_state=f"Alt text ratio: {metrics['alt_text_ratio']:.1%}",
                    target_state="100% of images have alt text",
                    expected_impact=6.0,
                    examples=[
                        "Describe the image content",
                        "Include relevant keywords naturally",
                        "Keep alt text concise",
                    ],
                )
            )

        return suggestions

    async def score(
        self, content: str, dimension_scores: list[DimensionScore] | None = None, **kwargs: Any
    ) -> AgentResult[ImprovementPlan]:
        """Generate improvement suggestions based on dimension scores.

        Args:
            content: The original content text.
            dimension_scores: List of dimension scores to base suggestions on.
            **kwargs: Additional keyword arguments.

        Returns:
            AgentResult containing ImprovementPlan.
        """
        try:
            if not dimension_scores:
                return AgentResult(
                    success=False,
                    error="Dimension scores are required for improvement suggestions",
                )

            all_suggestions: list[ImprovementSuggestion] = []

            for dim_score in dimension_scores:
                if dim_score.dimension == ScoreDimension.READABILITY:
                    all_suggestions.extend(self._generate_readability_suggestions(dim_score))
                elif dim_score.dimension == ScoreDimension.ORIGINALITY:
                    all_suggestions.extend(self._generate_originality_suggestions(dim_score))
                elif dim_score.dimension == ScoreDimension.ENGAGEMENT:
                    all_suggestions.extend(self._generate_engagement_suggestions(dim_score))
                elif dim_score.dimension == ScoreDimension.SEO:
                    all_suggestions.extend(self._generate_seo_suggestions(dim_score))

            # Sort by priority and expected impact
            priority_order = {"high": 0, "medium": 1, "low": 2}
            all_suggestions.sort(
                key=lambda s: (priority_order.get(s.priority, 3), -s.expected_impact)
            )

            total_expected = sum(s.expected_impact for s in all_suggestions)

            plan = ImprovementPlan(
                id=str(uuid.uuid4()),
                score_id=kwargs.get("score_id", str(uuid.uuid4())),
                suggestions=all_suggestions,
                total_expected_improvement=round(total_expected, 2),
            )

            return AgentResult(success=True, data=plan)

        except Exception as exc:
            logger.exception("Improvement suggestion generation failed")
            return AgentResult(success=False, error=str(exc))
