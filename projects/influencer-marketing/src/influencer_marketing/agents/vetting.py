"""Vetting agent for evaluating influencer quality and brand safety."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.discovery import DiscoveredInfluencer

logger = structlog.get_logger(__name__)


@dataclass
class VettingCriteria:
    """Criteria for influencer vetting."""

    authenticity_threshold: float = 0.7
    brand_safety_check: bool = True
    content_quality_weight: float = 0.3
    audience_quality_weight: float = 0.3
    engagement_quality_weight: float = 0.2
    brand_safety_weight: float = 0.2
    check_fake_followers: bool = True
    check_brand_mentions: bool = True
    excluded_categories: list[str] = field(default_factory=list)


@dataclass
class VettingReport:
    """Comprehensive vetting report for an influencer."""

    influencer: DiscoveredInfluencer
    overall_score: float
    authenticity_score: float
    content_quality_score: float
    audience_quality_score: float
    engagement_quality_score: float
    brand_safety_score: float
    is_approved: bool
    risk_flags: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    detailed_analysis: dict[str, Any] = field(default_factory=dict)


class VettingAgent(BaseAgent[tuple[DiscoveredInfluencer, VettingCriteria], VettingReport]):
    """Agent responsible for vetting and evaluating influencers."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="vetting",
            description="Evaluates influencer quality, authenticity, and brand safety",
            max_retries=3,
            timeout_seconds=180,
        )
        super().__init__(config)

    async def validate_input(
        self, input_data: tuple[DiscoveredInfluencer, VettingCriteria]
    ) -> bool:
        """Validate vetting input."""
        influencer, criteria = input_data
        if influencer is None:
            return False
        if not 0 <= criteria.authenticity_threshold <= 1:
            self.logger.warning("Invalid authenticity threshold")
            return False
        return True

    async def execute(
        self, input_data: tuple[DiscoveredInfluencer, VettingCriteria]
    ) -> AgentResult[VettingReport]:
        """Execute influencer vetting."""
        influencer, criteria = input_data
        self.logger.info("Starting influencer vetting", username=influencer.username)

        try:
            # Run all vetting checks
            authenticity = await self._check_authenticity(influencer, criteria)
            content_quality = await self._assess_content_quality(influencer)
            audience_quality = await self._assess_audience_quality(influencer)
            engagement_quality = await self._assess_engagement_quality(influencer)
            brand_safety = await self._check_brand_safety(influencer, criteria)

            # Calculate weighted overall score
            overall = (
                content_quality * criteria.content_quality_weight
                + audience_quality * criteria.audience_quality_weight
                + engagement_quality * criteria.engagement_quality_weight
                + brand_safety * criteria.brand_safety_weight
            )

            is_approved = (
                overall >= criteria.authenticity_threshold
                and brand_safety >= 0.5
                and authenticity >= 0.5
            )

            risk_flags = self._identify_risk_flags(
                influencer, authenticity, content_quality, audience_quality, brand_safety
            )
            recommendations = self._generate_recommendations(
                influencer, content_quality, audience_quality, engagement_quality
            )

            report = VettingReport(
                influencer=influencer,
                overall_score=round(overall, 3),
                authenticity_score=round(authenticity, 3),
                content_quality_score=round(content_quality, 3),
                audience_quality_score=round(audience_quality, 3),
                engagement_quality_score=round(engagement_quality, 3),
                brand_safety_score=round(brand_safety, 3),
                is_approved=is_approved,
                risk_flags=risk_flags,
                recommendations=recommendations,
            )

            self.logger.info(
                "Vetting completed",
                username=influencer.username,
                overall_score=overall,
                approved=is_approved,
            )
            return AgentResult(success=True, data=report)

        except Exception as exc:
            self.logger.error("Vetting failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    async def _check_authenticity(
        self, influencer: DiscoveredInfluencer, criteria: VettingCriteria
    ) -> float:
        """Check influencer authenticity (fake followers, bot activity)."""
        score = 1.0

        # Follower-to-following ratio check
        if influencer.following_count > 0:
            ratio = influencer.follower_count / influencer.following_count
            if ratio < 0.1:
                score -= 0.3
            elif ratio < 0.5:
                score -= 0.1

        # Engagement rate plausibility
        if influencer.engagement_rate > 0.15:
            score -= 0.2  # Suspiciously high engagement
        elif influencer.engagement_rate < 0.001:
            score -= 0.3  # Suspiciously low engagement

        # Post frequency check
        if influencer.post_count < 10:
            score -= 0.2

        return max(0.0, min(1.0, score))

    async def _assess_content_quality(self, influencer: DiscoveredInfluencer) -> float:
        """Assess the quality of influencer's content."""
        # Placeholder: In production, this would analyze recent posts
        # using computer vision and NLP
        score = 0.7  # Default moderate score
        if influencer.post_count > 100:
            score += 0.1
        if influencer.bio and len(influencer.bio) > 20:
            score += 0.1
        return min(1.0, score)

    async def _assess_audience_quality(self, influencer: DiscoveredInfluencer) -> float:
        """Assess audience quality and demographics."""
        # Placeholder: In production, this would analyze audience demographics
        score = 0.6
        if influencer.follower_count > 10000:
            score += 0.1
        if influencer.follower_count > 100000:
            score += 0.1
        return min(1.0, score)

    async def _assess_engagement_quality(self, influencer: DiscoveredInfluencer) -> float:
        """Assess engagement quality (likes, comments, shares ratio)."""
        score = 0.5
        if 0.01 <= influencer.engagement_rate <= 0.08:
            score += 0.3  # Healthy engagement range
        elif influencer.engagement_rate > 0.08:
            score += 0.1  # Possibly inflated
        return min(1.0, score)

    async def _check_brand_safety(
        self, influencer: DiscoveredInfluencer, criteria: VettingCriteria
    ) -> float:
        """Check brand safety (controversial content, competitor mentions)."""
        score = 1.0
        # Check for excluded categories
        for category in influencer.categories:
            if category.lower() in [c.lower() for c in criteria.excluded_categories]:
                score -= 0.5
        return max(0.0, min(1.0, score))

    def _identify_risk_flags(
        self,
        influencer: DiscoveredInfluencer,
        authenticity: float,
        content_quality: float,
        audience_quality: float,
        brand_safety: float,
    ) -> list[str]:
        """Identify risk flags from vetting scores."""
        flags: list[str] = []
        if authenticity < 0.5:
            flags.append("low_authenticity")
        if content_quality < 0.4:
            flags.append("poor_content_quality")
        if audience_quality < 0.4:
            flags.append("low_audience_quality")
        if brand_safety < 0.5:
            flags.append("brand_safety_concern")
        if influencer.engagement_rate > 0.15:
            flags.append("suspicious_engagement_rate")
        return flags

    def _generate_recommendations(
        self,
        influencer: DiscoveredInfluencer,
        content_quality: float,
        audience_quality: float,
        engagement_quality: float,
    ) -> list[str]:
        """Generate recommendations based on vetting results."""
        recs: list[str] = []
        if content_quality < 0.6:
            recs.append("Request content samples before proceeding")
        if audience_quality < 0.6:
            recs.append("Request audience demographic breakdown")
        if engagement_quality < 0.5:
            recs.append("Negotiate performance-based compensation")
        if not recs:
            recs.append("Influencer meets all criteria - proceed with outreach")
        return recs
