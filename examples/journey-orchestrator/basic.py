"""
Basic Journey Orchestration Example
===================================

Demonstrates core journey orchestration functionality including:
- Customer journey definition and configuration
- Journey stages and transitions
- Trigger-based journey activation
- Basic journey analytics
- Journey performance tracking

Usage:
    python basic.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JourneyTriggerType(str, Enum):
    """Types of journey triggers."""

    EVENT = "event"
    SCHEDULE = "schedule"
    SEGMENT_ENTRY = "segment_entry"
    SEGMENT_EXIT = "segment_exit"
    SCORE_THRESHOLD = "score_threshold"
    INACTIVITY = "inactivity"


class JourneyStageType(str, Enum):
    """Types of journey stages."""

    START = "start"
    CONDITION = "condition"
    ACTION = "action"
    WAIT = "wait"
    END = "end"


class JourneyStatus(str, Enum):
    """Journey instance statuses."""

    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXITED = "exited"


@dataclass
class JourneyStage:
    """A stage in a customer journey."""

    id: str
    name: str
    stage_type: JourneyStageType
    config: dict[str, Any] = field(default_factory=dict)
    next_stages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class JourneyDefinition:
    """Definition of a customer journey."""

    id: str
    name: str
    description: str
    trigger_type: JourneyTriggerType
    trigger_config: dict[str, Any] = field(default_factory=dict)
    stages: dict[str, JourneyStage] = field(default_factory=dict)
    start_stage_id: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_stage(self, stage: JourneyStage) -> None:
        """Add a stage to the journey.

        Args:
            stage: The stage to add.
        """
        self.stages[stage.id] = stage
        self.updated_at = datetime.now()

    def set_start_stage(self, stage_id: str) -> None:
        """Set the starting stage.

        Args:
            stage_id: ID of the starting stage.
        """
        if stage_id not in self.stages:
            raise ValueError(f"Stage '{stage_id}' not found")
        self.start_stage_id = stage_id

    def validate(self) -> list[str]:
        """Validate the journey definition.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        if not self.start_stage_id:
            errors.append("No start stage defined")
        elif self.start_stage_id not in self.stages:
            errors.append(f"Start stage '{self.start_stage_id}' not found")

        for stage_id, stage in self.stages.items():
            for next_id in stage.next_stages:
                if next_id not in self.stages:
                    errors.append(
                        f"Stage '{stage_id}' references unknown stage '{next_id}'"
                    )

        return errors


@dataclass
class JourneyInstance:
    """An active journey instance for a customer."""

    id: str
    journey_id: str
    customer_id: str
    current_stage_id: str = ""
    status: JourneyStatus = JourneyStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    stage_history: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, stage_id: str) -> None:
        """Transition to a new stage.

        Args:
            stage_id: The stage to transition to.
        """
        now = datetime.now()
        self.stage_history.append({
            "from_stage": self.current_stage_id,
            "to_stage": stage_id,
            "timestamp": now.isoformat(),
        })
        self.current_stage_id = stage_id


class JourneyOrchestrator:
    """Orchestrates customer journeys."""

    def __init__(self) -> None:
        """Initialize the journey orchestrator."""
        self.journeys: dict[str, JourneyDefinition] = {}
        self.instances: dict[str, JourneyInstance] = {}
        self._instance_counter = 0

    def create_journey(
        self,
        name: str,
        description: str,
        trigger_type: JourneyTriggerType,
        trigger_config: dict[str, Any] | None = None,
    ) -> JourneyDefinition:
        """Create a new journey definition.

        Args:
            name: Journey name.
            description: Journey description.
            trigger_type: Type of trigger.
            trigger_config: Trigger configuration.

        Returns:
            The created JourneyDefinition.
        """
        journey_id = f"journey_{len(self.journeys) + 1:04d}"
        journey = JourneyDefinition(
            id=journey_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config=trigger_config or {},
        )
        self.journeys[journey_id] = journey
        logger.info("Created journey '%s' (%s)", name, journey_id)
        return journey

    def start_journey(
        self,
        journey_id: str,
        customer_id: str,
        context: dict[str, Any] | None = None,
    ) -> JourneyInstance:
        """Start a journey for a customer.

        Args:
            journey_id: Journey definition ID.
            customer_id: Customer identifier.
            context: Initial context data.

        Returns:
            The created JourneyInstance.

        Raises:
            ValueError: If journey not found or invalid.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        journey = self.journeys[journey_id]
        errors = journey.validate()
        if errors:
            raise ValueError(f"Journey validation failed: {'; '.join(errors)}")

        self._instance_counter += 1
        instance_id = f"inst_{self._instance_counter:06d}"

        instance = JourneyInstance(
            id=instance_id,
            journey_id=journey_id,
            customer_id=customer_id,
            current_stage_id=journey.start_stage_id,
            status=JourneyStatus.ACTIVE,
            started_at=datetime.now(),
            context=context or {},
        )

        self.instances[instance_id] = instance
        logger.info(
            "Started journey '%s' for customer '%s' (instance: %s)",
            journey.name,
            customer_id,
            instance_id,
        )
        return instance

    def advance_stage(
        self,
        instance_id: str,
        next_stage_id: str | None = None,
    ) -> JourneyInstance:
        """Advance a journey instance to the next stage.

        Args:
            instance_id: Journey instance ID.
            next_stage_id: Specific stage to advance to (None for auto).

        Returns:
            Updated JourneyInstance.

        Raises:
            ValueError: If instance not found.
        """
        if instance_id not in self.instances:
            raise ValueError(f"Instance '{instance_id}' not found")

        instance = self.instances[instance_id]
        journey = self.journeys[instance.journey_id]

        current_stage = journey.stages.get(instance.current_stage_id)
        if current_stage is None:
            raise ValueError(f"Current stage '{instance.current_stage_id}' not found")

        # Determine next stage
        if next_stage_id is None:
            if not current_stage.next_stages:
                # No next stage, complete journey
                instance.status = JourneyStatus.COMPLETED
                instance.completed_at = datetime.now()
                logger.info("Journey instance '%s' completed", instance_id)
                return instance
            next_stage_id = current_stage.next_stages[0]

        if next_stage_id not in journey.stages:
            raise ValueError(f"Next stage '{next_stage_id}' not found")

        instance.transition_to(next_stage_id)
        logger.debug("Instance '%s' advanced to stage '%s'", instance_id, next_stage_id)
        return instance

    def get_journey_analytics(self, journey_id: str) -> dict[str, Any]:
        """Get analytics for a journey.

        Args:
            journey_id: Journey definition ID.

        Returns:
            Analytics dictionary.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        journey = self.journeys[journey_id]
        instances = [
            inst for inst in self.instances.values()
            if inst.journey_id == journey_id
        ]

        total = len(instances)
        active = sum(1 for i in instances if i.status == JourneyStatus.ACTIVE)
        completed = sum(1 for i in instances if i.status == JourneyStatus.COMPLETED)
        exited = sum(1 for i in instances if i.status == JourneyStatus.EXITED)

        # Calculate average completion time
        completion_times = []
        for inst in instances:
            if inst.completed_at and inst.started_at:
                duration = (inst.completed_at - inst.started_at).total_seconds()
                completion_times.append(duration)

        avg_completion_time = (
            sum(completion_times) / len(completion_times) if completion_times else 0
        )

        # Stage distribution
        stage_counts: dict[str, int] = {}
        for inst in instances:
            if inst.current_stage_id:
                stage_counts[inst.current_stage_id] = stage_counts.get(inst.current_stage_id, 0) + 1

        return {
            "journey_id": journey_id,
            "journey_name": journey.name,
            "total_instances": total,
            "active": active,
            "completed": completed,
            "exited": exited,
            "completion_rate": round(completed / total, 4) if total > 0 else 0,
            "avg_completion_time_seconds": round(avg_completion_time, 2),
            "stage_distribution": stage_counts,
        }


def main() -> None:
    """Run the basic journey orchestration example."""
    logger.info("=" * 60)
    logger.info("Basic Journey Orchestration Example")
    logger.info("=" * 60)

    orchestrator = JourneyOrchestrator()

    # Create a welcome journey
    journey = orchestrator.create_journey(
        name="New Customer Welcome",
        description="Welcome journey for new customers",
        trigger_type=JourneyTriggerType.SEGMENT_ENTRY,
        trigger_config={"segment": "new_customers"},
    )

    # Define stages
    start = JourneyStage(
        id="start",
        name="Journey Start",
        stage_type=JourneyStageType.START,
        next_stages=["send_welcome_email"],
    )
    welcome_email = JourneyStage(
        id="send_welcome_email",
        name="Send Welcome Email",
        stage_type=JourneyStageType.ACTION,
        config={"template": "welcome_v1", "channel": "email"},
        next_stages=["wait_3_days"],
    )
    wait_stage = JourneyStage(
        id="wait_3_days",
        name="Wait 3 Days",
        stage_type=JourneyStageType.WAIT,
        config={"duration_hours": 72},
        next_stages=["check_engagement"],
    )
    condition = JourneyStage(
        id="check_engagement",
        name="Check Engagement",
        stage_type=JourneyStageType.CONDITION,
        config={"condition": "email_opened"},
        next_stages=["send_tips_email", "send_reminder_email"],
    )
    tips_email = JourneyStage(
        id="send_tips_email",
        name="Send Tips Email",
        stage_type=JourneyStageType.ACTION,
        config={"template": "tips_v1", "channel": "email"},
        next_stages=["end"],
    )
    reminder_email = JourneyStage(
        id="send_reminder_email",
        name="Send Reminder Email",
        stage_type=JourneyStageType.ACTION,
        config={"template": "reminder_v1", "channel": "email"},
        next_stages=["end"],
    )
    end = JourneyStage(
        id="end",
        name="Journey End",
        stage_type=JourneyStageType.END,
    )

    # Add stages to journey
    for stage in [start, welcome_email, wait_stage, condition, tips_email, reminder_email, end]:
        journey.add_stage(stage)
    journey.set_start_stage("start")

    # Validate journey
    errors = journey.validate()
    if errors:
        logger.error("Journey validation errors: %s", errors)
        return
    logger.info("Journey validated successfully")

    # Start journey instances
    for i in range(5):
        customer_id = f"customer_{i + 1:03d}"
        instance = orchestrator.start_journey(
            journey_id=journey.id,
            customer_id=customer_id,
            context={"email": f"customer{i + 1}@example.com"},
        )

        # Simulate journey progression
        orchestrator.advance_stage(instance.id)  # -> send_welcome_email
        orchestrator.advance_stage(instance.id)  # -> wait_3_days
        orchestrator.advance_stage(instance.id)  # -> check_engagement

        # Branch based on engagement
        if i < 3:
            orchestrator.advance_stage(instance.id, "send_tips_email")
        else:
            orchestrator.advance_stage(instance.id, "send_reminder_email")

        orchestrator.advance_stage(instance.id)  # -> end

    # Get analytics
    analytics = orchestrator.get_journey_analytics(journey.id)
    logger.info("\nJourney Analytics:")
    logger.info("  Total instances: %d", analytics["total_instances"])
    logger.info("  Completed: %d", analytics["completed"])
    logger.info("  Completion rate: %.1f%%", analytics["completion_rate"] * 100)
    logger.info("  Avg completion time: %.1f seconds", analytics["avg_completion_time_seconds"])

    logger.info("\n" + "=" * 60)
    logger.info("Example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
