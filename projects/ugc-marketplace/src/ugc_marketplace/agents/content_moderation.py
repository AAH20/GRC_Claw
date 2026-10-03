"""Content moderation agent for UGC marketplace.

Provides single-item and batch content moderation with realistic mock data,
confidence scoring, and proper type hints.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModerationStatus(str, Enum):
    """Possible moderation outcomes."""

    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED_FOR_REVIEW = "flagged_for_review"


class ViolationCategory(str, Enum):
    """Categories of content violations."""

    NONE = "none"
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SPAM = "spam"
    EXPLICIT_CONTENT = "explicit_content"
    MISINFORMATION = "misinformation"
    COPYRIGHT_INFRINGEMENT = "copyright_infringement"
    VIOLENCE = "violence"


@dataclass
class ModerationDecision:
    """Result of moderating a single piece of content."""

    content_id: str
    status: ModerationStatus
    confidence: float
    violation_category: ViolationCategory
    reasons: list[str] = field(default_factory=list)
    moderated_at: str = field(default_factory="2026-10-03T12:00:00Z")

    def to_dict(self) -> dict[str, Any]:
        """Serialize decision to dictionary."""
        return {
            "content_id": self.content_id,
            "status": self.status.value,
            "confidence": round(self.confidence, 4),
            "violation_category": self.violation_category.value,
            "reasons": self.reasons,
            "moderated_at": self.moderated_at,
        }


@dataclass
class BatchModerationResult:
    """Result of batch moderation."""

    results: list[ModerationDecision]
    total_processed: int
    approved_count: int
    rejected_count: int
    flagged_count: int
    average_confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize batch result to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_processed": self.total_processed,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "flagged_count": self.flagged_count,
            "average_confidence": round(self.average_confidence, 4),
        }


# --- Mock data -----------------------------------------------------------

_MOCK_CONTENT_DB: dict[str, dict[str, Any]] = {
    "post_001": {
        "text": "Just finished a great workout! Feeling amazing today.",
        "author_id": "user_42",
        "content_type": "text",
        "metadata": {"language": "en", "region": "US"},
    },
    "post_002": {
        "text": "Buy cheap followers at spam-link.example.com!!!",
        "author_id": "user_99",
        "content_type": "text",
        "metadata": {"language": "en", "region": "unknown"},
    },
    "post_003": {
        "text": "I disagree with the new policy, here's why...",
        "author_id": "user_15",
        "content_type": "text",
        "metadata": {"language": "en", "region": "UK"},
    },
    "post_004": {
        "text": "Check out my vacation photos from last summer!",
        "author_id": "user_7",
        "content_type": "image",
        "metadata": {"language": "en", "region": "CA"},
    },
    "post_005": {
        "text": "This product changed my life, highly recommend!",
        "author_id": "user_23",
        "content_type": "text",
        "metadata": {"language": "en", "region": "AU"},
    },
    "post_006": {
        "text": "Fake news about vaccines causes real harm.",
        "author_id": "user_55",
        "content_type": "text",
        "metadata": {"language": "en", "region": "US"},
    },
    "post_007": {
        "text": "Looking for collaborators on a new project.",
        "author_id": "user_31",
        "content_type": "text",
        "metadata": {"language": "en", "region": "DE"},
    },
    "post_008": {
        "text": "Explicit adult content description here...",
        "author_id": "user_88",
        "content_type": "text",
        "metadata": {"language": "en", "region": "unknown"},
    },
    "post_009": {
        "text": "Happy birthday to my best friend! 🎉",
        "author_id": "user_12",
        "content_type": "text",
        "metadata": {"language": "en", "region": "US"},
    },
    "post_010": {
        "text": "Reposting copyrighted material without permission.",
        "author_id": "user_67",
        "content_type": "text",
        "metadata": {"language": "en", "region": "unknown"},
    },
}

_VIOLATION_KEYWORDS: dict[ViolationCategory, list[str]] = {
    ViolationCategory.SPAM: ["buy cheap", "spam-link", "click here", "free money"],
    ViolationCategory.HATE_SPEECH: ["hate", "inferior race", "ethnic cleansing"],
    ViolationCategory.HARASSMENT: ["kill yourself", "kys", "nobody likes you"],
    ViolationCategory.EXPLICIT_CONTENT: ["explicit adult", "nsfw", "xxx"],
    ViolationCategory.MISINFORMATION: ["fake news", "hoax", "conspiracy"],
    ViolationCategory.COPYRIGHT_INFRINGEMENT: ["copyrighted material", "pirated", "stolen content"],
    ViolationCategory.VIOLENCE: ["bomb making", "terrorist attack", "mass shooting"],
}


def _compute_content_hash(content_id: str) -> int:
    """Deterministic hash for reproducible mock decisions."""
    return int(hashlib.sha256(content_id.encode()).hexdigest(), 16)


def _analyze_text(text: str) -> tuple[ViolationCategory, list[str]]:
    """Analyze text for violation keywords."""
    text_lower = text.lower()
    for category, keywords in _VIOLATION_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in text_lower]
        if matched:
            return category, matched
    return ViolationCategory.NONE, []


def _generate_decision(content_id: str) -> ModerationDecision:
    """Generate a moderation decision for a content item."""
    content_data = _MOCK_CONTENT_DB.get(content_id)

    if content_data is None:
        # Unknown content — flag for manual review with low confidence
        return ModerationDecision(
            content_id=content_id,
            status=ModerationStatus.FLAGGED_FOR_REVIEW,
            confidence=0.35,
            violation_category=ViolationCategory.NONE,
            reasons=["Content not found in database; requires manual review"],
        )

    text = content_data.get("text", "")
    category, matched_keywords = _analyze_text(text)
    content_hash = _compute_content_hash(content_id)
    rng = random.Random(content_hash)

    if category != ViolationCategory.NONE:
        confidence = rng.uniform(0.75, 0.98)
        status = (
            ModerationStatus.REJECTED
            if confidence > 0.85
            else ModerationStatus.FLAGGED_FOR_REVIEW
        )
        reasons = [
            f"Detected {category.value.replace('_', ' ')} indicators",
            f"Matched patterns: {', '.join(matched_keywords)}",
        ]
    else:
        confidence = rng.uniform(0.88, 0.99)
        status = ModerationStatus.APPROVED
        reasons = ["No policy violations detected"]

    return ModerationDecision(
        content_id=content_id,
        status=status,
        confidence=confidence,
        violation_category=category,
        reasons=reasons,
    )


# --- Public API ----------------------------------------------------------


def moderate_content(content_id: str) -> ModerationDecision:
    """Moderate a single piece of content and return a decision.

    Args:
        content_id: Unique identifier for the content to moderate.

    Returns:
        ModerationDecision with status, confidence, and violation details.
    """
    if not content_id or not isinstance(content_id, str):
        raise ValueError("content_id must be a non-empty string")
    return _generate_decision(content_id)


def batch_moderate(content_ids: list[str]) -> BatchModerationResult:
    """Moderate multiple content items in batch.

    Args:
        content_ids: List of content identifiers to moderate.

    Returns:
        BatchModerationResult with individual decisions and aggregate stats.
    """
    if not isinstance(content_ids, list):
        raise TypeError("content_ids must be a list of strings")

    results: list[ModerationDecision] = []
    for cid in content_ids:
        if not isinstance(cid, str):
            raise TypeError(f"All content IDs must be strings, got {type(cid).__name__}")
        results.append(_generate_decision(cid))

    total = len(results)
    approved = sum(1 for r in results if r.status == ModerationStatus.APPROVED)
    rejected = sum(1 for r in results if r.status == ModerationStatus.REJECTED)
    flagged = sum(1 for r in results if r.status == ModerationStatus.FLAGGED_FOR_REVIEW)
    avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0

    return BatchModerationResult(
        results=results,
        total_processed=total,
        approved_count=approved,
        rejected_count=rejected,
        flagged_count=flagged,
        average_confidence=avg_confidence,
    )
