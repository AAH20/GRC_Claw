"""Intent Scoring Agent for analyzing buying signals and prioritizing accounts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, ClassVar

import structlog

logger = structlog.get_logger(__name__)


class IntentSignalType(str, Enum):
    """Types of intent signals that indicate buying interest."""

    WEBSITE_VISIT = "website_visit"
    CONTENT_DOWNLOAD = "content_download"
    EMAIL_ENGAGEMENT = "email_engagement"
    AD_CLICK = "ad_click"
    SOCIAL_ENGAGEMENT = "social_engagement"
    PRICING_PAGE_VISIT = "pricing_page_visit"
    COMPETITOR_MENTION = "competitor_mention"
    JOB_POSTING = "job_posting"


@dataclass
class IntentSignal:
    """Represents a single intent signal."""

    signal_type: IntentSignalType
    timestamp: datetime
    weight: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentScore:
    """Represents the computed intent score for an account."""

    account_id: str
    total_score: float
    normalized_score: float
    signals: list[IntentSignal] = field(default_factory=list)
    trend: str = "stable"
    last_activity: datetime | None = None


class IntentScoringAgent:
    """Scores accounts based on intent signals to prioritize outreach efforts.

    This agent aggregates intent data from multiple sources (website, email,
    ads, social) and computes a composite intent score for each account.
    """

    # Signal weights for scoring
    SIGNAL_WEIGHTS: ClassVar[dict[IntentSignalType, float]] = {
        IntentSignalType.PRICING_PAGE_VISIT: 1.0,
        IntentSignalType.CONTENT_DOWNLOAD: 0.8,
        IntentSignalType.WEBSITE_VISIT: 0.3,
        IntentSignalType.EMAIL_ENGAGEMENT: 0.5,
        IntentSignalType.AD_CLICK: 0.4,
        IntentSignalType.SOCIAL_ENGAGEMENT: 0.2,
        IntentSignalType.COMPETITOR_MENTION: 0.9,
        IntentSignalType.JOB_POSTING: 0.6,
    }

    def __init__(
        self,
        scoring_window_days: int = 30,
        decay_factor: float = 0.95,
    ) -> None:
        """Initialize the Intent Scoring Agent.

        Args:
            scoring_window_days: Number of days to look back for intent signals.
            decay_factor: Daily decay factor for signal recency (0-1).
        """
        self.scoring_window_days = scoring_window_days
        self.decay_factor = decay_factor
        logger.info(
            "IntentScoringAgent initialized",
            scoring_window_days=scoring_window_days,
        )

    async def score_account(self, account_id: str) -> IntentScore:
        """Compute intent score for a specific account.

        Args:
            account_id: The unique identifier for the account.

        Returns:
            IntentScore object with computed scores and signal breakdown.

        Raises:
            ValueError: If account_id is empty.
        """
        if not account_id:
            raise ValueError("account_id cannot be empty")

        logger.info("Scoring account intent", account_id=account_id)

        # In production, this would query intent data sources
        signals = self._fetch_signals(account_id)
        total_score = self._compute_score(signals)
        normalized = min(total_score / 10.0, 1.0)

        trend = self._compute_trend(signals)
        last_activity = max((s.timestamp for s in signals), default=None)

        return IntentScore(
            account_id=account_id,
            total_score=round(total_score, 2),
            normalized_score=round(normalized, 2),
            signals=signals,
            trend=trend,
            last_activity=last_activity,
        )

    async def rank_accounts(self, account_ids: list[str]) -> list[IntentScore]:
        """Rank multiple accounts by intent score.

        Args:
            account_ids: List of account identifiers to rank.

        Returns:
            List of IntentScore objects sorted by score descending.
        """
        if not account_ids:
            raise ValueError("account_ids cannot be empty")

        logger.info("Ranking accounts by intent", count=len(account_ids))

        scores = []
        for account_id in account_ids:
            score = await self.score_account(account_id)
            scores.append(score)

        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores

    def _fetch_signals(self, account_id: str) -> list[IntentSignal]:
        """Fetch intent signals for an account from data sources.

        Args:
            account_id: The account to fetch signals for.

        Returns:
            List of IntentSignal objects.
        """
        now = datetime.now(tz=timezone.utc)
        return [
            IntentSignal(
                signal_type=IntentSignalType.WEBSITE_VISIT,
                timestamp=now - timedelta(hours=2),
                weight=self.SIGNAL_WEIGHTS[IntentSignalType.WEBSITE_VISIT],
                metadata={"pages_viewed": 5, "duration_seconds": 180},
            ),
            IntentSignal(
                signal_type=IntentSignalType.CONTENT_DOWNLOAD,
                timestamp=now - timedelta(days=1),
                weight=self.SIGNAL_WEIGHTS[IntentSignalType.CONTENT_DOWNLOAD],
                metadata={"content_type": "whitepaper", "title": "ABM Guide"},
            ),
            IntentSignal(
                signal_type=IntentSignalType.PRICING_PAGE_VISIT,
                timestamp=now - timedelta(hours=6),
                weight=self.SIGNAL_WEIGHTS[IntentSignalType.PRICING_PAGE_VISIT],
                metadata={"time_on_page_seconds": 120},
            ),
        ]

    def _compute_score(self, signals: list[IntentSignal]) -> float:
        """Compute weighted score from signals with time decay.

        Args:
            signals: List of intent signals.

        Returns:
            Computed score as a float.
        """
        if not signals:
            return 0.0

        now = datetime.now(tz=timezone.utc)
        total = 0.0

        for signal in signals:
            age_days = (now - signal.timestamp).total_seconds() / 86400
            decay = self.decay_factor ** age_days
            total += signal.weight * decay * 10

        return total

    def _compute_trend(self, signals: list[IntentSignal]) -> str:
        """Compute intent trend direction.

        Args:
            signals: List of intent signals.

        Returns:
            Trend direction: "increasing", "decreasing", or "stable".
        """
        if len(signals) < 2:
            return "stable"

        sorted_signals = sorted(signals, key=lambda s: s.timestamp)
        mid = len(sorted_signals) // 2

        recent = sorted_signals[mid:]
        older = sorted_signals[:mid]

        recent_score = sum(s.weight for s in recent)
        older_score = sum(s.weight for s in older)

        if recent_score > older_score * 1.2:
            return "increasing"
        elif recent_score < older_score * 0.8:
            return "decreasing"
        return "stable"
