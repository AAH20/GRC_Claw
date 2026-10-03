"""Type definitions for quality scoring agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DimensionScore:
    """Represents a score for a specific quality dimension."""

    dimension: str
    score: float
    weight: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImprovementPlan:
    """Represents an improvement plan for content."""

    content_id: str
    current_score: float
    target_score: float
    recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
