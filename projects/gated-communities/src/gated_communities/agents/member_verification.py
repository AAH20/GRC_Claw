"""Member verification agent for gated communities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class VerificationStatus(str, Enum):
    """Possible verification statuses for a community member."""

    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    NOT_FOUND = "not_found"


@dataclass
class MemberProfile:
    """Represents a member's verification profile."""

    member_id: str
    display_name: str
    email: str
    status: VerificationStatus
    verified_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    trust_score: float = 0.0
    badges: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

_MOCK_MEMBERS: Dict[str, MemberProfile] = {
    "mbr_001": MemberProfile(
        member_id="mbr_001",
        display_name="Alice Chen",
        email="alice.chen@example.com",
        status=VerificationStatus.VERIFIED,
        verified_at="2025-09-15T10:30:00Z",
        trust_score=0.95,
        badges=["early_adopter", "contributor"],
    ),
    "mbr_002": MemberProfile(
        member_id="mbr_002",
        display_name="Bob Martinez",
        email="bob.martinez@example.com",
        status=VerificationStatus.PENDING,
        trust_score=0.42,
        badges=[],
    ),
    "mbr_003": MemberProfile(
        member_id="mbr_003",
        display_name="Carol Davis",
        email="carol.davis@example.com",
        status=VerificationStatus.REJECTED,
        rejection_reason="Incomplete identity documentation",
        trust_score=0.15,
        badges=[],
    ),
    "mbr_004": MemberProfile(
        member_id="mbr_004",
        display_name="David Kim",
        email="david.kim@example.com",
        status=VerificationStatus.SUSPENDED,
        trust_score=0.30,
        badges=["contributor"],
    ),
    "mbr_005": MemberProfile(
        member_id="mbr_005",
        display_name="Eve Johnson",
        email="eve.johnson@example.com",
        status=VerificationStatus.VERIFIED,
        verified_at="2025-10-01T08:00:00Z",
        trust_score=0.88,
        badges=["moderator", "early_adopter"],
    ),
}


def _generate_member_id() -> str:
    """Generate a unique member ID for new/unregistered lookups."""
    return f"mbr_{uuid.uuid4().hex[:8]}"


def verify_member(member_id: str) -> Dict[str, object]:
    """Verify a single member and return their verification status.

    Args:
        member_id: The unique identifier of the member to verify.

    Returns:
        A dictionary containing the member's verification details including
        status, trust score, badges, and any relevant metadata.
    """
    if not member_id or not isinstance(member_id, str):
        return {
            "member_id": member_id,
            "status": VerificationStatus.NOT_FOUND.value,
            "display_name": None,
            "trust_score": 0.0,
            "badges": [],
            "verified_at": None,
            "rejection_reason": None,
            "error": "Invalid member_id provided",
        }

    profile = _MOCK_MEMBERS.get(member_id)

    if profile is None:
        return {
            "member_id": member_id,
            "status": VerificationStatus.NOT_FOUND.value,
            "display_name": None,
            "trust_score": 0.0,
            "badges": [],
            "verified_at": None,
            "rejection_reason": None,
            "error": "Member not found in registry",
        }

    return {
        "member_id": profile.member_id,
        "status": profile.status.value,
        "display_name": profile.display_name,
        "email": profile.email,
        "trust_score": profile.trust_score,
        "badges": list(profile.badges),
        "verified_at": profile.verified_at,
        "rejection_reason": profile.rejection_reason,
    }


def batch_verify(member_ids: List[str]) -> Dict[str, object]:
    """Verify multiple members in a batch and return aggregated results.

    Args:
        member_ids: A list of unique member identifiers to verify.

    Returns:
        A dictionary containing individual results for each member and
        summary statistics (counts by status, total processed).
    """
    if not member_ids:
        return {
            "results": [],
            "summary": {
                "total": 0,
                "verified": 0,
                "pending": 0,
                "rejected": 0,
                "suspended": 0,
                "not_found": 0,
            },
        }

    results: List[Dict[str, object]] = []
    summary: Dict[str, int] = {
        "total": len(member_ids),
        "verified": 0,
        "pending": 0,
        "rejected": 0,
        "suspended": 0,
        "not_found": 0,
    }

    for mid in member_ids:
        result = verify_member(mid)
        results.append(result)

        status = result.get("status", VerificationStatus.NOT_FOUND.value)
        if status in summary:
            summary[status] += 1  # type: ignore[literal-required]

    return {
        "results": results,
        "summary": summary,
    }
