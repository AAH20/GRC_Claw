"""Reputation system agent for gated communities.

Tracks member reputation scores based on community actions such as
posting, receiving upvotes/downvotes, reporting violations, and
participating in governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ActionType(str, Enum):
    """Types of actions that affect a member's reputation."""

    POST_CREATED = "post_created"
    COMMENT_CREATED = "comment_created"
    UPVOTE_RECEIVED = "upvote_received"
    DOWNVOTE_RECEIVED = "downvote_received"
    REPORT_FILED = "report_filed"
    REPORT_CONFIRMED = "report_confirmed"
    REPORT_REJECTED = "report_rejected"
    GOVERNANCE_VOTE = "governance_vote"
    MEMBER_INVITED = "member_invited"
    VIOLATION_COMMITTED = "violation_committed"
    MENTORSHIP_PROVIDED = "mentorship_provided"
    CONTENT_REMOVED = "content_removed"


# Reputation point deltas for each action type
ACTION_REPUTATION_DELTAS: Dict[ActionType, int] = {
    ActionType.POST_CREATED: 5,
    ActionType.COMMENT_CREATED: 2,
    ActionType.UPVOTE_RECEIVED: 3,
    ActionType.DOWNVOTE_RECEIVED: -2,
    ActionType.REPORT_FILED: 1,
    ActionType.REPORT_CONFIRMED: 4,
    ActionType.REPORT_REJECTED: -3,
    ActionType.GOVERNANCE_VOTE: 2,
    ActionType.MEMBER_INVITED: 10,
    ActionType.VIOLATION_COMMITTED: -15,
    ActionType.MENTORSHIP_PROVIDED: 8,
    ActionType.CONTENT_REMOVED: -10,
}


@dataclass
class ReputationEvent:
    """A single reputation-affecting event in a member's history."""

    action: ActionType
    points: int
    timestamp: str
    description: str = ""


@dataclass
class MemberReputation:
    """Reputation record for a community member."""

    member_id: str
    score: int = 0
    level: str = "newcomer"
    history: List[ReputationEvent] = field(default_factory=list)


# ── Mock database ────────────────────────────────────────────────────────────

_mock_reputation_db: Dict[str, MemberRepputation] = {}


def _seed_mock_data() -> None:
    """Populate the mock database with realistic seed data."""
    seed_members = [
        ("member_001", 245, "veteran"),
        ("member_002", 128, "established"),
        ("member_003", 42, "regular"),
        ("member_004", 15, "newcomer"),
        ("member_005", 310, "veteran"),
        ("member_006", 78, "regular"),
        ("member_007", 5, "newcomer"),
        ("member_008", 190, "established"),
    ]
    for member_id, score, level in seed_members:
        _mock_reputation_db[member_id] = MemberReputation(
            member_id=member_id,
            score=score,
            level=level,
        )


# Seed on module import
_seed_mock_data()


# ── Public API ───────────────────────────────────────────────────────────────


def calculate_reputation(member_id: str) -> int:
    """Return the current reputation score for a member.

    Args:
        member_id: Unique identifier of the community member.

    Returns:
        The member's reputation score as an integer. Returns 0 for
        unknown members.
    """
    record: Optional[MemberReputation] = _mock_reputation_db.get(member_id)
    if record is None:
        return 0
    return record.score


def update_reputation(member_id: str, action: ActionType) -> int:
    """Update a member's reputation based on the given action.

    Applies the point delta associated with *action* to the member's
    current score, records the event in their history, and returns
    the new score.

    Args:
        member_id: Unique identifier of the community member.
        action: The action that was performed.

    Returns:
        The updated reputation score.
    """
    delta: int = ACTION_REPUTATION_DELTAS.get(action, 0)

    record: Optional[MemberReputation] = _mock_reputation_db.get(member_id)
    if record is None:
        record = MemberReputation(member_id=member_id)
        _mock_reputation_db[member_id] = record

    record.score += delta
    record.history.append(
        ReputationEvent(
            action=action,
            points=delta,
            timestamp="2026-10-03T12:00:00Z",
            description=f"Action {action.value} applied",
        )
    )

    return record.score


def get_reputation_level(member_id: str) -> str:
    """Return the reputation tier label for a member.

    Args:
        member_id: Unique identifier of the community member.

    Returns:
        One of: newcomer, regular, established, veteran.
    """
    score: int = calculate_reputation(member_id)
    if score >= 200:
        return "veteran"
    elif score >= 100:
        return "established"
    elif score >= 30:
        return "regular"
    else:
        return "newcomer"


def get_reputation_history(member_id: str) -> List[ReputationEvent]:
    """Return the full reputation event history for a member.

    Args:
        member_id: Unique identifier of the community member.

    Returns:
        List of ReputationEvent objects (empty for unknown members).
    """
    record: Optional[MemberReputation] = _mock_reputation_db.get(member_id)
    if record is None:
        return []
    return list(record.history)
