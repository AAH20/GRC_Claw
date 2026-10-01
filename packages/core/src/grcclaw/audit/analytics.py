"""
Audit analytics — aggregate, trend, and analyze audit data for insights.

Provides dashboards, metrics, trend analysis, and risk area identification
across audit engagements, findings, evidence, and compliance controls.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .models import (
    AuditEngagement,
    AuditEvent,
    AuditEventSeverity,
    AuditEventType,
    AuditStatus,
    AuditAnalytics,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ControlStatus,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    Finding,
    FindingSeverity,
    FindingStatus,
)


class AuditAnalyticsEngine:
    """
    Analytics engine for audit data.

    Features:
    - Event aggregation and trend analysis
    - Finding metrics (MTTR, aging, distribution)
    - Compliance score tracking
    - Risk area identification
    - Evidence coverage analysis
    - Audit engagement metrics
    - Exportable analytics reports
    """

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Core analytics
    # ------------------------------------------------------------------

    def compute_analytics(
        self,
        events: list[AuditEvent],
        audits: list[AuditEngagement],
        findings: list[Finding],
        evidence: list[Evidence],
        controls: list[ComplianceControl],
        assessments: list[ComplianceAssessment],
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> AuditAnalytics:
        """
        Compute comprehensive audit analytics.

        Aggregates all audit data into a single analytics snapshot.
        """
        analytics = AuditAnalytics(
            period_start=period_start,
            period_end=period_end,
        )

        # Event analytics
        analytics.total_events = len(events)
        analytics.events_by_type = self._count_by_attr(events, "event_type")
        analytics.events_by_severity = self._count_by_attr(events, "severity")

        # Audit analytics
        analytics.total_audits = len(audits)
        analytics.active_audits = sum(
            1 for a in audits if a.status not in (AuditStatus.CLOSED, AuditStatus.ARCHIVED)
        )
        analytics.completed_audits = sum(
            1 for a in audits if a.status == AuditStatus.CLOSED
        )

        # Finding analytics
        analytics.total_findings = len(findings)
        analytics.open_findings = sum(
            1 for f in findings
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
        )
        analytics.closed_findings = sum(
            1 for f in findings
            if f.status in (FindingStatus.CLOSED, FindingStatus.VERIFIED)
        )
        analytics.findings_by_severity = self._count_by_attr(findings, "severity")
        analytics.findings_by_status = self._count_by_attr(findings, "status")

        # Overdue findings
        now = datetime.now(timezone.utc)
        analytics.overdue_findings = sum(
            1 for f in findings
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
            and f.due_date
            and self._parse_date(f.due_date) < now
        )

        # Evidence analytics
        analytics.total_evidence = len(evidence)
        analytics.evidence_by_type = self._count_by_attr(evidence, "evidence_type")
        analytics.evidence_by_status = self._count_by_attr(evidence, "status")

        # Control analytics
        analytics.total_controls = len(controls)
        analytics.</longcat_think>
