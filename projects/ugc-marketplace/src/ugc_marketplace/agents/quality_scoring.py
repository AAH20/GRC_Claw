"""Quality scoring agent for UGC marketplace content.

Provides content quality assessment with detailed breakdowns and
comparative analysis across multiple content items.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ContentType(str, Enum):
    """Supported UGC content types."""

    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    AUDIO = "audio"
    MIXED = "mixed"


class QualityGrade(str, Enum):
    """Letter-grade classification derived from numeric score."""

    EXCELLENT = "A"
    GOOD = "B"
    AVERAGE = "C"
    BELOW_AVERAGE = "D"
    POOR = "F"


@dataclass(frozen=True)
class QualityDimension:
    """A single scored dimension of content quality."""

    name: str
    score: float  # 0.0 – 1.0
    weight: float  # contribution weight (all weights sum to 1.0)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class QualityScore:
    """Full quality score result for a single content item."""

    content_id: str
    content_type: ContentType
    overall_score: float  # 0.0 – 100.0
    grade: QualityGrade
    dimensions: list[QualityDimension]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade.value,
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 4),
                    "weight": d.weight,
                    "weighted_score": round(d.weighted_score, 4),
                    "details": d.details,
                }
                for d in self.dimensions
            ],
            "metadata": self.metadata,
        }


@dataclass
class ComparativeAnalysis:
    """Comparative quality analysis across multiple content items."""

    ranked_ids: list[str]
    best_content_id: str
    worst_content_id: str
    average_score: float
    score_spread: float
    pairwise_gaps: dict[str, float] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranked_ids": self.ranked_ids,
            "best_content_id": self.best_content_id,
            "worst_content_id": self.worst_content_id,
            "average_score": round(self.average_score, 2),
            "score_spread": round(self.score_spread, 2),
            "pairwise_gaps": {k: round(v, 2) for k, v in self.pairwise_gaps.items()},
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

# Deterministic mock content database keyed by content_id.
# In production this would be backed by a real database / feature store.
_MOCK_CONTENT_DB: dict[str, dict[str, Any]] = {
    "vid_001": {
        "content_type": ContentType.VIDEO,
        "title": "Morning Coffee Routine",
        "duration_seconds": 145,
        "resolution": "1080p",
        "has_captions": True,
        "engagement_rate": 0.082,
        "completion_rate": 0.71,
        "report_count": 0,
        "authenticity_signals": {
            "reverse_image_match": False,
            "watermark_detected": False,
            "ai_generated_probability": 0.03,
        },
        "creator_tier": "established",
        "upload_age_days": 12,
    },
    "vid_002": {
        "content_type": ContentType.VIDEO,
        "title": "Quick Product Unboxing",
        "duration_seconds": 38,
        "resolution": "720p",
        "has_captions": False,
        "engagement_rate": 0.031,
        "completion_rate": 0.22,
        "report_count": 2,
        "authenticity_signals": {
            "reverse_image_match": True,
            "watermark_detected": True,
            "ai_generated_probability": 0.67,
        },
        "creator_tier": "new",
        "upload_age_days": 3,
    },
    "img_001": {
        "content_type": ContentType.IMAGE,
        "title": "Handmade Ceramic Mug",
        "resolution": "2048x1536",
        "has_captions": False,
        "engagement_rate": 0.055,
        "completion_rate": 0.88,
        "report_count": 0,
        "authenticity_signals": {
            "reverse_image_match": False,
            "watermark_detected": False,
            "ai_generated_probability": 0.01,
        },
        "creator_tier": "established",
        "upload_age_days": 45,
    },
    "txt_001": {
        "content_type": ContentType.TEXT,
        "title": "Review: Ergonomic Keyboard",
        "word_count": 340,
        "has_captions": False,
        "engagement_rate": 0.048,
        "completion_rate": 0.65,
        "report_count": 1,
        "authenticity_signals": {
            "reverse_image_match": False,
            "watermark_detected": False,
            "ai_generated_probability": 0.12,
        },
        "creator_tier": "mid",
        "upload_age_days": 20,
    },
    "aud_001": {
        "content_type": ContentType.AUDIO,
        "title": "Lo-fi Study Session",
        "duration_seconds": 1830,
        "has_captions": True,
        "engagement_rate": 0.067,
        "completion_rate": 0.54,
        "report_count": 0,
        "authenticity_signals": {
            "reverse_image_match": False,
            "watermark_detected": False,
            "ai_generated_probability": 0.05,
        },
        "creator_tier": "established",
        "upload_age_days": 60,
    },
}

# Dimension weights — must sum to 1.0
_DIMENSION_WEIGHTS: dict[str, float] = {
    "engagement": 0.30,
    "authenticity": 0.25,
    "production_quality": 0.20,
    "creator_reputation": 0.15,
    "policy_compliance": 0.10,
}


# ---------------------------------------------------------------------------
# Internal Scoring Helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp *value* to [*low*, *high*]."""
    return max(low, min(high, value))


def _score_engagement(content: dict[str, Any]) -> QualityDimension:
    """Score based on engagement and completion metrics."""
    eng = _clamp(content.get("engagement_rate", 0.0) / 0.10)
    comp = _clamp(content.get("completion_rate", 0.0))
    raw = 0.6 * eng + 0.4 * comp
    return QualityDimension(
        name="engagement",
        score=round(_clamp(raw), 4),
        weight=_DIMENSION_WEIGHTS["engagement"],
        details={
            "engagement_rate": content.get("engagement_rate", 0.0),
            "completion_rate": content.get("completion_rate", 0.0),
        },
    )


def _score_authenticity(content: dict[str, Any]) -> QualityDimension:
    """Score based on authenticity / originality signals."""
    signals: dict[str, Any] = content.get("authenticity_signals", {})
    ai_prob = signals.get("ai_generated_probability", 0.0)
    reverse_match = signals.get("reverse_image_match", False)
    watermark = signals.get("watermark_detected", False)

    penalty = 0.0
    if reverse_match:
        penalty += 0.35
    if watermark:
        penalty += 0.25
    penalty += ai_prob * 0.40

    raw = 1.0 - _clamp(penalty)
    return QualityDimension(
        name="authenticity",
        score=round(_clamp(raw), 4),
        weight=_DIMENSION_WEIGHTS["authenticity"],
        details={
            "ai_generated_probability": ai_prob,
            "reverse_image_match": reverse_match,
            "watermark_detected": watermark,
        },
    )


def _score_production_quality(content: dict[str, Any]) -> QualityDimension:
    """Score based on technical production attributes."""
    ctype = content.get("contentType", content.get("content_type", ContentType.TEXT))
    details: dict[str, Any] = {}

    if ctype in (ContentType.VIDEO, ContentType.AUDIO):
        duration = content.get("duration_seconds", 0)
        # Ideal duration sweet-spot: 60 s – 600 s
        if 60 <= duration <= 600:
            duration_score = 1.0
        elif duration < 60:
            duration_score = duration / 60.0
        else:
            duration_score = max(0.3, 1.0 - (duration - 600) / 1200.0)
        details["duration_seconds"] = duration
        details["duration_score"] = round(duration_score, 4)
        raw = duration_score

        if ctype == ContentType.VIDEO:
            res = content.get("resolution", "720p")
            res_map = {"4k": 1.0, "1440p": 0.9, "1080p": 0.8, "720p": 0.6, "480p": 0.4}
            res_score = res_map.get(res, 0.5)
            details["resolution"] = res
            details["resolution_score"] = res_score
            raw = 0.6 * duration_score + 0.4 * res_score

        captions = content.get("has_captions", False)
        details["has_captions"] = captions
        raw = 0.85 * raw + 0.15 * (1.0 if captions else 0.5)

    elif ctype == ContentType.IMAGE:
        res_str = content.get("resolution", "1024x768")
        try:
            w, h = res_str.lower().split("x")
            pixels = int(w) * int(h)
        except (ValueError, AttributeError):
            pixels = 1024 * 768
        # 2 MP is a reasonable baseline
        res_score = _clamp(pixels / 2_000_000)
        details["resolution"] = res_str
        details["resolution_score"] = round(res_score, 4)
        raw = res_score

    else:  # TEXT
        wc = content.get("word_count", 0)
        # Ideal review length: 150 – 800 words
        if 150 <= wc <= 800:
            wc_score = 1.0
        elif wc < 150:
            wc_score = wc / 150.0
        else:
            wc_score = max(0.4, 1.0 - (wc - 800) / 1000.0)
        details["word_count"] = wc
        details["word_count_score"] = round(wc_score, 4)
        raw = wc_score

    return QualityDimension(
        name="production_quality",
        score=round(_clamp(raw), 4),
        weight=_DIMENSION_WEIGHTS["production_quality"],
        details=details,
    )


def _score_creator_reputation(content: dict[str, Any]) -> QualityDimension:
    """Score based on creator tier and account maturity."""
    tier = content.get("creator_tier", "new")
    tier_map = {"established": 1.0, "mid": 0.7, "new": 0.4}
    tier_score = tier_map.get(tier, 0.4)

    age = content.get("upload_age_days", 0)
    age_score = _clamp(age / 90.0)  # 90 days → full score

    raw = 0.6 * tier_score + 0.4 * age_score
    return QualityDimension(
        name="creator_reputation",
        score=round(_clamp(raw), 4),
        weight=_DIMENSION_WEIGHTS["creator_reputation"],
        details={
            "creator_tier": tier,
            "upload_age_days": age,
        },
    )


def _score_policy_compliance(content: dict[str, Any]) -> QualityDimension:
    """Score inversely proportional to report count."""
    reports = content.get("report_count", 0)
    # 0 reports → 1.0, 5+ reports → 0.0
    raw = 1.0 - _clamp(reports / 5.0)
    return QualityDimension(
        name="policy_compliance",
        score=round(_clamp(raw), 4),
        weight=_DIMENSION_WEIGHTS["policy_compliance"],
        details={"report_count": reports},
    )


def _grade_from_score(score: float) -> QualityGrade:
    """Map a 0–100 score to a letter grade."""
    if score >= 90:
        return QualityGrade.EXCELLENT
    if score >= 75:
        return QualityGrade.GOOD
    if score >= 60:
        return QualityGrade.AVERAGE
    if score >= 40:
        return QualityGrade.BELOW_AVERAGE
    return QualityGrade.POOR


def _generate_content_id(seed: str) -> str:
    """Generate a deterministic content ID from a seed string."""
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return f"gen_{digest}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_content(content_id: str) -> QualityScore:
    """Compute a full quality score for a single content item.

    Parameters
    ----------
    content_id:
        Unique identifier for the content item. If the ID is not found
        in the mock database, a synthetic record is generated
        deterministically from the ID string.

    Returns
    -------
    QualityScore
        Complete quality assessment with per-dimension breakdown.

    Examples
    --------
    >>> result = score_content("vid_001")
    >>> result.overall_score > 0
    True
    >>> result.grade in QualityGrade
    True
    """
    content = _MOCK_CONTENT_DB.get(content_id)

    if content is None:
        # Deterministic synthetic fallback
        content = _synthetic_content(content_id)

    dimensions: list[QualityDimension] = [
        _score_engagement(content),
        _score_authenticity(content),
        _score_production_quality(content),
        _score_creator_reputation(content),
        _score_policy_compliance(content),
    ]

    overall = sum(d.weighted_score for d in dimensions) * 100.0
    overall = round(_clamp(overall, 0.0, 100.0), 2)

    return QualityScore(
        content_id=content_id,
        content_type=content.get("content_type", ContentType.TEXT),
        overall_score=overall,
        grade=_grade_from_score(overall),
        dimensions=dimensions,
        metadata={
            "title": content.get("title", "Untitled"),
            "scorer_version": "1.0.0",
        },
    )


def compare_quality(content_ids: list[str]) -> ComparativeAnalysis:
    """Compare quality scores across multiple content items.

    Parameters
    ----------
    content_ids:
        List of content identifiers to compare. Must contain at least
        two IDs.

    Returns
    -------
    ComparativeAnalysis
        Ranked list, best/worst IDs, average score, spread, and
        pairwise gap analysis.

    Raises
    ------
    ValueError
        If fewer than two content IDs are provided.

    Examples
    --------
    >>> analysis = compare_quality(["vid_001", "vid_002", "img_001"])
    >>> len(analysis.ranked_ids) == 3
    True
    """
    if len(content_ids) < 2:
        raise ValueError(
            f"compare_quality requires at least 2 content IDs, got {len(content_ids)}"
        )

    scores: dict[str, QualityScore] = {}
    for cid in content_ids:
        scores[cid] = score_content(cid)

    # Rank descending by overall_score
    ranked = sorted(scores.values(), key=lambda s: s.overall_score, reverse=True)
    ranked_ids = [s.content_id for s in ranked]

    best = ranked[0]
    worst = ranked[-1]

    all_scores = [s.overall_score for s in ranked]
    avg = sum(all_scores) / len(all_scores)
    spread = max(all_scores) - min(all_scores)

    # Pairwise gaps: difference from best for each non-best item
    pairwise_gaps: dict[str, float] = {}
    for s in ranked[1:]:
        pairwise_gaps[s.content_id] = round(best.overall_score - s.overall_score, 2)

    summary = _build_summary(ranked, avg, spread)

    return ComparativeAnalysis(
        ranked_ids=ranked_ids,
        best_content_id=best.content_id,
        worst_content_id=worst.content_id,
        average_score=round(avg, 2),
        score_spread=round(spread, 2),
        pairwise_gaps=pairwise_gaps,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Private Utilities
# ---------------------------------------------------------------------------


def _synthetic_content(content_id: str) -> dict[str, Any]:
    """Generate a deterministic synthetic content record for unknown IDs."""
    # Use hash to derive stable pseudo-random attributes
    h = int(hashlib.sha256(content_id.encode()).hexdigest(), 16)

    types = [ContentType.VIDEO, ContentType.IMAGE, ContentType.TEXT, ContentType.AUDIO]
    ctype = types[h % len(types)]

    return {
        "content_type": ctype,
        "title": f"Synthetic Content {content_id}",
        "duration_seconds": 30 + (h % 570),
        "resolution": ["720p", "1080p", "4k"][h % 3],
        "has_captions": bool(h & 1),
        "engagement_rate": round((h % 100) / 1000.0, 4),
        "completion_rate": round(((h >> 4) % 100) / 100.0, 4),
        "report_count": (h >> 8) % 5,
        "authenticity_signals": {
            "reverse_image_match": bool(h & 2),
            "watermark_detected": bool(h & 4),
            "ai_generated_probability": round(((h >> 12) % 100) / 100.0, 4),
        },
        "creator_tier": ["new", "mid", "established"][h % 3],
        "upload_age_days": (h >> 16) % 120,
        "word_count": 50 + (h % 800),
    }


def _build_summary(
    ranked: list[QualityScore], avg: float, spread: float
) -> str:
    """Build a human-readable summary string."""
    best = ranked[0]
    worst = ranked[-1]
    parts = [
        f"Best: {best.content_id} ({best.overall_score:.1f}, grade {best.grade.value})",
        f"Worst: {worst.content_id} ({worst.overall_score:.1f}, grade {worst.grade.value})",
        f"Average: {avg:.1f}",
        f"Spread: {spread:.1f} points",
    ]
    if spread > 30:
        parts.append("High variance — significant quality gap between top and bottom.")
    elif spread < 10:
        parts.append("Low variance — content quality is relatively uniform.")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Module-level convenience (optional CLI-style usage)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    # Demo: score a single item
    single = score_content("vid_001")
    print("=== Single Score ===")
    print(json.dumps(single.to_dict(), indent=2))

    # Demo: compare multiple items
    print("\n=== Comparative Analysis ===")
    multi = compare_quality(["vid_001", "vid_002", "img_001", "txt_001", "aud_001"])
    print(json.dumps(multi.to_dict(), indent=2))
