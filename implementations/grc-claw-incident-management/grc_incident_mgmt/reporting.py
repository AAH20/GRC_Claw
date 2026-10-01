"""
GRC_Claw Incident Reporting (§6 of GRC-AIM-001)

Implements standardized incident reporting:
    • Incident report structure (§6.1)
    • Severity summary report (§6.2)
    • EU AI Act Article 73 reporting (§6.3)
    • Internal reporting cadence (§6.4)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from .models import (
    Incident,
    IncidentReport,
    IncidentStatus,
    Severity,
    ImpactAssessment,
    RootCause,
    ResponseAction,
    Evidence,
    Recommendation,
    RegulatoryAssessment,
)
from .taxonomy import IncidentCategory


# ═══════════════════════════════════════════════════════════════════════════════
# Incident Report Generator (§6.1)
# ═══════════════════════════════════════════════════════════════════════════════

class IncidentReportGenerator:
    """
    Generates standardized incident reports (§6.1).

    Every AI incident report follows a standardized format to ensure
    consistency, completeness, and regulatory compliance.
    """

    def generate(self, incident: Incident) -> IncidentReport:
        """Generate a complete incident report from an incident record."""
        return incident.to_report()

    def generate_json(self, incident: Incident) -> str:
        """Generate a JSON-formatted incident report."""
        report = self.generate(incident)
        return json.dumps(report.to_dict(), indent=2)

    def generate_executive_summary(self, incident: Incident) -> dict[str, Any]:
        """Generate a condensed severity summary for executive/board reporting (§6.2)."""
        return {
            "incident_id": incident.incident_id,
            "date_time": incident.detected_at,
            "category": incident.category.value if incident.category else "Unknown",
            "severity": incident.severity.value,
            "status": incident.status.value,
            "affected_systems": len(incident.affected_assets),
            "affected_system_names": [a.asset_name for a in incident.affected_assets],
            "individuals_affected": incident.impact_assessment.individuals_affected,
            "data_breached": incident.impact_assessment.records_affected > 0,
            "data_types": incident.impact_assessment.data_types,
            "financial_impact_usd": incident.impact_assessment.financial_impact_usd,
            "regulatory_notification": self._regulatory_notification_summary(incident),
            "summary": incident.summary or self._generate_summary(incident),
            "root_cause": incident.root_cause.description,
            "actions_taken": incident.containment_actions + incident.eradication_actions,
            "next_steps": self._generate_next_steps(incident),
        }

    def _regulatory_notification_summary(self, incident: Incident) -> dict[str, Any]:
        ra = incident.regulatory_assessment
        return {
            "required": ra.eu_ai_act_applicable and ra.article_73_triggered,
            "deadline": ra.notification_deadline,
            "submitted": ra.notification_submitted,
            "notification_date": ra.notification_date,
        }

    def _generate_summary(self, incident: Incident) -> str:
        cat = incident.category.value if incident.category else "Unknown"
        sev = incident.severity.value
        assets = ", ".join(a.asset_name for a in incident.affected_assets) or "N/A"
        return f"{sev} {cat} incident affecting {assets}. Status: {incident.status.value}."

    def _generate_next_steps(self, incident: Incident) -> list[str]:
        steps = []
        if incident.status != IncidentStatus.CONTAINED:
            steps.append("Complete containment actions")
        if incident.status != IncidentStatus.ERADICATED:
            steps.append("Complete eradication and root cause analysis")
        if incident.status != IncidentStatus.RECOVERED:
            steps.append("Execute recovery plan and validate service restoration")
        if incident.status != IncidentStatus.CLOSED:
            steps.append("Conduct post-incident review")
        if incident.regulatory_assessment.article_73_triggered and not incident.regulatory_assessment.notification_submitted:
            steps.append(f"Submit EU AI Act Art. 73 notification by {incident.regulatory_assessment.notification_deadline}")
        return steps


# ═══════════════════════════════════════════════════════════════════════════════
# EU AI Act Article 73 Reporting (§6.3)
# ═══════════════════════════════════════════════════════════════════════════════

class Article73Reporter:
    """
    EU AI Act Article 73 reporting (§6.3).

    Assesses incidents against Article 73 criteria and generates
    notifications to the national market surveillance authority.
    """

    # Article 73 serious incident criteria (§6.3.1)
    CRITERIA = {
        "death_or_serious_harm": "Incident caused or could have caused death or serious injury",
        "critical_infrastructure": "Incident affected critical infrastructure or essential services",
        "fundamental_rights": "Incident violated fundamental rights of individuals",
        "widespread_disruption": "Incident caused widespread disruption to economic or social activities",
        "market_integrity": "Incident affected the integrity of the AI market or public trust",
    }

    # Notification deadlines (§6.3.2)
    DEADLINES = {
        Severity.S1_CRITICAL: timedelta(hours=24),
        Severity.S2_HIGH: timedelta(hours=72),
        Severity.S3_MEDIUM: timedelta(hours=72),  # Assessed case-by-case
    }

    def assess_applicability(self, incident: Incident) -> dict[str, Any]:
        """Assess whether Article 73 reporting is required."""
        criteria_met = []
        impact = incident.impact_assessment

        if impact.individuals_affected > 0:
            criteria_met.append("death_or_serious_harm")
        if any(a.environment == "production" for a in incident.affected_assets):
            criteria_met.append("critical_infrastructure")
        if "pii" in impact.data_types or "phi" in impact.data_types:
            criteria_met.append("fundamental_rights")
        if impact.individuals_affected > 1000:
            criteria_met.append("widespread_disruption")
        if impact.reputational_impact and "severe" in impact.reputational_impact.lower():
            criteria_met.append("market_integly")

        applicable = len(criteria_met) > 0
        deadline = self.DEADLINES.get(incident.severity, timedelta(hours=72))

        return {
            "applicable": applicable,
            "criteria_met": criteria_met,
            "criteria_descriptions": [self.CRITERIA[c] for c in criteria_met],
            "deadline_hours": deadline.total_seconds() / 3600,
            "deadline_timestamp": (datetime.fromisoformat(incident.detected_at.replace("Z", "+00:00")) + deadline).isoformat() if incident.detected_at else "",
            "recipient": "national_market_surveillance_authority",
        }

    def generate_notification(self, incident: Incident) -> dict[str, Any]:
        """Generate Article 73 notification content (§6.3.3)."""
        assessment = self.assess_applicability(incident)

        return {
            "notification_type": "EU_AI_ACT_ARTICLE_73",
            "incident_id": incident.incident_id,
            "assessment": assessment,
            "content": {
                "incident_description": incident.summary or self._generate_description(incident),
                "ai_system_identification": {
                    "name": incident.affected_assets[0].asset_name if incident.affected_assets else "Unknown",
                    "version": incident.affected_assets[0].version if incident.affected_assets else "Unknown",
                    "risk_category": incident.category.value if incident.category else "Unknown",
                    "provider": "GRC_Claw",
                },
                "incident_cause": incident.root_cause.description or "Under investigation",
                "impact_assessment": {
                    "harm_caused": incident.impact_assessment.operational_impact,
                    "individuals_affected": incident.impact_assessment.individuals_affected,
                    "data_types_affected": incident.impact_assessment.data_types,
                },
                "corrective_actions": incident.eradication_actions + incident.containment_actions,
                "cross_border_impact": incident.regulatory_assessment.other_regulations,
                "contact_information": {
                    "responsible_person": "GRC_Claw Compliance Officer",
                    "email": "compliance@grc-claw.example",
                },
            },
            "submission_status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_description(self, incident: Incident) -> str:
        cat = incident.category.value if incident.category else "Unknown"
        sev = incident.severity.value
        return f"{sev} {cat} incident detected on {incident.detected_at}. Status: {incident.status.value}."


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Reporting Cadence (§6.4)
# ═══════════════════════════════════════════════════════════════════════════════

class ReportingCadence:
    """
    Internal reporting cadence (§6.4).

    Manages the frequency and audience of incident reports:
    • Incident Alert — Immediate (S1/S2)
    • Status Update — Every 4 hours (active S1/S2)
    • Incident Summary — Within 24 hours of closure
    • Post-Incident Report — Within 14 days of closure
    • Monthly Incident Report — Monthly
    • Quarterly Incident Report — Quarterly
    • Annual Incident Report — Annually
    """

    def __init__(self) -> None:
        self._schedule: list[dict[str, Any]] = []
        self._reports_sent: list[dict[str, Any]] = []

    def schedule_incident_alert(self, incident: Incident, recipients: list[str]) -> dict[str, Any]:
        """Schedule an immediate incident alert."""
        entry = {
            "report_type": "incident_alert",
            "incident_id": incident.incident_id,
            "severity": incident.severity.value,
            "recipients": recipients,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }
        self._schedule.append(entry)
        return entry

    def schedule_status_update(self, incident: Incident, recipients: list[str]) -> dict[str, Any]:
        """Schedule a status update (every 4 hours for active S1/S2)."""
        entry = {
            "report_type": "status_update",
            "incident_id": incident.incident_id,
            "severity": incident.severity.value,
            "recipients": recipients,
            "frequency_hours": 4,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }
        self._schedule.append(entry)
        return entry

    def schedule_incident_summary(self, incident: Incident, recipients: list[str]) -> dict[str, Any]:
        """Schedule an incident summary (within 24 hours of closure)."""
        entry = {
            "report_type": "incident_summary",
            "incident_id": incident.incident_id,
            "severity": incident.severity.value,
            "recipients": recipients,
            "deadline_hours": 24,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }
        self._schedule.append(entry)
        return entry

    def schedule_post_incident_report(self, incident: Incident, recipients: list[str]) -> dict[str, Any]:
        """Schedule a post-incident report (within 14 days of closure)."""
        entry = {
            "report_type": "post_incident_report",
            "incident_id": incident.incident_id,
            "severity": incident.severity.value,
            "recipients": recipients,
            "deadline_days": 14,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }
        self._schedule.append(entry)
        return entry

    def get_pending_reports(self) -> list[dict[str, Any]]:
        return [r for r in self._schedule if r["status"] == "scheduled"]

    def mark_sent(self, report_type: str, incident_id: str) -> None:
        for r in self._schedule:
            if r["report_type"] == report_type and r["incident_id"] == incident_id:
                r["status"] = "sent"
                r["sent_at"] = datetime.now(timezone.utc).isoformat()
                self._reports_sent.append(r)
                break


# ═══════════════════════════════════════════════════════════════════════════════
# Report Formatter
# ═══════════════════════════════════════════════════════════════════════════════

class ReportFormatter:
    """Formats incident reports for different audiences."""

    @staticmethod
    def to_markdown(report: IncidentReport) -> str:
        """Convert incident report to Markdown format."""
        data = report.to_dict()["incident_report"]
        lines = [
            f"# Incident Report: {data['incident_id']}",
            "",
            f"**Report ID:** {data['report_id']}  ",
            f"**Version:** {data['version']}  ",
            f"**Status:** {data['status']}  ",
            "",
            "## Classification",
            f"- **Category:** {data['classification']['category']}",
            f"- **Subcategory:** {data['classification']['subcategory']}",
            f"- **Severity:** {data['classification']['severity']}",
            f"- **Confidence:** {data['classification']['confidence']:.2f}",
            "",
            "## Timeline",
        ]
        timeline = data["timeline"]
        for key, value in timeline.items():
            if value:
                lines.append(f"- **{key}:** {value}")

        lines.extend(["", "## Affected Assets"])
        for asset in data.get("affected_assets", []):
            lines.append(f"- {asset.get('asset_name', 'Unknown')} ({asset.get('asset_type', 'unknown')}) — {asset.get('environment', 'unknown')}")

        lines.extend(["", "## Impact Assessment"])
        impact = data.get("impact_assessment", {})
        lines.append(f"- **Individuals Affected:** {impact.get('individuals_affected', 0)}")
        lines.append(f"- **Records Affected:** {impact.get('records_affected', 0)}")
        lines.append(f"- **Financial Impact:** ${impact.get('financial_impact_usd', 0):,.2f}")

        lines.extend(["", "## Root Cause"])
        rc = data.get("root_cause", {})
        lines.append(f"- **Category:** {rc.get('category', 'unknown')}")
        lines.append(f"- **Description:** {rc.get('description', 'N/A')}")

        lines.extend(["", "## Lessons Learned"])
        for lesson in data.get("lessons_learned", []):
            lines.append(f"- {lesson}")

        lines.extend(["", "## Recommendations"])
        for rec in data.get("recommendations", []):
            lines.append(f"- [{rec.get('priority', 'unknown')}] {rec.get('description', 'N/A')} (Owner: {rec.get('owner', 'TBD')}, Due: {rec.get('due_date', 'TBD')})")

        return "\n".join(lines)

    @staticmethod
    def to_csv_summary(reports: list[IncidentReport]) -> str:
        """Generate a CSV summary of multiple incident reports."""
        lines = ["incident_id,category,subcategory,severity,status,detected_at,individuals_affected,financial_impact_usd"]
        for r in reports:
            data = r.to_dict()["incident_report"]
            impact = data.get("impact_assessment", {})
            lines.append(
                f"{data['incident_id']},{data['classification']['category']},"
                f"{data['classification']['subcategory']},{data['classification']['severity']},"
                f"{data['status']},{data['timeline']['detected_at']},"
                f"{impact.get('individuals_affected', 0)},{impact.get('financial_impact_usd', 0)}"
            )
        return "\n".join(lines)
