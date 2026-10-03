"""Type definitions for fraud detection agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Transaction:
    """Represents a transaction."""

    id: str
    user_id: str
    amount: float
    currency: str = "USD"
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Represents a detected anomaly."""

    transaction_id: str
    anomaly_type: str
    severity: str
    score: float
    description: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Pattern:
    """Represents a detected pattern."""

    pattern_type: str
    transaction_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class RiskScore:
    """Represents a risk score."""

    user_id: str
    score: float
    risk_level: str
    factors: list[str] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountAnalysis:
    """Represents an account analysis."""

    user_id: str
    risk_score: float
    anomalies: list[Anomaly] = field(default_factory=list)
    patterns: list[Pattern] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)
