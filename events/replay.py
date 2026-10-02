"""Event replay for reprocessing historical events.

Provides capabilities to replay events from the event store with support for
filtering, batching, rate limiting, and progress tracking.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from .schema import Event, EventStatus

logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """Result of an event replay operation.

    Attributes:
        replay_id: Unique identifier for this replay operation.
        total_events: Total number of events that matched the replay criteria.
        processed_events: Number of events successfully processed.
        failed_events: Number of events that failed processing.
        skipped_events: Number of events skipped (filtered out).
        start_time: When the replay started.
        end_time: When the replay completed (None if still running).
        errors: List of error messages encountered during replay.
    """

    replay_id: str
    total_events: int = 0
    processed_events: int = 0
    failed_events: int = 0
    skipped_events: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if the replay has completed."""
        return self.end_time is not None

    @property
    def duration_seconds(self) -> float:
        """Get the duration of the replay in seconds.

        Returns:
            Duration in seconds, or 0 if the replay hasn't started.
        """
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Get the success rate as a fraction (0.0 to 1.0).

        Returns:
            Success rate, or 0.0 if no events were processed.
        """
        total = self.processed_events + self.failed_events
        if total == 0:
            return 0.0
        return self.processed_events / total


class EventReplayer:
    """Replays historical events from the event store.

    Supports filtering by event type, time range, and custom predicates.
    Events are processed in batches with optional rate limiting.

    Example:
        >>> replayer = EventReplayer(event_store)
        >>> result = await replayer.replay(
        ...     event_types=["campaign.created"],
        ...     handler=my_handler,
        ...     batch_size=100,
        ... )
    """

    def __init__(self, event_store: Any) -> None:
        """Initialize the event replayer.

        Args:
            event_store: The event store to read events from. Must implement
                a `get_events()` method.
        """
        self._event_store = event_store
        self._replay_history: List[ReplayResult] = []

    async def replay(
        self,
        handler: Callable[[Event], Awaitable[None]],
        *,
        event_types: Optional[List[str]] = None,
        after_version: int = 0,
        before_version: Optional[int] = None,
        filter_fn: Optional[Callable[[Event], bool]] = None,
        batch_size: int = 100,
        rate_limit: Optional[float] = None,
        continue_on_error: bool = True,
        replay_id: Optional[str] = None,
    ) -> ReplayResult:
        """Replay events from the store through a handler.

        Args:
            handler: Async callback invoked for each event.
            event_types: If provided, only replay events of these types.
            after_version: Only replay events after this version.
            before_version: Only replay events before this version.
            filter_fn: Optional predicate to filter events.
            batch_size: Number of events to process per batch.
            rate_limit: Minimum seconds between batches (for throttling).
            continue_on_error: If True, continue replay after handler errors.
            replay_id: Optional identifier for this replay operation.

        Returns:
            A ReplayResult with statistics about the replay.
        """
        import uuid

        result = ReplayResult(replay_id=replay_id or str(uuid.uuid4()))
        events = self._event_store.get_events(
            event_types=event_types,
            after_version=after_version,
            before_version=before_version,
        )
        result.total_events = len(events)

        logger.info(
            "Starting replay %s: %d events to process",
            result.replay_id,
            result.total_events,
        )

        for i in range(0, len(events), batch_size):
            batch = events[i : i + batch_size]
            await self._process_batch(
                batch, handler, result, filter_fn, continue_on_error
            )
            if rate_limit and i + batch_size < len(events):
                await asyncio.sleep(rate_limit)

        result.end_time = datetime.now(timezone.utc)
        self._replay_history.append(result)

        logger.info(
            "Replay %s complete: %d processed, %d failed, %d skipped (%.2fs)",
            result.replay_id,
            result.processed_events,
            result.failed_events,
            result.skipped_events,
            result.duration_seconds,
        )
        return result

    async def _process_batch(
        self,
        batch: List[Event],
        handler: Callable[[Event], Awaitable[None]],
        result: ReplayResult,
        filter_fn: Optional[Callable[[Event], bool]],
        continue_on_error: bool,
    ) -> None:
        """Process a batch of events.

        Args:
            batch: The events to process.
            handler: The handler callback.
            result: The ReplayResult to update.
            filter_fn: Optional filter predicate.
            continue_on_error: Whether to continue after errors.
        """
        for event in batch:
            if filter_fn and not filter_fn(event):
                result.skipped_events += 1
                continue

            try:
                await handler(event)
                result.processed_events += 1
            except Exception as exc:
                result.failed_events += 1
                error_msg = f"Event {event.metadata.event_id}: {exc}"
                result.errors.append(error_msg)
                logger.warning("Replay handler failed: %s", error_msg)
                if not continue_on_error:
                    result.end_time = datetime.now(timezone.utc)
                    return

    def get_replay_history(self) -> List[ReplayResult]:
        """Get the history of all replay operations.

        Returns:
            List of ReplayResult objects, most recent last.
        """
        return list(self._replay_history)

    def clear_history(self) -> None:
        """Clear the replay history."""
        self._replay_history.clear()
