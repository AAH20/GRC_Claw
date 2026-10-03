"""Compliance Monitor Agent for Gated Communities.

Monitors community compliance against governance policies, regulatory
requirements, and internal standards. Provides status checks and detailed
compliance reports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ComplianceStatus(str, Enum):
    """Overall compliance status for a community."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AT_RISK = "at_risk"
    PENDING_REVIEW = "pending_review"


class PolicyCategory(str, Enum):
    """Categories of compliance policies."""

    DATA_PRIVACY = "data_privacy"
    ACCESS_CONTROL = "access_control"
    CONTENT_MODERATION = "content_moderation"
    AUDIT_TRAIL = "audit_trail"
    MEMBER_VERIFICATION = "member_verification"
    RETENTION = "retention"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PolicyViolation:
    """Represents a single policy violation."""

    policy_id: str
    category: PolicyCategory
    severity: PolicySeverity
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    remediation: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None


@dataclass
class ComplianceCheckResult:
    """Result of a compliance check for a community."""

    community_id: str
    community_name: str
    status: ComplianceStatus
    checked_at: datetime
    score: float  # 0.0 – 100.0
    total_policies: int
    passed_policies: int
    failed_policies: int
    violations: List[PolicyViolation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Detailed compliance report for a community."""

    report_id: str
    community_id: str
    community_name: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    overall_score: float
    summary: str
    category_breakdown: Dict[str, Dict[str, Any]]
    violations: List[PolicyViolation]
    recommendations: List[str]
    next_review_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

_MOCK_COMMUNITIES: Dict[str, Dict[str, Any]] = {
    "comm_001": {
        "name": "Engineering Guild",
        "member_count": 342,
        "created_at": datetime(2024, 3, 15, tzinfo=timezone.utc),
        "policies": {
            PolicyCategory.DATA_PRIVACY: {"passed": True, "last_audit": "2026-09-15"},
            PolicyCategory.ACCESS_CONTROL: {"passed": True, "last_audit": "2026-09-20"},
            PolicyCategory.CONTENT_MODERATION: {"passed": True, "last_audit": "2026-09-10"},
            PolicyCategory.AUDIT_TRAIL: {"passed": True, "last_audit": "2026-09-25"},
            PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-18"},
            PolicyCategory.RETENTION: {"passed": True, "last_audit": "2026-09-22"},
        },
        "violations": [],
    },
    "comm_002": {
        "name": "Product Leaders Forum",
        "member_count": 89,
        "created_at": datetime(2025, 1, 10, tzinfo=timezone.utc),
        "policies": {
            PolicyCategory.DATA_PRIVACY: {"passed": True, "last_audit": "2026-09-12"},
            PolicyCategory.ACCESS_CONTROL: {"passed": False, "last_audit": "2026-09-28"},
            PolicyCategory.CONTENT_MODERATION: {"passed": True, "last_audit": "2026-09-14"},
            PolicyCategory.AUDIT_TRAIL: {"passed": False, "last_audit": "2026-09-28"},
            PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-16"},
            PolicyCategory.RETENTION: {"passed": True, "last_audit": "2026-09-20"},
        },
        "violations": [
            PolicyViolation(
                policy_id="POL-AC-001",
                category=PolicyCategory.ACCESS_CONTROL,
                severity=PolicySeverity.HIGH,
                description="Inactive admin accounts not deactivated within 30 days",
                detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=timezone.utc),
                remediation="Review and deactivate inactive admin accounts",
            ),
            PolicyViolation(
                policy_id="POL-AT-003",
                category=PolicyCategory.AUDIT_TRAIL,
                severity=PolicySeverity.MEDIUM,
                description="Audit log retention period below 90-day minimum",
                detected_at=datetime(2026, 9, 28, 14, 30, tzinfo=timezone.utc),
                remediation="Extend audit log retention to meet 90-day policy",
            ),
        ],
    },
    "comm_003": {
        "name": "Design Circle",
        "member_count": 156,
        "created_at": datetime(2024, 8, 22, tzinfo=timezone.utc),
        "policies": {
            PolicyCategory.DATA_PRIVACY: {"passed": False, "last_audit": "2026-09-30"},
            PolicyCategory.ACCESS_CONTROL: {"passed": True, "last_audit": "2026-09-25"},
            PolicyCategory.CONTENT_MODERATION: {"passed": False, "last_audit": "2026-09-30"},
            PolicyCategory.AUDIT_TRAIL: {"passed": True, "last_audit": "2026-09-27"},
            PolicyCategory.MEMBER_VERIFICATION: {"passed": True, "last_audit": "2026-09-19"},
            PolicyCategory.RETENTION: {"passed": False, "last_audit": "2026-09-30"},
        },
        "violations": [
            PolicyViolation(
                policy_id="POL-DP-002",
                category=PolicyCategory.DATA_PRIVACY,
                severity=PolicySeverity.CRITICAL,
                description="Member PII stored without encryption at rest",
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                remediation="Enable AES-256 encryption for all PII data stores",
            ),
            PolicyViolation(
                policy_id="POL-CM-001",
                category=PolicyCategory.CONTENT_MODERATION,
                severity=PolicySeverity.HIGH,
                description="Content moderation queue backlog exceeds 48 hours",
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                remediation="Increase moderation staff or implement automated triage",
            ),
            PolicyViolation(
                policy_id="POL-RT-001",
                category=PolicyCategory.RETENTION,
                severity=PolicySeverity.MEDIUM,
                description="Data retention schedule not enforced for deleted content",
                detected_at=datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc),
                remediation="Implement automated retention policy enforcement",
            ),
        ],
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _get_community_mock(community_id: str) -> Dict[str, Any]:
    """Retrieve mock community data, generating defaults for unknown IDs."""
    if community_id in _MOCK_COMMUNITIES:
        return _MOCK_COMMUNITIES[community_id]
    # Generate deterministic mock data for unknown community IDs
    return {
        "name": f"Community {community_id}",
        "member_count": 50,
        "created_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
        "policies": {
            cat: {"passed": True, "last_audit": "2026-09-15"}
            for cat in PolicyCategory
        },
        "violations": [],
    }


def _calculate_score(passed: int, total: int) -> float:
    """Calculate compliance score as a percentage."""
    if total == 0:
        return 100.0
    return round((passed / total) * 100, 1)


def _determine_status(score: float, violations: List[PolicyViolation]) -> ComplianceStatus:
    """Determine overall compliance status from score and violations."""
    has_critical = any(v.severity == PolicySeverity.CRITICAL and not v.is_resolved for v in violations)
    has_high = any(v.severity == PolicySeverity.HIGH and not v.is_resolved for v in violations)

    if has_critical or score < 50:
        return ComplianceStatus.NON_COMPLIANT
    if has_high or score < 75:
        return ComplianceStatus.AT_RISK
    if score < 90:
        return ComplianceStatus.PENDING_REVIEW
    return ComplianceStatus.COMPLIANT


def _generate_recommendations(violations: List[PolicyViolation]) -> List[str]:
    """Generate remediation recommendations from violations."""
    recommendations: List[str] = []
    for v in violations:
        if not v.is_resolved and v.remediation:
            recommendations.append(f"[{v.severity.value.upper()}] {v.remediation}")
    if not recommendations:
        recommendations.append("No immediate action required. Continue regular monitoring.")
    return recommendations


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_compliance(community_id: str) -> ComplianceCheckResult:
    """Check compliance status for a given community.

    Args:
        community_id: Unique identifier of the community to check.

    Returns:
        ComplianceCheckResult with status, score, and any violations.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    community = _get_community_mock(community_id)
    policies: Dict[PolicyCategory, Dict[str, Any]] = community["policies"]
    violations: List[PolicyViolation] = community.get("violations", [])

    total = len(policies)
    passed = sum(1 for p in policies.values() if p["passed"])
    failed = total - passed
    score = _calculate_score(passed, total)
    status = _determine_status(score, violations)
    recommendations = _generate_recommendations(violations)

    return ComplianceCheckResult(
        community_id=community_id,
        community_name=community["name"],
        status=status,
        checked_at=datetime.now(timezone.utc),
        score=score,
        total_policies=total,
        passed_policies=passed,
        failed_policies=failed,
        violations=violations,
        recommendations=recommendations,
    )


def generate_compliance_report(community_id: str) -> ComplianceReport:
    """Generate a detailed compliance report for a given community.

    Args:
        community_id: Unique identifier of the community.

    Returns:
        ComplianceReport with full breakdown, violations, and recommendations.

    Raises:
        ValueError: If community_id is empty or None.
    """
    if not community_id:
        raise ValueError("community_id must be a non-empty string")

    check_result = check_compliance(community_id)
    community = _get_community_mock(community_id)
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=30)

    # Build category breakdown
    category_breakdown: Dict[str, Dict[str, Any]] = {}
    policies: Dict[PolicyCategory, Dict[str, Any]] = community["policies"]
    for cat, info in policies.items():
        cat_violations = [v for v in check_result.violations if v.category == cat]
        category_breakdown[cat.value] = {
            "status": "pass" if info["passed"] else "fail",
            "last_audit": info["last_audit"],
            "violation_count": len(cat_violations),
            "violations": [
                {
                    "policy_id": v.policy_id,
                    "severity": v.severity.value,
                    "description": v.description,
                    "detected_at": v.detected_at.isoformat(),
                    "resolved": v.is_resolved,
                }
                for v in cat_violations
            ],
        }

    # Build summary text
    if check_result.status == ComplianceStatus.COMPLIANT:
        summary = (
            f"Community '{check_result.community_name}' is fully compliant "
            f"with a score of {check_result.score}% across {check_result.total_policies} policies."
        )
    elif check_result.status == ComplianceStatus.AT_RISK:
        summary = (
            f"Community '{check_result.community_name}' is at risk with a score of "
            f"{check_result.score}%. {check_result.failed_policies} policy(s) require attention."
        )
    elif check_result.status == ComplianceStatus.NON_COMPLIANT:
        summary = (
            f"Community '{check_result.community_name}' is non-compliant with a score of "
            f"{check_result.score}%. Immediate remediation required for "
            f"{check_result.failed_policies} policy violation(s)."
        )
    else:
        summary = (
            f"Community '{check_result.community_name}' is pending review with a score of "
            f"{check_result.score}%."
        )

    return ComplianceReport(
        report_id=str(uuid.uuid4()),
        community_id=community_id,
        community_name=check_result.community_name,
        generated_at=now,
        period_start=period_start,
        period_end=now,
        overall_status=check_result.status,
        overall_score=check_result.score,
        summary=summary,
        category_breakdown=category_breakdown,
        violations=check_result.violations,
        recommendations=check_result.recommendations,
        next_review_date=now + timedelta(days=30),
        metadata={
            "member_count": community["member_count"],
            "community_created_at": community["created_at"].isoformat(),
            "report_version": "1.0",
        },
    )
