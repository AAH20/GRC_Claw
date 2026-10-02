"""Availability Optimizer Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from interview_scheduler.models.interview import Interview
from interview_scheduler.models.timeslot import TimeSlot, SlotStatus

logger = logging.getLogger(__name__)


class AvailabilityOptimizerAgent:
    """Agent responsible for finding optimal time slots.

    Uses LangChain DeepAgents to intelligently score and rank available
    time slots based on participant preferences, business hours, and
    scheduling constraints.
    """

    def __init__(
        self,
        business_hours_start: int = 9,
        business_hours_end: int = 17,
        slot_interval_minutes: int = 30,
    ) -> None:
        """Initialize the Availability Optimizer Agent.

        Args:
            business_hours_start: Business start hour.
            business_hours_end: Business end hour.
            slot_interval_minutes: Interval between candidate slots.
        """
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end
        self.slot_interval_minutes = slot_interval_minutes
        self._agent: Any = None

    async def _get_agent(self) -> Any:
        """Lazy-initialize the LangChain DeepAgent."""
        if self._agent is None:
            try:
                from langchain_deepagents import create_deep_agent

                self._agent = create_deep_agent(
                    tools=[self._score_slot_tool, self._filter_business_hours_tool],
                    instructions=(
                        "You are an availability optimization agent. Find the best "
                        "time slots for interviews based on participant availability, "
                        "business hours, and preferences."
                    ),
                )
            except ImportError:
                logger.warning("langchain-deepagents not available, using direct optimization")
                self._agent = None
        return self._agent

    async def _score_slot_tool(
        self, slot: TimeSlot, preferences: dict[str, Any]
    ) -> float:
        """Tool for scoring a time slot."""
        return self.score_slot(slot, preferences)

    async def _filter_business_hours_tool(
        self, slots: list[TimeSlot], start_hour: int, end_hour: int
    ) -> list[TimeSlot]:
        """Tool for filtering slots within business hours."""
        return self.filter_business_hours(slots, start_hour, end_hour)

    def generate_candidate_slots(
        self,
        start: datetime,
        end: datetime,
        duration_minutes: int,
    ) -> list[TimeSlot]:
        """Generate candidate time slots within a range.

        Args:
            start: Start of the search window.
            end: End of the search window.
            duration_minutes: Required slot duration.

        Returns:
            List of candidate time slots.
        """
        slots: list[TimeSlot] = []
        current = start
        while current + timedelta(minutes=duration_minutes) <= end:
            slots.append(
                TimeSlot(
                    start_time=current,
                    end_time=current + timedelta(minutes=duration_minutes),
                    status=SlotStatus.AVAILABLE,
                )
            )
            current += timedelta(minutes=self.slot_interval_minutes)
        return slots

    def filter_business_hours(
        self,
        slots: list[TimeSlot],
        start_hour: int | None = None,
        end_hour: int | None = None,
    ) -> list[TimeSlot]:
        """Filter slots to only those within business hours.

        Args:
            slots: Slots to filter.
            start_hour: Business start hour (defaults to agent config).
            end_hour: Business end hour (defaults to agent config).

        Returns:
            Filtered list of slots.
        """
        start_h = start_hour or self.business_hours_start
        end_h = end_hour or self.business_hours_end
        return [
            slot for slot in slots
            if slot.start_time.hour >= start_h and slot.end_time.hour <= end_h
        ]

    def score_slot(
        self,
        slot: TimeSlot,
        preferences: dict[str, Any] | None = None,
    ) -> float:
        """Score a time slot based on preferences.

        Args:
            slot: The time slot to score.
            preferences: Optional scoring preferences.

        Returns:
            Score between 0.0 and 1.0.
        """
        score = 0.5  # Base score
        prefs = preferences or {}

        # Prefer mid-morning slots (10-12)
        if 10 <= slot.start_time.hour <= 12:
            score += 0.2

        # Prefer slots not too early or too late
        if 9 <= slot.start_time.hour <= 16:
            score += 0.1

        # Penalize lunch hours (12-13)
        if 12 <= slot.start_time.hour <= 13:
            score -= 0.1

        # Prefer earlier slots in the search window
        if "search_start" in prefs:
            search_start = prefs["search_start"]
            if isinstance(search_start, str):
                search_start = datetime.fromisoformat(search_start)
            hours_from_start = (slot.start_time - search_start).total_seconds() / 3600
            if hours_from_start < 24:
                score += 0.1

        # Prefer slots on preferred days
        if "preferred_days" in prefs:
            preferred_days = prefs["preferred_days"]
            if slot.start_time.weekday() in preferred_days:
                score += 0.1

        return max(0.0, min(1.0, score))

    def find_optimal_slots(
        self,
        candidate_slots: list[TimeSlot],
        busy_slots: list[TimeSlot],
        duration_minutes: int,
        max_results: int = 10,
        preferences: dict[str, Any] | None = None,
    ) -> list[TimeSlot]:
        """Find the optimal available time slots.

        Args:
            candidate_slots: All candidate slots.
            busy_slots: Busy slots to exclude.
            duration_minutes: Required duration.
            max_results: Maximum number of results.
            preferences: Optional scoring preferences.

        Returns:
            List of optimal time slots sorted by score.
        """
        # Filter out busy slots
        available: list[TimeSlot] = []
        for slot in candidate_slots:
            is_busy = False
            for busy in busy_slots:
                if slot.start_time < busy.end_time and busy.start_time < slot.end_time:
                    is_busy = True
                    break
            if not is_busy:
                available.append(slot)

        # Score and sort
        scored_slots: list[tuple[float, TimeSlot]] = []
        for slot in available:
            score = self.score_slot(slot, preferences)
            scored_slots.append((score, slot))

        scored_slots.sort(key=lambda x: x[0], reverse=True)

        # Return top results
        result: list[TimeSlot] = []
        for score, slot in scored_slots[:max_results]:
            slot.score = score
            result.append(slot)
        return result

    def optimize_for_participants(
        self,
        participant_slots: dict[str, list[TimeSlot]],
        duration_minutes: int,
        max_results: int = 10,
    ) -> list[TimeSlot]:
        """Find optimal slots that work for all participants.

        Args:
            participant_slots: Map of participant ID to their busy slots.
            duration_minutes: Required duration.
            max_results: Maximum number of results.

        Returns:
            List of optimal common time slots.
        """
        if not participant_slots:
            return []

        # Find common free windows
        all_busy: list[TimeSlot] = []
        for slots in participant_slots.values():
            all_busy.extend(slots)

        if not all_busy:
            return []

        # Generate candidates across the full range
        earliest_start = min(s.start_time for s in all_busy)
        latest_end = max(s.end_time for s in all_busy)
        candidates = self.generate_candidate_slots(
            earliest_start, latest_end, duration_minutes
        )

        return self.find_optimal_slots(candidates, all_busy, duration_minutes, max_results)
