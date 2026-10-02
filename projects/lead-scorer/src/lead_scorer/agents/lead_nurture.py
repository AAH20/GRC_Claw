"""Automated lead nurture agent.

Manages nurture sequences, enrolls leads, tracks engagement, and
determines when leads are ready to exit nurture based on score changes
and engagement signals.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from lead_scorer.agents.scoring import LeadGrade
from lead_scorer.models.routing import (
    NurtureCampaign,
    NurtureChannel,
    NurtureEngagementEvent,
    NurtureEnrollment,
    NurtureEnrollmentRequest,
    NurtureSequence,
    NurtureSequenceCreate,
    NurtureStep,
    NurtureStepStatus,
    RouteDestination,
)

logger = structlog.get_logger(__name__)


class NurtureConfig(BaseModel):
    """Configuration for the nurture agent."""

    max_enrollment_days: int = Field(default=90, ge=1, le=365)
    min_steps_before_exit: int = Field(default=2, ge=1, le=10)
    engagement_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    score_improvement_threshold: float = Field(default=15.0, ge=0.0, le=100.0)
    auto_exit_on_hot: bool = True
    auto_exit_on_qualified: bool = True
    send_time_optimization: bool = True
    timezone: str = "UTC"


class NurtureStatus(StrEnum):
    """Nurture enrollment status values."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXITED = "exited"
    CONVERTED = "converted"


class LeadNurtureAgent:
    """Agent responsible for automated lead nurture sequences.

    Enrolls cold/warm leads into nurture sequences, tracks engagement,
    and determines when leads are ready to exit nurture based on
    score improvements and engagement signals.
    """

    def __init__(
        self,
        config: NurtureConfig | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> None:
        """Initialize the nurture agent.

        Args:
            config: Nurture configuration.
            timeout_seconds: Maximum time allowed for nurture operations.
            max_retries: Number of retry attempts on failure.
        """
        self.config = config or NurtureConfig()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._sequences: dict[str, NurtureSequence] = {}
        self._enrollments: dict[str, NurtureEnrollment] = {}
        self._campaigns: dict[str, NurtureCampaign] = {}
        self._engagement_events: list[NurtureEngagementEvent] = []

    @property
    def sequences(self) -> dict[str, NurtureSequence]:
        """Get all nurture sequences."""
        return dict(self._sequences)

    @property
    def enrollments(self) -> dict[str, NurtureEnrollment]:
        """Get all nurture enrollments."""
        return dict(self._enrollments)

    def create_sequence(self, data: NurtureSequenceCreate) -> NurtureSequence:
        """Create a new nurture sequence.

        Args:
            data: Sequence creation data.

        Returns:
            The created NurtureSequence.

        Raises:
            ValueError: If sequence data is invalid.
        """
        if not data.name:
            raise ValueError("Sequence name is required")
        if not data.steps:
            raise ValueError("At least one step is required")

        sequence_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        steps: list[NurtureStep] = []
        for i, step_data in enumerate(data.steps):
            step = NurtureStep(
                id=str(uuid.uuid4()),
                sequence_id=sequence_id,
                order=i,
                channel=NurtureChannel(step_data.get("channel", "email")),
                subject=step_data.get("subject", ""),
                content_template=step_data.get("content_template", ""),
                delay_days=step_data.get("delay_days", i * 3),
                status=NurtureStepStatus.PENDING,
                metadata=step_data.get("metadata", {}),
            )
            steps.append(step)

        sequence = NurtureSequence(
            id=sequence_id,
            name=data.name,
            description=data.description,
            steps=steps,
            target_grade=data.target_grade,
            target_destination=data.target_destination,
            is_active=data.is_active,
            created_at=now,
            updated_at=now,
        )

        self._sequences[sequence_id] = sequence
        logger.info(
            "nurture_sequence_created",
            sequence_id=sequence_id,
            name=data.name,
            step_count=len(steps),
        )
        return sequence

    def get_sequence(self, sequence_id: str) -> NurtureSequence | None:
        """Get a nurture sequence by ID.

        Args:
            sequence_id: The sequence identifier.

        Returns:
            The NurtureSequence if found, None otherwise.
        """
        return self._sequences.get(sequence_id)

    def list_sequences(self, active_only: bool = True) -> list[NurtureSequence]:
        """List all nurture sequences.

        Args:
            active_only: If True, return only active sequences.

        Returns:
            List of NurtureSequence objects.
        """
        sequences = self._sequences.values()
        if active_only:
            sequences = [s for s in sequences if s.is_active]
        return list(sequences)

    def update_sequence(
        self, sequence_id: str, **updates: Any
    ) -> NurtureSequence | None:
        """Update a nurture sequence.

        Args:
            sequence_id: The sequence identifier.
            **updates: Fields to update.

        Returns:
            The updated NurtureSequence, or None if not found.
        """
        sequence = self._sequences.get(sequence_id)
        if not sequence:
            logger.warning("sequence_not_found", sequence_id=sequence_id)
            return None

        update_data = {k: v for k, v in updates.items() if v is not None}
        updated = sequence.model_copy(update=update_data)
        updated.updated_at = datetime.now(UTC).isoformat()
        self._sequences[sequence_id] = updated
        logger.info("nurture_sequence_updated", sequence_id=sequence_id)
        return updated

    def delete_sequence(self, sequence_id: str) -> bool:
        """Delete a nurture sequence.

        Args:
            sequence_id: The sequence identifier.

        Returns:
            True if deleted, False if not found.
        """
        if sequence_id in self._sequences:
            del self._sequences[sequence_id]
            logger.info("nurture_sequence_deleted", sequence_id=sequence_id)
            return True
        return False

    async def enroll(
        self, request: NurtureEnrollmentRequest
    ) -> NurtureEnrollment:
        """Enroll a lead in a nurture sequence.

        Args:
            request: Enrollment request with lead_id and sequence_id.

        Returns:
            The created NurtureEnrollment.

        Raises:
            ValueError: If lead_id or sequence_id is empty, or sequence not found.
        """
        if not request.lead_id:
            raise ValueError("lead_id is required")
        if not request.sequence_id:
            raise ValueError("sequence_id is required")

        sequence = self._sequences.get(request.sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {request.sequence_id} not found")

        enrollment_id = str(uuid.uuid4())
        enrollment = NurtureEnrollment(
            id=enrollment_id,
            lead_id=request.lead_id,
            sequence_id=request.sequence_id,
            current_step=0,
            status=NurtureStatus.ACTIVE,
            metadata=request.metadata,
        )

        self._enrollments[enrollment_id] = enrollment
        logger.info(
            "lead_enrolled_in_nurture",
            enrollment_id=enrollment_id,
            lead_id=request.lead_id,
            sequence_id=request.sequence_id,
            sequence_name=sequence.name,
        )
        return enrollment

    def get_enrollment(self, enrollment_id: str) -> NurtureEnrollment | None:
        """Get an enrollment by ID.

        Args:
            enrollment_id: The enrollment identifier.

        Returns:
            The NurtureEnrollment if found, None otherwise.
        """
        return self._enrollments.get(enrollment_id)

    def get_lead_enrollments(self, lead_id: str) -> list[NurtureEnrollment]:
        """Get all enrollments for a lead.

        Args:
            lead_id: The lead identifier.

        Returns:
            List of NurtureEnrollment objects for the lead.
        """
        return [e for e in self._enrollments.values() if e.lead_id == lead_id]

    async def process_engagement(
        self,
        enrollment_id: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> NurtureEngagementEvent:
        """Process an engagement event for an enrolled lead.

        Args:
            enrollment_id: The enrollment identifier.
            event_type: Type of engagement event.
            metadata: Optional event metadata.

        Returns:
            The created NurtureEngagementEvent.

        Raises:
            ValueError: If enrollment not found.
        """
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")

        event = NurtureEngagementEvent(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment_id,
            lead_id=enrollment.lead_id,
            step_id="",
            event_type=event_type,
            metadata=metadata or {},
        )

        self._engagement_events.append(event)
        enrollment.last_activity_at = event.timestamp

        # Update step status based on event type
        sequence = self._sequences.get(enrollment.sequence_id)
        if sequence and enrollment.current_step < len(sequence.steps):
            step = sequence.steps[enrollment.current_step]
            if event_type == "sent":
                step.status = NurtureStepStatus.SENT
                step.sent_at = event.timestamp
            elif event_type == "delivered":
                step.status = NurtureStepStatus.DELIVERED
            elif event_type == "opened":
                step.status = NurtureStepStatus.OPENED
                step.opened_at = event.timestamp
            elif event_type == "clicked":
                step.status = NurtureStepStatus.CLICKED
                step.clicked_at = event.timestamp
            elif event_type == "responded":
                step.status = NurtureStepStatus.RESPONDED
                step.responded_at = event.timestamp
            elif event_type == "bounced":
                step.status = NurtureStepStatus.BOUNCED
            elif event_type == "unsubscribed":
                step.status = NurtureStepStatus.UNSUBSCRIBED

        logger.info(
            "nurture_engagement_processed",
            enrollment_id=enrollment_id,
            lead_id=enrollment.lead_id,
            event_type=event_type,
        )
        return event

    async def advance_step(self, enrollment_id: str) -> NurtureEnrollment | None:
        """Advance an enrollment to the next step in its sequence.

        Args:
            enrollment_id: The enrollment identifier.

        Returns:
            The updated NurtureEnrollment, or None if not found or completed.
        """
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment:
            return None

        sequence = self._sequences.get(enrollment.sequence_id)
        if not sequence:
            return None

        next_step = enrollment.current_step + 1
        if next_step >= len(sequence.steps):
            enrollment.status = NurtureStatus.COMPLETED
            enrollment.completed_at = datetime.now(UTC).isoformat()
            logger.info(
                "nurture_sequence_completed",
                enrollment_id=enrollment_id,
                lead_id=enrollment.lead_id,
            )
            return enrollment

        enrollment.current_step = next_step
        logger.info(
            "nurture_step_advanced",
            enrollment_id=enrollment_id,
            lead_id=enrollment.lead_id,
            new_step=next_step,
        )
        return enrollment

    async def evaluate_exit(
        self,
        enrollment_id: str,
        current_score: float | None = None,
        current_grade: LeadGrade | None = None,
        qualification_status: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate whether a lead should exit nurture.

        Args:
            enrollment_id: The enrollment identifier.
            current_score: Current lead score.
            current_grade: Current lead grade.
            qualification_status: Current qualification status.

        Returns:
            Dictionary with exit decision and reason.

        Raises:
            ValueError: If enrollment not found.
        """
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found")

        sequence = self._sequences.get(enrollment.sequence_id)
        if not sequence:
            return {"should_exit": False, "reason": "Sequence not found"}

        # Check minimum steps completed
        if enrollment.current_step < self.config.min_steps_before_exit:
            return {
                "should_exit": False,
                "reason": f"Minimum {self.config.min_steps_before_exit} steps required",
            }

        # Check max enrollment days
        enrolled_at = datetime.fromisoformat(enrollment.enrolled_at)
        days_enrolled = (datetime.now(UTC) - enrolled_at).days
        if days_enrolled > self.config.max_enrollment_days:
            enrollment.status = NurtureStatus.EXITED
            return {
                "should_exit": True,
                "reason": (
                    f"Max enrollment period "
                    f"({self.config.max_enrollment_days} days) exceeded"
                ),
                "destination": RouteDestination.MARKETING,
            }

        # Check if lead became hot
        if self.config.auto_exit_on_hot and current_grade == LeadGrade.HOT:
            enrollment.status = NurtureStatus.EXITED
            return {
                "should_exit": True,
                "reason": "Lead became hot — exit to sales",
                "destination": RouteDestination.SALES,
            }

        # Check if lead became qualified
        if (
            self.config.auto_exit_on_qualified
            and qualification_status == "qualified"
        ):
            enrollment.status = NurtureStatus.EXITED
            return {
                "should_exit": True,
                "reason": "Lead qualified — exit to sales",
                "destination": RouteDestination.SALES_DEVELOPMENT,
            }

        # Check score improvement
        if current_score is not None:
            # Get initial score from enrollment metadata
            initial_score = enrollment.metadata.get("initial_score", 0.0)
            improvement = current_score - initial_score
            if improvement >= self.config.score_improvement_threshold:
                enrollment.status = NurtureStatus.EXITED
                return {
                    "should_exit": True,
                    "reason": f"Score improved by {improvement:.1f} points",
                    "destination": RouteDestination.SALES_DEVELOPMENT,
                }

        # Check engagement level
        engagement_score = self._compute_engagement_score(enrollment_id)
        if engagement_score >= self.config.engagement_threshold:
            return {
                "should_exit": False,
                "reason": f"High engagement ({engagement_score:.2f}) — continue nurture",
                "engagement_score": engagement_score,
            }

        return {
            "should_exit": False,
            "reason": "Continue nurture — no exit criteria met",
            "engagement_score": engagement_score,
        }

    def _compute_engagement_score(self, enrollment_id: str) -> float:
        """Compute engagement score for an enrollment.

        Args:
            enrollment_id: The enrollment identifier.

        Returns:
            Engagement score between 0.0 and 1.0.
        """
        events = [
            e for e in self._engagement_events if e.enrollment_id == enrollment_id
        ]
        if not events:
            return 0.0

        # Weight different event types
        weights = {
            "sent": 0.0,
            "delivered": 0.1,
            "opened": 0.3,
            "clicked": 0.6,
            "responded": 1.0,
            "bounced": -0.5,
            "unsubscribed": -1.0,
        }

        total = 0.0
        for event in events:
            total += weights.get(event.event_type, 0.0)

        # Normalize to 0-1 range
        return max(0.0, min(total / len(events), 1.0))

    def create_campaign(self, campaign: NurtureCampaign) -> NurtureCampaign:
        """Create a nurture campaign.

        Args:
            campaign: The campaign to create.

        Returns:
            The created NurtureCampaign.
        """
        self._campaigns[campaign.id] = campaign
        logger.info(
            "nurture_campaign_created",
            campaign_id=campaign.id,
            name=campaign.name,
        )
        return campaign

    def get_campaign(self, campaign_id: str) -> NurtureCampaign | None:
        """Get a campaign by ID.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            The NurtureCampaign if found, None otherwise.
        """
        return self._campaigns.get(campaign_id)

    def get_engagement_events(
        self, enrollment_id: str | None = None
    ) -> list[NurtureEngagementEvent]:
        """Get engagement events, optionally filtered by enrollment.

        Args:
            enrollment_id: Optional enrollment identifier to filter by.

        Returns:
            List of NurtureEngagementEvent objects.
        """
        if enrollment_id:
            return [
                e for e in self._engagement_events if e.enrollment_id == enrollment_id
            ]
        return list(self._engagement_events)

    def get_nurture_stats(self) -> dict[str, Any]:
        """Get nurture statistics for monitoring.

        Returns:
            Dictionary with nurture metrics.
        """
        total_enrollments = len(self._enrollments)
        active_enrollments = sum(
            1 for e in self._enrollments.values() if e.status == NurtureStatus.ACTIVE
        )
        completed_enrollments = sum(
            1 for e in self._enrollments.values() if e.status == NurtureStatus.COMPLETED
        )
        exited_enrollments = sum(
            1 for e in self._enrollments.values() if e.status == NurtureStatus.EXITED
        )
        total_events = len(self._engagement_events)

        return {
            "total_sequences": len(self._sequences),
            "total_campaigns": len(self._campaigns),
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "exited_enrollments": exited_enrollments,
            "total_engagement_events": total_events,
        }
