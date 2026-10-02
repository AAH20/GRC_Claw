"""Trajectory testing for validating agent execution paths.

This module provides tools for testing and validating agent trajectories including:
- Step-by-step trajectory validation
- Trajectory comparison and diffing
- Trajectory replay testing
- Trajectory anomaly detection
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TrajectoryStepStatus(Enum):
    """Status of a trajectory step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TrajectoryStep:
    """Represents a single step in an agent trajectory.

    Attributes:
        step_id: Unique identifier for the step.
        action: The action taken at this step.
        observation: The observation/result of the action.
        timestamp: When the step occurred.
        status: Current status of the step.
        metadata: Additional step metadata.
        duration_seconds: How long the step took.
    """

    step_id: str
    action: str
    observation: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    status: TrajectoryStepStatus = TrajectoryStepStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0


@dataclass
class Trajectory:
    """Represents a complete agent trajectory.

    Attributes:
        trajectory_id: Unique identifier for the trajectory.
        steps: List of steps in the trajectory.
        start_time: When the trajectory started.
        end_time: When the trajectory ended.
        metadata: Additional trajectory metadata.
    """

    trajectory_id: str
    steps: list[TrajectoryStep] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Calculate total trajectory duration.

        Returns:
            Total duration in seconds.
        """
        if self.end_time > self.start_time:
            return self.end_time - self.start_time
        return sum(step.duration_seconds for step in self.steps)

    @property
    def step_count(self) -> int:
        """Get the number of steps.

        Returns:
            Number of steps.
        """
        return len(self.steps)

    @property
    def failed_steps(self) -> list[TrajectoryStep]:
        """Get all failed steps.

        Returns:
            List of failed steps.
        """
        return [s for s in self.steps if s.status == TrajectoryStepStatus.FAILED]

    def to_dict(self) -> dict[str, Any]:
        """Convert trajectory to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "trajectory_id": self.trajectory_id,
            "steps": [
                {
                    "step_id": s.step_id,
                    "action": s.action,
                    "observation": s.observation,
                    "timestamp": s.timestamp,
                    "status": s.status.value,
                    "metadata": s.metadata,
                    "duration_seconds": s.duration_seconds,
                }
                for s in self.steps
            ],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
            "duration_seconds": self.duration_seconds,
            "step_count": self.step_count,
        }


class TrajectoryValidator:
    """Validates agent trajectories against expected patterns."""

    def __init__(self) -> None:
        """Initialize TrajectoryValidator."""
        self._rules: list[Callable[[TrajectoryStep], tuple[bool, str]]] = []

    def add_rule(
        self, rule: Callable[[TrajectoryStep], tuple[bool, str]]
    ) -> None:
        """Add a validation rule.

        Args:
            rule: A callable that takes a TrajectoryStep and returns (passed, message).
        """
        self._rules.append(rule)

    def validate_step(self, step: TrajectoryStep) -> tuple[bool, list[str]]:
        """Validate a single step against all rules.

        Args:
            step: The step to validate.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        errors: list[str] = []
        for rule in self._rules:
            passed, message = rule(step)
            if not passed:
                errors.append(message)
        return len(errors) == 0, errors

    def validate_trajectory(self, trajectory: Trajectory) -> tuple[bool, list[str]]:
        """Validate an entire trajectory.

        Args:
            trajectory: The trajectory to validate.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        all_errors: list[str] = []

        for step in trajectory.steps:
            valid, errors = self.validate_step(step)
            if not valid:
                all_errors.extend(
                    [f"Step {step.step_id}: {err}" for err in errors]
                )

        # Check trajectory-level constraints
        if not trajectory.steps:
            all_errors.append("Trajectory has no steps")

        failed_steps = trajectory.failed_steps
        if failed_steps:
            all_errors.append(
                f"Trajectory has {len(failed_steps)} failed step(s): "
                f"{[s.step_id for s in failed_steps]}"
            )

        return len(all_errors) == 0, all_errors


class TrajectoryComparator:
    """Compares two trajectories for equality or similarity."""

    def __init__(self, ignore_timestamps: bool = True) -> None:
        """Initialize TrajectoryComparator.

        Args:
            ignore_timestamps: Whether to ignore timestamp differences.
        """
        self.ignore_timestamps = ignore_timestamps

    def compare(
        self, expected: Trajectory, actual: Trajectory
    ) -> tuple[bool, list[str]]:
        """Compare two trajectories.

        Args:
            expected: The expected trajectory.
            actual: The actual trajectory.

        Returns:
            Tuple of (matches, list_of_differences).
        """
        differences: list[str] = []

        if expected.step_count != actual.step_count:
            differences.append(
                f"Step count mismatch: expected {expected.step_count}, "
                f"got {actual.step_count}"
            )

        for i, (exp_step, act_step) in enumerate(
            zip(expected.steps, actual.steps)
        ):
            if exp_step.action != act_step.action:
                differences.append(
                    f"Step {i}: action mismatch: "
                    f"expected '{exp_step.action}', got '{act_step.action}'"
                )

            if exp_step.status != act_step.status:
                differences.append(
                    f"Step {i}: status mismatch: "
                    f"expected {exp_step.status.value}, got {act_step.status.value}"
                )

            if not self.ignore_timestamps:
                if abs(exp_step.timestamp - act_step.timestamp) > 1.0:
                    differences.append(
                        f"Step {i}: timestamp mismatch: "
                        f"expected {exp_step.timestamp}, got {act_step.timestamp}"
                    )

        return len(differences) == 0, differences

    def compute_similarity(
        self, expected: Trajectory, actual: Trajectory
    ) -> float:
        """Compute similarity score between two trajectories.

        Args:
            expected: The expected trajectory.
            actual: The actual trajectory.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        if not expected.steps and not actual.steps:
            return 1.0
        if not expected.steps or not actual.steps:
            return 0.0

        max_steps = max(expected.step_count, actual.step_count)
        matching_steps = 0

        for exp_step, act_step in zip(expected.steps, actual.steps):
            if exp_step.action == act_step.action:
                matching_steps += 1

        return matching_steps / max_steps


class TrajectoryRecorder:
    """Records agent trajectories for later analysis."""

    def __init__(self) -> None:
        """Initialize TrajectoryRecorder."""
        self._trajectories: dict[str, Trajectory] = {}
        self._current_trajectory: Trajectory | None = None

    def start_trajectory(self, trajectory_id: str) -> Trajectory:
        """Start recording a new trajectory.

        Args:
            trajectory_id: Unique identifier for the trajectory.

        Returns:
            The new trajectory object.
        """
        self._current_trajectory = Trajectory(
            trajectory_id=trajectory_id,
            start_time=time.time(),
        )
        return self._current_trajectory

    def record_step(
        self,
        step_id: str,
        action: str,
        observation: dict[str, Any] | None = None,
        status: TrajectoryStepStatus = TrajectoryStepStatus.COMPLETED,
        metadata: dict[str, Any] | None = None,
    ) -> TrajectoryStep:
        """Record a step in the current trajectory.

        Args:
            step_id: Unique identifier for the step.
            action: The action taken.
            observation: The observation/result.
            status: Step status.
            metadata: Additional metadata.

        Returns:
            The recorded step.

        Raises:
            RuntimeError: If no trajectory is currently being recorded.
        """
        if self._current_trajectory is None:
            raise RuntimeError("No trajectory is currently being recorded")

        step = TrajectoryStep(
            step_id=step_id,
            action=action,
            observation=observation or {},
            timestamp=time.time(),
            status=status,
            metadata=metadata or {},
        )
        self._current_trajectory.steps.append(step)
        return step

    def end_trajectory(self) -> Trajectory:
        """End the current trajectory.

        Returns:
            The completed trajectory.

        Raises:
            RuntimeError: If no trajectory is currently being recorded.
        """
        if self._current_trajectory is None:
            raise RuntimeError("No trajectory is currently being recorded")

        self._current_trajectory.end_time = time.time()
        trajectory = self._current_trajectory
        self._trajectories[trajectory.trajectory_id] = trajectory
        self._current_trajectory = None
        return trajectory

    def get_trajectory(self, trajectory_id: str) -> Trajectory | None:
        """Get a recorded trajectory by ID.

        Args:
            trajectory_id: The trajectory ID.

        Returns:
            The trajectory, or None if not found.
        """
        return self._trajectories.get(trajectory_id)

    def get_all_trajectories(self) -> dict[str, Trajectory]:
        """Get all recorded trajectories.

        Returns:
            Dictionary of trajectory ID to Trajectory.
        """
        return self._trajectories.copy()

    def export_to_json(self, filepath: str) -> None:
        """Export all trajectories to a JSON file.

        Args:
            filepath: Path to the output JSON file.
        """
        data = {
            tid: traj.to_dict() for tid, traj in self._trajectories.items()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


class TrajectoryAnomalyDetector:
    """Detects anomalies in agent trajectories."""

    def __init__(
        self,
        max_step_duration: float = 60.0,
        max_total_duration: float = 300.0,
        max_steps: int = 100,
    ) -> None:
        """Initialize TrajectoryAnomalyDetector.

        Args:
            max_step_duration: Maximum allowed duration for a single step.
            max_total_duration: Maximum allowed total trajectory duration.
            max_steps: Maximum allowed number of steps.
        """
        self.max_step_duration = max_step_duration
        self.max_total_duration = max_total_duration
        self.max_steps = max_steps

    def detect(self, trajectory: Trajectory) -> list[str]:
        """Detect anomalies in a trajectory.

        Args:
            trajectory: The trajectory to analyze.

        Returns:
            List of anomaly descriptions.
        """
        anomalies: list[str] = []

        if trajectory.step_count > self.max_steps:
            anomalies.append(
                f"Too many steps: {trajectory.step_count} "
                f"(max: {self.max_steps})"
            )

        if trajectory.duration_seconds > self.max_total_duration:
            anomalies.append(
                f"Trajectory too long: {trajectory.duration_seconds:.2f}s "
                f"(max: {self.max_total_duration}s)"
            )

        for step in trajectory.steps:
            if step.duration_seconds > self.max_step_duration:
                anomalies.append(
                    f"Step {step.step_id} too long: "
                    f"{step.duration_seconds:.2f}s "
                    f"(max: {self.max_step_duration}s)"
                )

            if step.status == TrajectoryStepStatus.FAILED:
                anomalies.append(f"Step {step.step_id} failed")

        return anomalies
