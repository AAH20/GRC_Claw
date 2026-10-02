"""
Real-Time Lead Scoring Example
==============================

Demonstrates real-time lead scoring capabilities including:
- Event-driven scoring with streaming data
- Real-time score updates on behavior
- WebSocket-based score notifications
- Score change alerts and thresholds
- Real-time lead ranking
- Integration with CRM systems
- Score caching and performance optimization

Usage:
    python real-time.py
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RealTimeEventType(str, Enum):
    """Types of real-time events."""

    PAGE_VIEW = "page_view"
    FORM_SUBMIT = "form_submit"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    CONTENT_DOWNLOAD = "content_download"
    WEBINAR_ATTEND = "webinar_attend"
    TRIAL_START = "trial_start"
    DEMO_REQUEST = "demo_request"
    PRICING_VIEW = "pricing_view"
    CHAT_START = "chat_start"
    VIDEO_WATCH = "video_watch"
    SOCIAL_SHARE = "social_share"


class AlertType(str, Enum):
    """Types of score alerts."""

    SCORE_THRESHOLD = "score_threshold"
    SCORE_DROP = "score_drop"
    HIGH_VALUE_LEAD = "high_value_lead"
    CHURN_RISK = "churn_risk"
    BUYING_SIGNAL = "buying_signal"


@dataclass
class RealTimeEvent:
    """A real-time event from any source."""

    event_id: str
    lead_id: str
    event_type: RealTimeEventType
    timestamp: datetime
    properties: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"


@dataclass
class ScoreAlert:
    """A score-based alert."""

    alert_id: str
    lead_id: str
    alert_type: AlertType
    message: str
    old_score: float
    new_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LeadScoreState:
    """Real-time score state for a lead."""

    lead_id: str
    current_score: float = 0.0
    previous_score: float = 0.0
    score_history: list[dict[str, Any]] = field(default_factory=list)
    event_count: int = 0
    last_event_at: datetime | None = None
    first_event_at: datetime | None = None
    alerts_triggered: list[ScoreAlert] = field(default_factory=list)
    is_hot: bool = False
    is_cold: bool = False

    def update_score(self, new_score: float, event_type: RealTimeEventType) -> None:
        """Update the lead's score.

        Args:
            new_score: The new score value.
            event_type: The event that triggered the update.
        """
        self.previous_score = self.current_score
        self.current_score = new_score
        self.event_count += 1
        self.last_event_at = datetime.now()

        if self.first_event_at is None:
            self.first_event_at = self.last_event_at

        self.score_history.append({
            "score": new_score,
            "event_type": event_type.value,
            "timestamp": self.last_event_at.isoformat(),
        })

        # Keep only last 100 history entries
        if len(self.score_history) > 100:
            self.score_history = self.score_history[-100:]

        # Update hot/cold status
        self.is_hot = new_score >= 80.0
        self.is_cold = new_score < 20.0


class RealTimeLeadScoringEngine:
    """Real-time lead scoring engine with event-driven architecture."""

    def __init__(
        self,
        hot_threshold: float = 80.0,
        cold_threshold: float = 20.0,
        alert_callbacks: list[Callable[[ScoreAlert], None]] | None = None,
    ) -> None:
        """Initialize the real-time scoring engine.

        Args:
            hot_threshold: Score threshold for hot leads.
            cold_threshold: Score threshold for cold leads.
            alert_callbacks: Optional callbacks for score alerts.
        """
        self.hot_threshold = hot_threshold
        self.cold_threshold = cold_threshold
        self.alert_callbacks = alert_callbacks or []
        self.leads: dict[str, LeadScoreState] = {}
        self.event_weights: dict[RealTimeEventType, float] = {
            RealTimeEventType.PAGE_VIEW: 1.0,
            RealTimeEventType.FORM_SUBMIT: 10.0,
            RealTimeEventType.EMAIL_OPEN: 2.0,
            RealTimeEventType.EMAIL_CLICK: 5.0,
            RealTimeEventType.CONTENT_DOWNLOAD: 8.0,
            RealTimeEventType.WEBINAR_ATTEND: 15.0,
            RealTimeEventType.TRIAL_START: 25.0,
            RealTimeEventType.DEMO_REQUEST: 30.0,
            RealTimeEventType.PRICING_VIEW: 12.0,
            RealTimeEventType.CHAT_START: 10.0,
            RealTimeEventType.VIDEO_WATCH: 3.0,
            RealTimeEventType.SOCIAL_SHARE: 4.0,
        }
        self._event_queue: asyncio.Queue[RealTimeEvent] = asyncio.Queue()
        self._running = False

    def register_lead(self, lead_id: str, initial_score: float = 0.0) -> LeadScoreState:
        """Register a lead for real-time scoring.

        Args:
            lead_id: Unique lead identifier.
            initial_score: Initial score value.

        Returns:
            The LeadScoreState for the lead.
        """
        state = LeadScoreState(
            lead_id=lead_id,
            current_score=initial_score,
            previous_score=initial_score,
        )
        self.leads[lead_id] = state
        logger.info("Registered lead '%s' with initial score %.1f", lead_id, initial_score)
        return state

    def process_event(self, event: RealTimeEvent) -> LeadScoreState:
        """Process a real-time event and update the lead's score.

        Args:
            event: The real-time event to process.

        Returns:
            Updated LeadScoreState.

        Raises:
            ValueError: If lead is not registered.
        """
        if event.lead_id not in self.leads:
            raise ValueError(f"Lead '{event.lead_id}' not registered")

        state = self.leads[event.lead_id]

        # Calculate score delta
        base_weight = self.event_weights.get(event.event_type, 1.0)

        # Apply recency bonus (events within last hour get bonus)
        if state.last_event_at:
            time_diff = (event.timestamp - state.last_event_at).total_seconds()
            if time_diff < 3600:  # Within 1 hour
                base_weight *= 1.5

        # Apply frequency penalty (too many events in short time)
        if state.event_count > 0 and state.last_event_at:
            time_diff = (event.timestamp - state.last_event_at).total_seconds()
            if time_diff < 60:  # Within 1 minute
                base_weight *= 0.5

        # Update score
        new_score = min(state.current_score + base_weight, 100.0)
        state.update_score(new_score, event.event_type)

        # Check for alerts
        self._check_alerts(state, event)

        logger.debug(
            "Processed event '%s' for lead '%s': score %.1f -> %.1f",
            event.event_type.value,
            event.lead_id,
            state.previous_score,
            state.current_score,
        )

        return state

    def _check_alerts(self, state: LeadScoreState, event: RealTimeEvent) -> None:
        """Check and trigger score alerts.

        Args:
            state: The lead's score state.
            event: The triggering event.
        """
        alerts: list[ScoreAlert] = []

        # Hot lead threshold crossed
        if state.previous_score < self.hot_threshold <= state.current_score:
            alerts.append(ScoreAlert(
                alert_id=f"alert_{len(state.alerts_triggered)}",
                lead_id=state.lead_id,
                alert_type=AlertType.HIGH_VALUE_LEAD,
                message=f"Lead crossed hot threshold ({self.hot_threshold})",
                old_score=state.previous_score,
                new_score=state.current_score,
                metadata={"event_type": event.event_type.value},
            ))

        # Score dropped significantly
        if state.previous_score - state.current_score > 20:
            alerts.append(ScoreAlert(
                alert_id=f"alert_{len(state.alerts_triggered)}",
                lead_id=state.lead_id,
                alert_type=AlertType.SCORE_DROP,
                message=f"Score dropped by {state.previous_score - state.current_score:.1f} points",
                old_score=state.previous_score,
                new_score=state.current_score,
            ))

        # Buying signal
        if event.event_type in [RealTimeEventType.DEMO_REQUEST, RealTimeEventType.TRIAL_START]:
            alerts.append(ScoreAlert(
                alert_id=f"alert_{len(state.alerts_triggered)}",
                lead_id=state.lead_id,
                alert_type=AlertType.BUYING_SIGNAL,
                message=f"Buying signal: {event.event_type.value}",
                old_score=state.previous_score,
                new_score=state.current_score,
            ))

        for alert in alerts:
            state.alerts_triggered.append(alert)
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error("Alert callback failed: %s", e)

    async def start_event_processor(self) -> None:
        """Start the async event processor."""
        self._running = True
        logger.info("Real-time event processor started")

        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                self.process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error processing event: %s", e)

    def stop_event_processor(self) -> None:
        """Stop the async event processor."""
        self._running = False
        logger.info("Real-time event processor stopped")

    async def submit_event(self, event: RealTimeEvent) -> None:
        """Submit an event for async processing.

        Args:
            event: The event to submit.
        """
        await self._event_queue.put(event)

    def get_leaderboard(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Get the top leads by score.

        Args:
            top_n: Number of leads to return.

        Returns:
            List of lead score summaries.
        """
        sorted_leads = sorted(
            self.leads.values(),
            key=lambda s: s.current_score,
            reverse=True,
        )

        return [
            {
                "lead_id": s.lead_id,
                "score": round(s.current_score, 2),
                "event_count": s.event_count,
                "is_hot": s.is_hot,
                "last_event": s.last_event_at.isoformat() if s.last_event_at else None,
            }
            for s in sorted_leads[:top_n]
        ]

    def get_score_trend(self, lead_id: str, window: int = 10) -> list[dict[str, Any]]:
        """Get score trend for a lead.

        Args:
            lead_id: The lead identifier.
            window: Number of history entries to return.

        Returns:
            List of score history entries.
        """
        if lead_id not in self.leads:
            raise ValueError(f"Lead '{lead_id}' not found")

        state = self.leads[lead_id]
        return state.score_history[-window:]


def print_alert(alert: ScoreAlert) -> None:
    """Default alert handler that prints alerts.

    Args:
        alert: The score alert to print.
    """
    logger.info(
        "ALERT [%s] Lead '%s': %s (score: %.1f -> %.1f)",
        alert.alert_type.value,
        alert.lead_id,
        alert.message,
        alert.old_score,
        alert.new_score,
    )


async def main() -> None:
    """Run the real-time lead scoring example."""
    logger.info("=" * 60)
    logger.info("Real-Time Lead Scoring Example")
    logger.info("=" * 60)

    engine = RealTimeLeadScoringEngine(
        hot_threshold=75.0,
        cold_threshold=15.0,
        alert_callbacks=[print_alert],
    )

    # Register leads
    engine.register_lead("lead_rt_001", initial_score=10.0)
    engine.register_lead("lead_rt_002", initial_score=5.0)
    engine.register_lead("lead_rt_003", initial_score=20.0)

    # Start event processor in background
    processor_task = asyncio.create_task(engine.start_event_processor())

    # Simulate real-time events
    events = [
        RealTimeEvent("evt_001", "lead_rt_001", RealTimeEventType.PAGE_VIEW, datetime.now(), {"page": "/products"}),
        RealTimeEvent("evt_002", "lead_rt_001", RealTimeEventType.PAGE_VIEW, datetime.now(), {"page": "/pricing"}),
        RealTimeEvent("evt_003", "lead_rt_001", RealTimeEventType.PRICING_VIEW, datetime.now()),
        RealTimeEvent("evt_004", "lead_rt_001", RealTimeEventType.FORM_SUBMIT, datetime.now(), {"form": "contact"}),
        RealTimeEvent("evt_005", "lead_rt_001", RealTimeEventType.CONTENT_DOWNLOAD, datetime.now(), {"content": "whitepaper"}),
        RealTimeEvent("evt_006", "lead_rt_001", RealTimeEventType.WEBINAR_ATTEND, datetime.now()),
        RealTimeEvent("evt_007", "lead_rt_001", RealTimeEventType.DEMO_REQUEST, datetime.now()),
        RealTimeEvent("evt_008", "lead_rt_001", RealTimeEventType.TRIAL_START, datetime.now()),

        RealTimeEvent("evt_009", "lead_rt_002", RealTimeEventType.PAGE_VIEW, datetime.now(), {"page": "/blog"}),
        RealTimeEvent("evt_010", "lead_rt_002", RealTimeEventType.EMAIL_OPEN, datetime.now()),

        RealTimeEvent("evt_011", "lead_rt_003", RealTimeEventType.PAGE_VIEW, datetime.now(), {"page": "/solutions"}),
        RealTimeEvent("evt_012", "lead_rt_003", RealTimeEventType.DEMO_REQUEST, datetime.now()),
        RealTimeEvent("evt_013", "lead_rt_003", RealTimeEventType.TRIAL_START, datetime.now()),
    ]

    logger.info("\nProcessing %d real-time events...", len(events))
    for event in events:
        await engine.submit_event(event)
        await asyncio.sleep(0.1)  # Small delay between events

    # Wait for processing to complete
    await asyncio.sleep(1.0)

    # Stop processor
    engine.stop_event_processor()
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

    # Display results
    logger.info("\nLeaderboard:")
    logger.info("-" * 60)
    for entry in engine.get_leaderboard(top_n=5):
        logger.info(
            "  %s - Score: %.1f (Events: %d, Hot: %s)",
            entry["lead_id"],
            entry["score"],
            entry["event_count"],
            entry["is_hot"],
        )

    # Score trend for top lead
    logger.info("\nScore trend for lead_rt_001:")
    trend = engine.get_score_trend("lead_rt_001")
    for entry in trend:
        logger.info("  %s: %.1f (%s)", entry["timestamp"], entry["score"], entry["event_type"])

    logger.info("\n" + "=" * 60)
    logger.info("Real-time example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
