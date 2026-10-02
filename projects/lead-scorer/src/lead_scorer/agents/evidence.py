"""Evidence agent for collecting engagement signals and intent data."""

from __future__ import annotations

import math
import time
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class EngagementType(StrEnum):
    """Types of engagement events."""

    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    WEBSITE_VISIT = "website_visit"
    CONTENT_DOWNLOAD = "content_download"
    WEBINAR_ATTEND = "webinar_attend"
    DEMO_REQUEST = "demo_request"
    PRICING_PAGE_VIEW = "pricing_page_view"
    SOCIAL_ENGAGEMENT = "social_engagement"


class EngagementEvent(BaseModel):
    """A single engagement event."""

    event_type: EngagementType
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntentSignal(BaseModel):
    """An intent signal indicating buying intent."""

    signal_type: str
    strength: float = Field(ge=0.0, le=1.0)
    source: str
    detected_at: datetime
    description: str = ""


class EvidenceResult(BaseModel):
    """Result from the evidence agent."""

    engagement_events: list[EngagementEvent] = Field(default_factory=list)
    intent_signals: list[IntentSignal] = Field(default_factory=list)
    total_engagements: int = 0
    engagement_score: float = Field(ge=0.0, le=1.0, default=0.0)
    intent_score: float = Field(ge=0.0, le=1.0, default=0.0)
    recency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceAgent:
    """Agent responsible for collecting engagement and intent evidence.

    Gathers behavioral data (email opens, website visits, content downloads)
    and intent signals (pricing page views, demo requests) to inform scoring.
    """

    def __init__(self, timeout_seconds: int = 45, max_retries: int = 2) -> None:
        """Initialize the evidence agent.

        Args:
            timeout_seconds: Maximum time allowed for evidence collection.
            max_retries: Number of retry attempts on failure.
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._engagement_weights: dict[EngagementType, float] = {
            EngagementType.EMAIL_OPEN: 0.1,
            EngagementType.EMAIL_CLICK: 0.2,
            EngagementType.WEBSITE_VISIT: 0.15,
            EngagementType.CONTENT_DOWNLOAD: 0.3,
            EngagementType.WEBINAR_ATTEND: 0.4,
            EngagementType.DEMO_REQUEST: 0.8,
            EngagementType.PRICING_PAGE_VIEW: 0.6,
            EngagementType.SOCIAL_ENGAGEMENT: 0.1,
        }

    async def collect(self, lead_id: str) -> EvidenceResult:
        """Collect evidence for a lead.

        Args:
            lead_id: Unique identifier for the lead.

        Returns:
            EvidenceResult with engagement events and intent signals.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If collection exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("collecting_evidence", lead_id=lead_id)
        start_time = time.monotonic()

        try:
            events = await self._fetch_engagement_events(lead_id)
            signals = await self._fetch_intent_signals(lead_id)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(
                    f"Evidence collection timed out after {elapsed:.1f}s"
                )

            engagement_score = self._compute_engagement_score(events)
            intent_score = self._compute_intent_score(signals)
            recency_score = self._compute_recency_score(events)

            result = EvidenceResult(
                engagement_events=events,
                intent_signals=signals,
                total_engagements=len(events),
                engagement_score=engagement_score,
                intent_score=intent_score,
                recency_score=recency_score,
                metadata={"elapsed_seconds": elapsed, "lead_id": lead_id},
            )

            logger.info(
                "evidence_collected",
                lead_id=lead_id,
                total_events=len(events),
                engagement_score=engagement_score,
                intent_score=intent_score,
            )
            return result

        except Exception as exc:
            logger.error("evidence_collection_failed", lead_id=lead_id, error=str(exc))
            raise

    async def _fetch_engagement_events(self, lead_id: str) -> list[EngagementEvent]:
        """Fetch engagement events from CRM and marketing automation.

        In production, this would query Salesforce/HubSpot APIs.
        """
        now = datetime.now(UTC)
        return [
            EngagementEvent(
                event_type=EngagementType.EMAIL_OPEN,
                timestamp=now - timedelta(days=2),
                metadata={"campaign": "welcome_series"},
            ),
            EngagementEvent(
                event_type=EngagementType.WEBSITE_VISIT,
                timestamp=now - timedelta(days=1),
                metadata={"page": "/features", "duration_seconds": 120},
            ),
            EngagementEvent(
                event_type=EngagementType.CONTENT_DOWNLOAD,
                timestamp=now - timedelta(hours=6),
                metadata={"content": "whitepaper_2024"},
            ),
        ]

    async def _fetch_intent_signals(self, lead_id: str) -> list[IntentSignal]:
        """Fetch intent signals from various sources.

        In production, this would query Bombora, 6sense, or similar.
        """
        now = datetime.now(UTC)
        return [
            IntentSignal(
                signal_type="pricing_page_view",
                strength=0.7,
                source="website_analytics",
                detected_at=now - timedelta(hours=3),
                description="Visited pricing page twice in 24h",
            ),
            IntentSignal(
                signal_type="competitor_comparison",
                strength=0.5,
                source="website_analytics",
                detected_at=now - timedelta(days=1),
                description="Viewed competitor comparison page",
            ),
        ]

    def _compute_engagement_score(self, events: list[EngagementEvent]) -> float:
        """Compute engagement score from events."""
        if not events:
            return 0.0
        total_weight = sum(self._engagement_weights.get(e.event_type, 0.1) for e in events)
        # Normalize: cap at 1.0, use diminishing returns
        return min(total_weight / 3.0, 1.0)

    def _compute_intent_score(self, signals: list[IntentSignal]) -> float:
        """Compute intent score from signals."""
        if not signals:
            return 0.0
        avg_strength = sum(s.strength for s in signals) / len(signals)
        # Boost for multiple signals
        count_boost = min(len(signals) * 0.1, 0.3)
        return min(avg_strength + count_boost, 1.0)

    def _compute_recency_score(self, events: list[EngagementEvent]) -> float:
        """Compute recency score based on most recent engagement."""
        if not events:
            return 0.0
        now = datetime.now(UTC)
        most_recent = max(e.timestamp for e in events)
        days_since = (now - most_recent).days
        # Exponential decay: score = e^(-days/14)
        return math.exp(-days_since / 14.0)
