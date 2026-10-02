"""Next Best Action agent for recommending optimal outreach actions."""

from __future__ import annotations

import time
from datetime import UTC
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from lead_scorer.agents.qualification import QualificationResult, QualificationStatus
from lead_scorer.agents.scoring import LeadGrade, ScoringResult

logger = structlog.get_logger(__name__)


class ActionType(StrEnum):
    """Types of recommended actions."""

    EMAIL = "email"
    PHONE_CALL = "phone_call"
    LINKEDIN = "linkedin"
    DEMO = "demo"
    MEETING = "meeting"
    CONTENT_SEND = "content_send"
    WAIT = "wait"
    DISQUALIFY = "disqualify"


class ActionPriority(StrEnum):
    """Action priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendedAction(BaseModel):
    """A single recommended action."""

    action_type: ActionType
    priority: ActionPriority
    title: str
    description: str
    expected_outcome: str = ""
    timing: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class NextBestActionResult(BaseModel):
    """Result from the next best action agent."""

    lead_id: str
    primary_action: RecommendedAction
    alternative_actions: list[RecommendedAction] = Field(default_factory=list)
    reasoning: str = ""
    generated_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class NextBestActionAgent:
    """Agent responsible for recommending the next best action.

    Uses scoring and qualification results to determine the optimal
    outreach action for a lead.
    """

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 1) -> None:
        """Initialize the next best action agent.

        Args:
            timeout_seconds: Maximum time allowed for recommendation.
            max_retries: Number of retry attempts on failure.
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def recommend(
        self,
        lead_id: str,
        scoring_result: ScoringResult | None = None,
        qualification_result: QualificationResult | None = None,
        **kwargs: Any,
    ) -> NextBestActionResult:
        """Recommend the next best action for a lead.

        Args:
            lead_id: Unique identifier for the lead.
            scoring_result: Optional scoring result.
            qualification_result: Optional qualification result.
            **kwargs: Additional context.

        Returns:
            NextBestActionResult with primary and alternative actions.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If recommendation exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("recommending_action", lead_id=lead_id)
        start_time = time.monotonic()

        try:
            primary, alternatives, reasoning = self._determine_actions(
                scoring_result, qualification_result
            )

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Recommendation timed out after {elapsed:.1f}s")

            from datetime import datetime

            result = NextBestActionResult(
                lead_id=lead_id,
                primary_action=primary,
                alternative_actions=alternatives,
                reasoning=reasoning,
                generated_at=datetime.now(UTC).isoformat(),
                metadata={"elapsed_seconds": elapsed},
            )

            logger.info(
                "action_recommended",
                lead_id=lead_id,
                action=primary.action_type.value,
                priority=primary.priority.value,
            )
            return result

        except Exception as exc:
            logger.error("recommendation_failed", lead_id=lead_id, error=str(exc))
            raise

    def _determine_actions(
        self,
        scoring_result: ScoringResult | None,
        qualification_result: QualificationResult | None,
    ) -> tuple[RecommendedAction, list[RecommendedAction], str]:
        """Determine primary and alternative actions."""
        grade = scoring_result.grade if scoring_result else None
        qual_status = qualification_result.status if qualification_result else None

        if grade == LeadGrade.HOT and qual_status == QualificationStatus.QUALIFIED:
            primary = RecommendedAction(
                action_type=ActionType.DEMO,
                priority=ActionPriority.HIGH,
                title="Schedule Product Demo",
                description="Lead is hot and qualified. Schedule a personalized demo.",
                expected_outcome="Demo completed within 3 days",
                timing="Within 24 hours",
            )
            alternatives = [
                RecommendedAction(
                    action_type=ActionType.MEETING,
                    priority=ActionPriority.MEDIUM,
                    title="Book Discovery Call",
                    description="Offer a discovery call as an alternative to demo.",
                    expected_outcome="Call booked within 2 days",
                ),
                RecommendedAction(
                    action_type=ActionType.CONTENT_SEND,
                    priority=ActionPriority.LOW,
                    title="Send Case Study",
                    description="Share relevant case study to build credibility.",
                    expected_outcome="Content engagement within 1 week",
                ),
            ]
            reasoning = "Hot qualified lead — prioritize demo scheduling"

        elif grade == LeadGrade.HOT:
            primary = RecommendedAction(
                action_type=ActionType.PHONE_CALL,
                priority=ActionPriority.HIGH,
                title="Qualification Call",
                description="Hot lead needs qualification. Call to assess BANT/MEDDIC.",
                expected_outcome="Qualification completed within 2 days",
                timing="Within 24 hours",
            )
            alternatives = [
                RecommendedAction(
                    action_type=ActionType.EMAIL,
                    priority=ActionPriority.MEDIUM,
                    title="Send Qualification Questionnaire",
                    description="Email a qualification form if call not answered.",
                    expected_outcome="Form returned within 3 days",
                ),
            ]
            reasoning = "Hot lead but not yet qualified — prioritize qualification"

        elif grade == LeadGrade.WARM:
            primary = RecommendedAction(
                action_type=ActionType.EMAIL,
                priority=ActionPriority.MEDIUM,
                title="Nurture Email Sequence",
                description="Warm lead — enroll in nurture campaign with valuable content.",
                expected_outcome="Engagement within 1 week",
                timing="Immediate",
            )
            alternatives = [
                RecommendedAction(
                    action_type=ActionType.LINKEDIN,
                    priority=ActionPriority.MEDIUM,
                    title="LinkedIn Engagement",
                    description="Connect and engage on LinkedIn.",
                    expected_outcome="Connection accepted within 3 days",
                ),
                RecommendedAction(
                    action_type=ActionType.CONTENT_SEND,
                    priority=ActionPriority.LOW,
                    title="Send Whitepaper",
                    description="Share educational content to build trust.",
                    expected_outcome="Download within 1 week",
                ),
            ]
            reasoning = "Warm lead — nurture with content and engagement"

        elif grade == LeadGrade.COLD:
            primary = RecommendedAction(
                action_type=ActionType.WAIT,
                priority=ActionPriority.LOW,
                title="Add to Long-term Nurture",
                description="Cold lead — add to quarterly newsletter and revisit later.",
                expected_outcome="Re-evaluate in 90 days",
                timing="Next quarter",
            )
            alternatives = [
                RecommendedAction(
                    action_type=ActionType.CONTENT_SEND,
                    priority=ActionPriority.LOW,
                    title="Send Educational Content",
                    description="Share blog posts or industry reports.",
                    expected_outcome="Low engagement expected",
                ),
            ]
            reasoning = "Cold lead — minimal investment, long-term nurture"

        else:
            primary = RecommendedAction(
                action_type=ActionType.WAIT,
                priority=ActionPriority.LOW,
                title="Gather More Data",
                description="Insufficient data to recommend action. Collect more signals.",
                expected_outcome="Re-score in 2 weeks",
                timing="2 weeks",
            )
            alternatives = []
            reasoning = "Insufficient data — collect more signals before acting"

        return primary, alternatives, reasoning
