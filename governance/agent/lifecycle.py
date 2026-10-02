"""Agent lifecycle state machine.

Manages the complete lifecycle of an AI agent from provisioning through
decommissioning, with state transitions, guards, and hooks.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LifecycleError(Exception):
    """Base exception for lifecycle operations."""


class InvalidTransitionError(LifecycleError):
    """Raised when an invalid state transition is attempted."""


class LifecycleState(str, Enum):
    """Agent lifecycle states."""

    PROVISIONING = "provisioning"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ROTATING = "rotating"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DECOMMISSIONING = "decommissioning"
    DECOMMISSIONED = "decommissioned"
    ARCHIVED = "archived"


@dataclass
class TransitionRecord:
    """Record of a lifecycle state transition."""

    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: float
    reason: str
    actor: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentLifecycle:
    """Lifecycle state machine for an AI agent.

    Enforces valid state transitions, maintains transition history,
    and supports hooks for state entry/exit actions.
    """

    VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
        LifecycleState.PROVISIONING: {
            LifecycleState.PENDING_APPROVAL,
            LifecycleState.DECOMMISSIONED,
        },
        LifecycleState.PENDING_APPROVAL: {
            LifecycleState.ACTIVE,
            LifecycleState.DECOMMISSIONED,
        },
        LifecycleState.ACTIVE: {
            LifecycleState.SUSPENDED,
            LifecycleState.ROTATING,
            LifecycleState.DEGRADED,
            LifecycleState.MAINTENANCE,
            LifecycleState.DECOMMISSIONING,
        },
        LifecycleState.SUSPENDED: {
            LifecycleState.ACTIVE,
            LifecycleState.DECOMMISSIONING,
        },
        LifecycleState.ROTATING: {
            LifecycleState.ACTIVE,
            LifecycleState.DEGRADED,
        },
        LifecycleState.DEGRADED: {
            LifecycleState.ACTIVE,
            LifecycleState.MAINTENANCE,
            LifecycleState.DECOMMISSIONING,
        },
        LifecycleState.MAINTENANCE: {
            LifecycleState.ACTIVE,
            LifecycleState.DECOMMISSIONING,
        },
        LifecycleState.DECOMMISSIONING: {
            LifecycleState.DECOMMISSIONED,
        },
        LifecycleState.DECOMMISSIONED: {
            LifecycleState.ARCHIVED,
        },
        LifecycleState.ARCHIVED: set(),
    }

    def __init__(
        self,
        agent_id: str,
        initial_state: LifecycleState = LifecycleState.PROVISIONING,
    ) -> None:
        """Initialize the lifecycle state machine.

        Args:
            agent_id: The agent identifier.
            initial_state: Starting lifecycle state.
        """
        self._agent_id = agent_id
        self._state = initial_state
        self._history: List[TransitionRecord] = []
        self._entry_hooks: Dict[
            LifecycleState, List[Callable[[str], None]]
        ] = {}
        self._exit_hooks: Dict[
            LifecycleState, List[Callable[[str], None]]
        ] = {}
        self._transition_hooks: List[
            Callable[[TransitionRecord], None]
        ] = []
        self._state_entered_at: Dict[LifecycleState, float] = {
            initial_state: time.time()
        }
        self._metadata: Dict[str, Any] = {}

    @property
    def agent_id(self) -> str:
        """Get the agent identifier."""
        return self._agent_id

    @property
    def state(self) -> LifecycleState:
        """Get the current lifecycle state."""
        return self._state

    @property
    def history(self) -> List[TransitionRecord]:
        """Get the transition history."""
        return list(self._history)

    @property
    def state_duration(self) -> float:
        """Get the duration in the current state (seconds)."""
        entered = self._state_entered_at.get(self._state, time.time())
        return time.time() - entered

    @property
    def is_active(self) -> bool:
        """Check if the agent is in an active state."""
        return self._state == LifecycleState.ACTIVE

    @property
    def is_terminal(self) -> bool:
        """Check if the agent is in a terminal state."""
        return self._state in {
            LifecycleState.DECOMMISSIONED,
            LifecycleState.ARCHIVED,
        }

    def can_transition_to(self, target: LifecycleState) -> bool:
        """Check if a transition to the target state is valid.

        Args:
            target: The target lifecycle state.

        Returns:
            True if the transition is valid.
        """
        return target in self.VALID_TRANSITIONS.get(self._state, set())

    def transition(
        self,
        target: LifecycleState,
        reason: str = "",
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TransitionRecord:
        """Transition to a new lifecycle state.

        Args:
            target: The target lifecycle state.
            reason: Reason for the transition.
            actor: Who initiated the transition.
            metadata: Optional metadata.

        Returns:
            The transition record.

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        if not self.can_transition_to(target):
            raise InvalidTransitionError(
                f"Cannot transition from {self._state.value} to {target.value}"
            )

        old_state = self._state
        record = TransitionRecord(
            from_state=old_state,
            to_state=target,
            timestamp=time.time(),
            reason=reason,
            actor=actor,
            metadata=metadata or {},
        )

        # Execute exit hooks
        self._execute_hooks(self._exit_hooks.get(old_state, []), old_state)

        # Perform transition
        self._state = target
        self._state_entered_at[target] = time.time()
        self._history.append(record)

        # Execute entry hooks
        self._execute_hooks(self._entry_hooks.get(target, []), target)

        # Execute transition hooks
        for hook in self._transition_hooks:
            try:
                hook(record)
            except Exception as exc:
                logger.warning("Transition hook failed: %s", exc)

        logger.info(
            "Agent %s transitioned %s -> %s (reason: %s, actor: %s)",
            self._agent_id,
            old_state.value,
            target.value,
            reason,
            actor,
        )
        return record

    def _execute_hooks(
        self, hooks: List[Callable[[str], None]], state: LifecycleState
    ) -> None:
        """Execute hooks for a state."""
        for hook in hooks:
            try:
                hook(self._agent_id)
            except Exception as exc:
                logger.warning("Hook failed for state %s: %s", state.value, exc)

    def on_enter(
        self, state: LifecycleState, hook: Callable[[str], None]
    ) -> None:
        """Register an entry hook for a state.

        Args:
            state: The lifecycle state.
            hook: Callable to invoke on entry.
        """
        self._entry_hooks.setdefault(state, []).append(hook)

    def on_exit(
        self, state: LifecycleState, hook: Callable[[str], None]
    ) -> None:
        """Register an exit hook for a state.

        Args:
            state: The lifecycle state.
            hook: Callable to invoke on exit.
        """
        self._exit_hooks.setdefault(state, []).append(hook)

    def on_transition(
        self, hook: Callable[[TransitionRecord], None]
    ) -> None:
        """Register a transition hook.

        Args:
            hook: Callable to invoke on every transition.
        """
        self._transition_hooks.append(hook)

    def get_state_timeline(self) -> List[Dict[str, Any]]:
        """Get a timeline of state durations.

        Returns:
            List of state duration records.
        """
        timeline: List[Dict[str, Any]] = []
        for record in self._history:
            duration = 0.0
            for next_record in self._history:
                if next_record.from_state == record.to_state:
                    duration = next_record.timestamp - record.timestamp
                    break
            else:
                if record.to_state == self._state:
                    duration = time.time() - record.timestamp
            timeline.append(
                {
                    "state": record.to_state.value,
                    "entered_at": record.timestamp,
                    "duration_seconds": duration,
                    "reason": record.reason,
                    "actor": record.actor,
                }
            )
        return timeline

    def to_dict(self) -> Dict[str, Any]:
        """Serialize lifecycle to dictionary."""
        return {
            "agent_id": self._agent_id,
            "state": self._state.value,
            "is_active": self.is_active,
            "is_terminal": self.is_terminal,
            "state_duration_seconds": self.state_duration,
            "history": [
                {
                    "from_state": r.from_state.value,
                    "to_state": r.to_state.value,
                    "timestamp": r.timestamp,
                    "reason": r.reason,
                    "actor": r.actor,
                    "metadata": r.metadata,
                }
                for r in self._history
            ],
            "metadata": self._metadata,
        }
