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
        analytics.controls_by_status = self._count_by_attr(controls, "status")

        # Average compliance score
        if assessments:
            scores = [a.compliance_score for a in assessments if a.compliance_score > 0]
            analytics.compliance_score_avg = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Mean time to remediate
        analytics.mean_time_to_remediate_days = self._compute_mttr(findings)

        # Findings trend (monthly)
        analytics.findings_trend = self._compute_findings_trend(findings)

        # Top risk areas
        analytics.top_risk_areas = self._identify_top_risk_areas(findings, controls)

        return analytics

    # ------------------------------------------------------------------
    # Event analytics
    # ------------------------------------------------------------------

    def analyze_event_patterns(
        self, events: list[AuditEvent]
    ) -> dict[str, Any]:
        """Analyze event patterns for anomalies and trends."""
        if not events:
            return {"total": 0, "patterns": []}

        # Group by hour
        hourly: dict[int, int] = defaultdict(int)
        daily: dict[str, int] = defaultdict(int)
        by_actor: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)

        for event in events:
            try:
                dt = self._parse_date(event.timestamp)
                hourly[dt.hour] += 1
                daily[dt.strftime("%Y-%m-%d")] += 1
            except (ValueError, TypeError):
                pass
            by_actor[event.actor.id] += 1
            by_type[event.event_type.value] += 1
            by_severity[event.severity.value] += 1

        # Detect anomalies (unusual spikes)
        patterns = []
        if daily:
            avg_daily = sum(daily.values()) / len(daily)
            for date, count in daily.items():
                if count > avg_daily * 3:
                    patterns.append({
                        "type": "spike",
                        "date": date,
                        "count": count,
                        "average": round(avg_daily, 1),
                        "severity": "high" if count > avg_daily * 5 else "medium",
                    })

        # Detect after-hours activity
        after_hours = sum(count for hour, count in hourly.items() if hour < 6 or hour > 22)
        business_hours = sum(count for hour, count in hourly.items() if 6 <= hour <= 22)
        if after_hours > business_hours * 0.3:
            patterns.append({
                "type": "after_hours_activity",
                "after_hours_count": after_hours,
                "business_hours_count": business_hours,
                "ratio": round(after_hours / max(business_hours, 1), 2),
                "severity": "medium",
            })

        return {
            "total_events": len(events),
            "unique_actors": len(by_actor),
            "unique_event_types": len(by_type),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "by_actor_top10": dict(sorted(by_actor.items(), key=lambda x: -x[1])[:10]),
            "hourly_distribution": dict(hourly),
            "daily_distribution": dict(sorted(daily.items())),
            "patterns_detected": patterns,
        }

    # ------------------------------------------------------------------
    # Finding analytics
    # ------------------------------------------------------------------

    def analyze_findings(
        self, findings: list[Finding]
    ) -> dict[str, Any]:
        """Deep analysis of audit findings."""
        if not findings:
            return {"total": 0}

        by_severity: dict[str, int] = defaultdict(int)
        by_status: dict[str, int] = defaultdict(int)
        by_audit: dict[str, int] = defaultdict(int)
        by_control: dict[str, int] = defaultdict(int)
        aging_buckets = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}

        now = datetime.now(timezone.utc)
        for f in findings:
            by_severity[f.severity.value] += 1
            by_status[f.status.value] += 1
            if f.audit_id:
                by_audit[f.audit_id] += 1
            if f.control_id:
                by_control[f.control_id] += 1

            # Aging analysis for open findings
            if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS):
                try:
                    created = self._parse_date(f.created_at)
                    age_days = (now - created).days
                    if age_days <= 30:
                        aging_buckets["0-30"] += 1
                    elif age_days <= 60:
                        aging_buckets["31-60"] += 1
                    elif age_days <= 90:
                        aging_buckets["61-90"] += 1
                    else:
                        aging_buckets["90+"] += 1
                except (ValueError, TypeError):
                    pass

        # Remediation rate
        total_closed = by_status.get("closed", 0) + by_status.get("verified", 0)
        remediation_rate = round(total_closed / len(findings) * 100, 1) if findings else 0.0

        return {
            "total_findings": len(findings),
            "by_severity": dict(by_severity),
            "by_status": dict(by_status),
            "by_audit": dict(by_audit),
            "by_control_top10": dict(sorted(by_control.items(), key=lambda x: -x[1])[:10]),
            "open_aging": aging_buckets,
            "remediation_rate_pct": remediation_rate,
            "critical_open": sum(
                1 for f in findings
                if f.severity == FindingSeverity.CRITICAL
                and f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
            ),
        }

    def _compute_mttr(self, findings: list[Finding]) -> Optional[float]:
        """Compute mean time to remediate in days."""
        remediated = []
        for f in findings:
            if f.remediated_at and f.created_at:
                try:
                    created = self._parse_date(f.created_at)
                    fixed = self._parse_date(f.remediated_at)
                    remediated.append((fixed - created).days)
                except (ValueError, TypeError):
                    pass
        if not remediated:
            return None
        return round(sum(remediated) / len(remediated), 1)

    def _compute_findings_trend(
        self, findings: list[Finding]
    ) -> list[dict[str, Any]]:
        """Compute monthly findings trend."""
        monthly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for f in findings:
            try:
                dt = self._parse_date(f.created_at)
                month_key = dt.strftime("%Y-%m")
                monthly[month_key]["total"] += 1
                monthly[month_key][f.severity.value] += 1
            except (ValueError, TypeError):
                pass

        trend = []
        for month in sorted(monthly.keys()):
            data = monthly[month]
            trend.append({
                "month": month,
                "total": data["total"],
                "critical": data.get("critical", 0),
                "high": data.get("high", 0),
                "medium": data.get("medium", 0),
                "low": data.get("low", 0),
            })
        return trend

    # ------------------------------------------------------------------
    # Compliance analytics
    # ------------------------------------------------------------------

    def analyze_compliance_posture(
        self,
        controls: list[ComplianceControl],
        assessments: list[ComplianceAssessment],
    ) -> dict[str, Any]:
        """Analyze compliance posture across frameworks."""
        if not controls:
            return {"frameworks": []}

        by_framework: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "compliant": 0,
            "partially_compliant": 0,
            "non_compliant": 0,
            "not_assessed": 0,
            "not_applicable": 0,
            "compensating": 0,
            "score": 0.0,
        })

        for c in controls:
            fw = c.framework.value
            by_framework[fw]["total"] += 1
            if c.status == ControlStatus.COMPLIANT:
                by_framework[fw]["compliant"] += 1
            elif c.status == ControlStatus.PARTIALLY_COMPLIANT:
                by_framework[fw]["partially_compliant"] += 1
            elif c.status == ControlStatus.NON_COMPLIANT:
                by_framework[fw]["non_compliant"] += 1
            elif c.status == ControlStatus.NOT_ASSESSED:
                by_framework[fw]["not_assessed"] += 1
            elif c.status == ControlStatus.NOT_APPLICABLE:
                by_framework[fw]["not_applicable"] += 1
            elif c.status == ControlStatus.COMPENSATING_CONTROL:
                by_framework[fw]["compensating"] += 1

        # Compute scores
        frameworks = []
        for fw, data in by_framework.items():
            applicable = data["total"] - data["not_applicable"]
            if applicable > 0:
                data["score"] = round(
                    (data["compliant"] + 0.5 * data["partially_compliant"]) / applicable * 100, 2
                )
            frameworks.append({"framework": fw, **data})

        # Assessment history
        assessment_history = []
        for a in sorted(assessments, key=lambda x: x.created_at or ""):
            assessment_history.append({
                "assessment_id": a.assessment_id,
                "framework": a.framework.value,
                "name": a.assessment_name,
                "score": a.compliance_score,
                "date": a.created_at,
                "status": a.status.value,
            })

        return {
            "frameworks": frameworks,
            "assessment_history": assessment_history,
            "overall_score": round(
                sum(f["score"] for f in frameworks) / len(frameworks), 2
            ) if frameworks else 0.0,
        }

    # ------------------------------------------------------------------
    # Risk area identification
    # ------------------------------------------------------------------

    def _identify_top_risk_areas(
        self,
        findings: list[Finding],
        controls: list[ComplianceControl],
    ) -> list[dict[str, Any]]:
        """Identify top risk areas based on finding density and severity."""
        # Map control_id -> control info
        control_map = {c.control_id: c for c in controls}

        # Group findings by control
        by_control: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            if f.control_id:
                by_control[f.control_id].append(f)

        risk_areas = []
        severity_weights = {
            FindingSeverity.CRITICAL: 10,
            FindingSeverity.HIGH: 5,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 1,
            FindingSeverity.INFORMATIONAL: 0,
        }

        for control_id, control_findings in by_control.items():
            control = control_map.get(control_id)
            if not control:
                continue

            # Compute risk score
            score = sum(severity_weights.get(f.severity, 0) for f in control_findings)
            open_count = sum(
                1 for f in control_findings
                if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS)
            )

            risk_areas.append({
                "control_id": control_id,
                "control_identifier": control.control_identifier,
                "control_title": control.title,
                "framework": control.framework.value,
                "total_findings": len(control_findings),
                "open_findings": open_count,
                "risk_score": score,
                "max_severity": max(
                    (f.severity.value for f in control_findings),
                    key=lambda s: severity_weights.get(FindingSeverity(s), 0),
                ) if control_findings else None,
            })

        # Sort by risk score descending
        risk_areas.sort(key=lambda x: -x["risk_score"])
        return risk_areas[:10]

    # ------------------------------------------------------------------
    # Evidence analytics
    # ------------------------------------------------------------------

    def analyze_evidence_coverage(
        self,
        evidence: list[Evidence],
        controls: list[ComplianceControl],
    ) -> dict[str, Any]:
        """Analyze evidence coverage across controls."""
        # Map evidence to controls
        evidence_by_control: dict[str, list[str]] = defaultdict(list)
        for ev in evidence:
            for cid in ev.control_ids:
                evidence_by_control[cid].append(ev.evidence_id)

        # Controls without evidence
        controls_without_evidence = []
        controls_with_evidence = []
        for c in controls:
            ev_ids = evidence_by_control.get(c.control_id, [])
            if not ev_ids:
                controls_without_evidence.append({
                    "control_id": c.control_id,
                    "identifier": c.control_identifier,
                    "title": c.title,
                    "status": c.status.value,
                })
            else:
                controls_with_evidence.append({
                    "control_id": c.control_id,
                    "identifier": c.control_identifier,
                    "title": c.title,
                    "evidence_count": len(ev_ids),
                    "status": c.status.value,
                })

        # Evidence status distribution
        by_status: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        for ev in evidence:
            by_status[ev.status.value] += 1
            by_type[ev.evidence_type.value] += 1

        total_controls = len(controls)
        coverage_pct = round(
            (total_controls - len(controls_without_evidence)) / total_controls * 100, 1
        ) if total_controls > 0 else 0.0

        return {
            "total_controls": total_controls,
            "controls_with_evidence": len(controls_with_evidence),
            "controls_without_evidence": len(controls_without_evidence),
            "coverage_pct": coverage_pct,
            "evidence_by_status": dict(by_status),
            "evidence_by_type": dict(by_type),
            "total_evidence_items": len(evidence),
            "uncovered_controls": controls_without_evidence,
        }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def generate_dashboard(
        self,
        events: list[AuditEvent],
        audits: list[AuditEngagement],
        findings: list[Finding],
        evidence: list[Evidence],
        controls: list[ComplianceControl],
        assessments: list[ComplianceAssessment],
    ) -> dict[str, Any]:
        """Generate a comprehensive audit dashboard."""
        analytics = self.compute_analytics(
            events, audits, findings, evidence, controls, assessments
        )
        event_patterns = self.analyze_event_patterns(events)
        finding_analysis = self.analyze_findings(findings)
        compliance_posture = self.analyze_compliance_posture(controls, assessments)
        evidence_coverage = self.analyze_evidence_coverage(evidence, controls)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_events": analytics.total_events,
                "total_audits": analytics.total_audits,
                "active_audits": analytics.active_audits,
                "total_findings": analytics.total_findings,
                "open_findings": analytics.open_findings,
                "overdue_findings": analytics.overdue_findings,
                "total_evidence": analytics.total_evidence,
                "total_controls": analytics.total_controls,
                "compliance_score_avg": analytics.compliance_score_avg,
                "mean_time_to_remediate_days": analytics.mean_time_to_remediate_days,
            },
            "findings": finding_analysis,
            "events": event_patterns,
            "compliance": compliance_posture,
            "evidence": evidence_coverage,
            "findings_trend": analytics.findings_trend,
            "top_risk_areas": analytics.top_risk_areas,
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_analytics_json(self, analytics: AuditAnalytics) -> str:
        """Export analytics as JSON."""
        return json.dumps(self._analytics_to_dict(analytics), indent=2, default=str)

    def _analytics_to_dict(self, analytics: AuditAnalytics) -> dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "period_start": analytics.period_start,
            "period_end": analytics.period_end,
            "total_events": analytics.total_events,
            "events_by_type": analytics.events_by_type,
            "events_by_severity": analytics.events_by_severity,
            "total_audits": analytics.total_audits,
            "active_audits": analytics.active_audits,
            "completed_audits": analytics.completed_audits,
            "total_findings": analytics.total_findings,
            "open_findings": analytics.open_findings,
            "closed_findings": analytics.closed_findings,
            "overdue_findings": analytics.overdue_findings,
            "findings_by_severity": analytics.findings_by_severity,
            "findings_by_status": analytics.findings_by_status,
            "total_evidence": analytics.total_evidence,
            "evidence_by_type": analytics.evidence_by_type,
            "evidence_by_status": analytics.evidence_by_status,
            "total_controls": analytics.total_controls,
            "controls_by_status": analytics.controls_by_status,
            "compliance_score_avg": analytics.compliance_score_avg,
            "mean_time_to_remediate_days": analytics.mean_time_to_remediate_days,
            "findings_trend": analytics.findings_trend,
            "top_risk_areas": analytics.top_risk_areas,
            "generated_at": analytics.generated_at,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _count_by_attr(self, items: list, attr_name: str) -> dict[str, int]:
        """Count items by an attribute."""
        counts: dict[str, int] = defaultdict(int)
        for item in items:
            val = getattr(item, attr_name, None)
            if val is not None:
                if hasattr(val, "value"):
                    counts[val.value] += 1
                else:
                    counts[str(val)] += 1
        return dict(counts)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse an ISO date string."""
        return datetime.fromisoformat(date_str)
