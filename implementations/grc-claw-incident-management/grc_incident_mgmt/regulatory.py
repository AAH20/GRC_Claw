"""
GRC_Claw Regulatory Reporting Automation (§17 of GRC-AIM-001)

Implements automated regulatory reporting workflows:
    • Multi-regulation applicability assessment (§17.3)
    • Automated report generation with templates (§17.4)
    • Deadline management and escalation (§17.5)
    • Submission and tracking (§17.6)
    • Regulatory communication management (§17.7)
    • Compliance dashboard (§17.8)

Supported regulations (§17.2):
    • EU AI Act Art. 73, Art. 86
    • GDPR Art. 33, Art. 34
    • NIS2 Directive
    • SEC Cybersecurity Rules
    • CIRCIA
    • PIPEDA
    • APRA CPS 234
    • DORA
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from .models import Incident, IncidentStatus
from .taxonomy import IncidentCategory, Severity


# ═══════════════════════════════════════════════════════════════════════════════
# Supported Regulations (§17.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Regulation:
    """Regulation definition."""
    name: str
    jurisdiction: str
    trigger: str
    deadline_hours: dict[str, float]  # severity → hours
    recipient: str
    portal_url: str = ""
    content_requirements: list[str] = field(default_factory=list)


REGULATIONS: dict[str, Regulation] = {
    "EU_AI_ACT_ART_73": Regulation(
        name="EU AI Act Art. 73",
        jurisdiction="EU",
        trigger="Serious incident",
        deadline_hours={"S1": 24, "S2": 72, "S3": 72},
        recipient="National market surveillance authority",
        content_requirements=[
            "incident_description", "system_identification", "cause",
            "impact", "corrective_actions", "cross_border_impact", "contact_info",
        ],
    ),
    "EU_AI_ACT_ART_86": Regulation(
        name="EU AI Act Art. 86",
        jurisdiction="EU",
        trigger="Serious incident (deployer)",
        deadline_hours={"S1": 24, "S2": 72, "S3": 72},
        recipient="National market surveillance authority",
    ),
    "GDPR_ART_33": Regulation(
        name="GDPR Art. 33",
        jurisdiction="EU/EEA",
        trigger="Personal data breach",
        deadline_hours={"default": 72},
        recipient="Supervisory authority",
    ),
    "GDPR_ART_34": Regulation(
        name="GDPR Art. 34",
        jurisdiction="EU/EEA",
        trigger="High-risk data breach",
        deadline_hours={"default": 0},  # Without undue delay
        recipient="Affected data subjects",
    ),
    "NIS2": Regulation(
        name="NIS2 Directive",
        jurisdiction="EU",
        trigger="Significant incident",
        deadline_hours={"S1": 24, "S2": 72},  # Early warning + incident report
        recipient="National CSIRT",
    ),
    "SEC_CYBER": Regulation(
        name="SEC Cybersecurity Rules",
        jurisdiction="US",
        trigger="Material cybersecurity incident",
        deadline_hours={"default": 96},  # 4 business days
        recipient="SEC EDGAR",
    ),
    "CIRCIA": Regulation(
        name="CIRCIA",
        jurisdiction="US",
        trigger="Significant cyber incident",
        deadline_hours={"default": 72},
        recipient="CISA",
    ),
    "PIPEDA": Regulation(
        name="PIPEDA",
        jurisdiction="Canada",
        trigger="Breach of security safeguards",
        deadline_hours={"default": 0},  # As soon as feasible
        recipient="Privacy Commissioner",
    ),
    "APRA_CPS_234": Regulation(
        name="APRA CPS 234",
        jurisdiction="Australia",
        trigger="Material information security incident",
        deadline_hours={"default": 72},
        recipient="APRA",
    ),
    "DORA": Regulation(
        name="DORA",
        jurisdiction="EU",
        trigger="Major ICT-related incident",
        deadline_hours={"initial": 4, "intermediate": 72, "final": 720},  # 4h, 72h, 1 month
        recipient="Competent authority",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Applicability Assessment Engine (§17.3)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RegulationAssessment:
    """Result of regulation applicability assessment."""
    regulation: str
    jurisdiction: str
    applicable: bool
    threshold_met: bool
    criteria_met: list[str] = field(default_factory=list)
    deadline: str = ""
    deadline_hours: float = 0.0
    recipient: str = ""
    content_requirements: list[str] = field(default_factory=list)
    portal_url: str = ""
    status: str = "pending"  # pending | notified | acknowledged | closed
    reason: str = ""


class ApplicabilityAssessmentEngine:
    """
    Multi-regulation applicability assessment engine (§17.3).

    When an incident is detected, assesses all relevant regulations:
    1. Check jurisdiction applicability
    2. Check entity applicability (provider, deployer, operator)
    3. Check incident type applicability
    4. Check threshold criteria
    5. Check deadline
    6. Check content requirements
    7. Check recipient
    """

    def __init__(self, entity_roles: Optional[list[str]] = None) -> None:
        self._entity_roles = entity_roles or ["provider", "deployer"]
        self._assessments: list[RegulationAssessment] = []

    def set_entity_roles(self, roles: list[str]) -> None:
        self._entity_roles = roles

    def assess_all(self, incident: Incident) -> dict[str, Any]:
        """Assess all regulations for an incident."""
        applicable = []
        non_applicable = []

        for reg_id, reg in REGULATIONS.items():
            assessment = self._assess_regulation(reg_id, reg, incident)
            if assessment.applicable:
                applicable.append(assessment)
            else:
                non_applicable.append(assessment)

        self._assessments.extend(applicable)

        return {
            "assessment_id": hashlib.sha256(
                f"{incident.incident_id}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            "incident_id": incident.incident_id,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "applicable_regulations": [a.__dict__ for a in applicable],
            "non_applicable_regulations": [a.__dict__ for a in non_applicable],
        }

    def _assess_regulation(
        self, reg_id: str, reg: Regulation, incident: Incident
    ) -> RegulationAssessment:
        """Assess a single regulation."""
        # Check incident type applicability
        type_applicable = self._check_incident_type(reg_id, incident)
        if not type_applicable:
            return RegulationAssessment(
                regulation=reg.name,
                jurisdiction=reg.jurisdiction,
                applicable=False,
                threshold_met=False,
                reason=f"Incident type does not trigger {reg.name}",
            )

        # Check threshold criteria
        threshold_met, criteria = self._check_thresholds(reg_id, incident)
        if not threshold_met:
            return RegulationAssessment(
                regulation=reg.name,
                jurisdiction=reg.jurisdiction,
                applicable=False,
                threshold_met=False,
                reason=f"Threshold criteria not met for {reg.name}",
            )

        # Calculate deadline
        deadline_hours = self._get_deadline(reg, incident.severity)
        detected = datetime.fromisoformat(incident.detected_at.replace("Z", "+00:00")) if incident.detected_at else datetime.now(timezone.utc)
        deadline = (detected + timedelta(hours=deadline_hours)).isoformat()

        return RegulationAssessment(
            regulation=reg.name,
            jurisdiction=reg.jurisdiction,
            applicable=True,
            threshold_met=True,
            criteria_met=criteria,
            deadline=deadline,
            deadline_hours=deadline_hours,
            recipient=reg.recipient,
            content_requirements=reg.content_requirements,
            portal_url=reg.portal_url,
        )

    def _check_incident_type(self, reg_id: str, incident: Incident) -> bool:
        """Check if incident type triggers this regulation."""
        if reg_id in ("EU_AI_ACT_ART_73", "EU_AI_ACT_ART_86"):
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH, Severity.S3_MEDIUM)
        elif reg_id in ("GDPR_ART_33", "GDPR_ART_34"):
            return incident.category == IncidentCategory.DATA_LEAKAGE
        elif reg_id == "NIS2":
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH)
        elif reg_id == "SEC_CYBER":
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH)
        elif reg_id == "CIRCIA":
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH)
        elif reg_id == "PIPEDA":
            return incident.category == IncidentCategory.DATA_LEAKAGE
        elif reg_id == "APRA_CPS_234":
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH)
        elif reg_id == "DORA":
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH)
        return False

    def _check_thresholds(self, reg_id: str, incident: Incident) -> tuple[bool, list[str]]:
        """Check if incident meets threshold criteria."""
        criteria = []
        impact = incident.impact_assessment

        if reg_id in ("EU_AI_ACT_ART_73", "EU_AI_ACT_ART_86"):
            if impact.individuals_affected > 0:
                criteria.append("death_or_serious_harm")
            if any(a.environment == "production" for a in incident.affected_assets):
                criteria.append("critical_infrastructure")
            if "pii" in impact.data_types or "phi" in impact.data_types:
                criteria.append("fundamental_rights")
            if impact.individuals_affected > 1000:
                criteria.append("widespread_disruption")
            return len(criteria) > 0, criteria

        elif reg_id in ("GDPR_ART_33", "GDPR_ART_34"):
            if impact.records_affected > 0:
                criteria.append("personal_data_breach")
            if "pii" in impact.data_types:
                criteria.append("pii_involved")
            return len(criteria) > 0, criteria

        elif reg_id in ("NIS2", "SEC_CYBER", "CIRCIA", "APRA_CPS_234", "DORA"):
            return incident.severity in (Severity.S1_CRITICAL, Severity.S2_HIGH), ["high_severity"]

        elif reg_id == "PIPEDA":
            if impact.records_affected > 0:
                criteria.append("security_safeguards_breach")
            return len(criteria) > 0, criteria

        return False, []

    def _get_deadline(self, reg: Regulation, severity: Severity) -> float:
        """Get deadline in hours for a regulation and severity."""
        return reg.deadline_hours.get(severity.value, reg.deadline_hours.get("default", 72))


# ═══════════════════════════════════════════════════════════════════════════════
# Report Generation (§17.4)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReportTemplate:
    """Report template for a regulation."""
    template_id: str
    regulation: str
    auto_populated_fields: dict[str, str]  # field_name → source
    manual_fields: list[str] = field(default_factory=list)


REPORT_TEMPLATES: dict[str, ReportTemplate] = {
    "TPL-EU-AIA-73": ReportTemplate(
        template_id="TPL-EU-AIA-73",
        regulation="EU AI Act Art. 73",
        auto_populated_fields={
            "incident_id": "incident.incident_id",
            "incident_datetime": "incident.detected_at",
            "incident_description": "ai_generated_summary",
            "affected_systems": "asset_inventory",
            "individuals_affected": "impact_assessment.individuals_affected",
            "data_types_affected": "data_classification",
            "severity": "auto_classification",
            "timeline": "incident.timeline",
            "containment_actions": "response_actions_log",
        },
        manual_fields=["root_cause", "corrective_actions"],
    ),
    "TPL-EU-GDPR-33": ReportTemplate(
        template_id="TPL-EU-GDPR-33",
        regulation="GDPR Art. 33",
        auto_populated_fields={
            "incident_id": "incident.incident_id",
            "breach_description": "ai_generated_summary",
            "data_categories": "data_classification",
            "individuals_affected": "impact_assessment.individuals_affected",
        },
        manual_fields=["likely_consequences", "measures_taken"],
    ),
    "TPL-EU-NIS2": ReportTemplate(
        template_id="TPL-EU-NIS2",
        regulation="NIS2",
        auto_populated_fields={
            "incident_id": "incident.incident_id",
            "incident_description": "ai_generated_summary",
            "severity": "auto_classification",
            "impact": "impact_assessment",
        },
        manual_fields=["cross_border_impact", "threat_actor"],
    ),
    "TPL-US-SEC": ReportTemplate(
        template_id="TPL-US-SEC",
        regulation="SEC Cybersecurity Rules",
        auto_populated_fields={
            "incident_id": "incident.incident_id",
            "incident_description": "ai_generated_summary",
            "materiality_assessment": "impact_assessment",
        },
        manual_fields=["materiality_determination", "financial_impact"],
    ),
}


class ReportGenerator:
    """
    Automated report generation (§17.4).

    Pre-defined templates for each regulation with auto-populated
    fields from incident data.
    """

    def __init__(self) -> None:
        self._templates = dict(REPORT_TEMPLATES)

    def generate(
        self,
        template_id: str,
        incident: Incident,
    ) -> dict[str, Any]:
        """Generate a regulatory report from a template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        report = {
            "template_id": template_id,
            "regulation": template.regulation,
            "incident_id": incident.incident_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "auto_populated": {},
            "manual": {},
            "submission_status": "draft",
        }

        # Auto-populate fields
        for field_name, source in template.auto_populated_fields.items():
            report["auto_populated"][field_name] = self._resolve_field(source, incident)

        # Mark manual fields
        for field_name in template.manual_fields:
            report["manual"][field_name] = ""

        return report

    def _resolve_field(self, source: str, incident: Incident) -> Any:
        """Resolve a field source to its value from incident data."""
        if source == "ai_generated_summary":
            return incident.summary or self._generate_summary(incident)
        elif source == "incident.incident_id":
            return incident.incident_id
        elif source == "incident.detected_at":
            return incident.detected_at
        elif source == "incident.timeline":
            return {
                "detected_at": incident.detected_at,
                "triaged_at": incident.triaged_at,
                "contained_at": incident.contained_at,
                "eradicated_at": incident.eradicated_at,
                "recovered_at": incident.recovered_at,
                "closed_at": incident.closed_at,
            }
        elif source == "impact_assessment":
            return incident.impact_assessment.__dict__
        elif source == "impact_assessment.individuals_affected":
            return incident.impact_assessment.individuals_affected
        elif source == "auto_classification":
            return incident.severity.value
        elif source == "response_actions.log":
            return [a.__dict__ for a in incident.response_actions]
        elif source == "asset_inventory":
            return [a.__dict__ for a in incident.affected_assets]
        elif source == "data_classification":
            return incident.impact_assessment.data_types
        return ""

    def _generate_summary(self, incident: Incident) -> str:
        cat = incident.category.value if incident.category else "Unknown"
        sev = incident.severity.value
        return f"{sev} {cat} incident detected on {incident.detected_at}. Status: {incident.status.value}."

    def get_auto_population_rate(self, report: dict[str, Any]) -> float:
        """Calculate auto-population rate for a report."""
        auto = report.get("auto_populated", {})
        if not auto:
            return 0.0
        filled = sum(1 for v in auto.values() if v)
        return filled / len(auto)


# ═══════════════════════════════════════════════════════════════════════════════
# Deadline Management (§17.5)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DeadlineTracker:
    """Tracks a regulatory notification deadline."""
    regulation: str
    incident_id: str
    deadline: str
    deadline_hours: float
    status: str = "pending"  # pending | submitted | acknowledged | closed | missed
    submitted_at: str = ""
    escalation_level: int = 0


class DeadlineManager:
    """
    Deadline management (§17.5).

    Tracks notification deadlines, sends escalation alerts at
    50%, 75%, 90%, and 100% of deadline elapsed.
    """

    ESCALATION_THRESHOLDS = [0.50, 0.75, 0.90, 1.00]

    def __init__(self) -> None:
        self._trackers: dict[str, DeadlineTracker] = {}

    def create_tracker(
        self,
        regulation: str,
        incident_id: str,
        deadline: str,
        deadline_hours: float,
    ) -> DeadlineTracker:
        tracker = DeadlineTracker(
            regulation=regulation,
            incident_id=incident_id,
            deadline=deadline,
            deadline_hours=deadline_hours,
        )
        key = f"{regulation}:{incident_id}"
        self._trackers[key] = tracker
        return tracker

    def check_deadlines(self) -> list[dict[str, Any]]:
        """Check all deadlines and generate escalation alerts."""
        alerts = []
        now = datetime.now(timezone.utc)

        for key, tracker in self._trackers.items():
            if tracker.status != "pending":
                continue

            try:
                deadline = datetime.fromisoformat(tracker.deadline.replace("Z", "+00:00"))
                detected = deadline - timedelta(hours=tracker.deadline_hours)
                elapsed = (now - detected).total_seconds()
                total = (deadline - detected).total_seconds()
                pct = elapsed / total if total > 0 else 0

                for threshold in self.ESCALATION_THRESHOLDS:
                    if pct >= threshold and tracker.escalation_level < int(threshold * 100):
                        tracker.escalation_level = int(threshold * 100)
                        alerts.append({
                            "regulation": tracker.regulation,
                            "incident_id": tracker.incident_id,
                            "deadline": tracker.deadline,
                            "elapsed_pct": pct,
                            "escalation_level": tracker.escalation_level,
                            "action": self._get_escalation_action(threshold),
                            "recipients": self._get_escalation_recipients(threshold),
                        })

                if now > deadline:
                    tracker.status = "missed"
                    alerts.append({
                        "regulation": tracker.regulation,
                        "incident_id": tracker.incident_id,
                        "deadline": tracker.deadline,
                        "elapsed_pct": 1.0,
                        "escalation_level": 100,
                        "action": "Executive escalation + incident creation",
                        "recipients": ["CISO", "Legal", "Executive"],
                    })
            except (ValueError, AttributeError):
                pass

        return alerts

    def mark_submitted(self, regulation: str, incident_id: str) -> bool:
        key = f"{regulation}:{incident_id}"
        tracker = self._trackers.get(key)
        if tracker:
            tracker.status = "submitted"
            tracker.submitted_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_pending(self) -> list[DeadlineTracker]:
        return [t for t in self._trackers.values() if t.status == "pending"]

    def _get_escalation_action(self, threshold: float) -> str:
        actions = {
            0.50: "Warning notification",
            0.75: "Urgent notification",
            0.90: "Critical notification",
            1.00: "Escalation + incident creation",
        }
        return actions.get(threshold, "Unknown")

    def _get_escalation_recipients(self, threshold: float) -> list[str]:
        recipients = {
            0.50: ["GRC_Claw Analyst"],
            0.75: ["Security Lead", "CISO"],
            0.90: ["CISO", "Legal"],
            1.00: ["CISO", "Legal", "Executive"],
        }
        return recipients.get(threshold, [])


# ═══════════════════════════════════════════════════════════════════════════════
# Submission Tracking (§17.6)
# ═══════════════════════════════════════════════════════════════════════════════

class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"


@dataclass
class SubmissionRecord:
    """Regulatory submission record."""
    submission_id: str
    regulation: str
    incident_id: str
    status: SubmissionStatus = SubmissionStatus.DRAFT
    submitted_at: str = ""
    acknowledged_at: str = ""
    method: str = ""  # portal_api | email | web_form | physical_mail
    content: dict[str, Any] = field(default_factory=dict)


class SubmissionTracker:
    """
    Submission and tracking (§17.6).

    Tracks regulatory submissions through their lifecycle.
    """

    def __init__(self) -> None:
        self._submissions: dict[str, SubmissionRecord] = {}

    def create_submission(
        self,
        regulation: str,
        incident_id: str,
        content: dict[str, Any],
        method: str = "portal_api",
    ) -> SubmissionRecord:
        sub_id = hashlib.sha256(
            f"{regulation}:{incident_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        record = SubmissionRecord(
            submission_id=sub_id,
            regulation=regulation,
            incident_id=incident_id,
            status=SubmissionStatus.DRAFT,
            method=method,
            content=content,
        )
        self._submissions[sub_id] = record
        return record

    def update_status(self, submission_id: str, status: SubmissionStatus) -> bool:
        record = self._submissions.get(submission_id)
        if record:
            if isinstance(status, str):
                status = SubmissionStatus(status)
            record.status = status
            if status == SubmissionStatus.SUBMITTED:
                record.submitted_at = datetime.now(timezone.utc).isoformat()
            elif status == SubmissionStatus.ACKNOWLEDGED:
                record.acknowledged_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_submissions(self, status: Optional[SubmissionStatus] = None) -> list[SubmissionRecord]:
        if status:
            return [s for s in self._submissions.values() if s.status == status]
        return list(self._submissions.values())


# ═══════════════════════════════════════════════════════════════════════════════
# Regulatory Communication Management (§17.7)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CommunicationRecord:
    """Regulatory communication record."""
    communication_id: str
    regulation: str
    direction: str  # inbound | outbound
    timestamp: str
    sender: str = ""
    recipient: str = ""
    method: str = ""  # portal | email | phone | mail
    content: str = ""
    attachments: list[str] = field(default_factory=list)
    status: str = "draft"  # draft | sent | received | acknowledged


class CommunicationManager:
    """
    Regulatory communication management (§17.7).

    Logs all regulatory communications and manages follow-ups.
    """

    def __init__(self) -> None:
        self._communications: dict[str, CommunicationRecord] = {}

    def log_communication(self, record: CommunicationRecord) -> None:
        self._communications[record.communication_id] = record

    def get_communications(
        self, regulation: str = "", direction: str = ""
    ) -> list[CommunicationRecord]:
        results = list(self._communications.values())
        if regulation:
            results = [c for c in results if c.regulation == regulation]
        if direction:
            results = [c for c in results if c.direction == direction]
        return results

    def get_follow_ups(self) -> list[CommunicationRecord]:
        return [c for c in self._communications.values() if c.status == "follow_up"]


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Dashboard (§17.8)
# ═══════════════════════════════════════════════════════════════════════════════

class ComplianceDashboard:
    """
    Compliance dashboard (§17.8).

    Real-time visibility into regulatory reporting status.
    """

    def __init__(self) -> None:
        self._deadline_manager = DeadlineManager()
        self._submission_tracker = SubmissionTracker()

    def get_dashboard(self) -> dict[str, Any]:
        """Get compliance dashboard data."""
        pending = self._deadline_manager.get_pending()
        submissions = self._submission_tracker.get_submissions()

        # Compliance rate
        submitted = [s for s in submissions if s.status in (
            SubmissionStatus.SUBMITTED, SubmissionStatus.ACKNOWLEDGED,
            SubmissionStatus.ACCEPTED, SubmissionStatus.CLOSED
        )]
        compliance_rate = len(submitted) / len(submissions) if submissions else 1.0

        return {
            "pending_notifications": len(pending),
            "pending_details": [
                {
                    "regulation": t.regulation,
                    "incident_id": t.incident_id,
                    "deadline": t.deadline,
                    "deadline_hours": t.deadline_hours,
                }
                for t in pending
            ],
            "submission_status_counts": {
                status.value: len(self._submission_tracker.get_submissions(status))
                for status in SubmissionStatus
            },
            "compliance_rate": compliance_rate,
            "total_submissions": len(submissions),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Regulatory Reporting Metrics (§17.9)
# ═══════════════════════════════════════════════════════════════════════════════

class RegulatoryMetrics:
    """
    Regulatory reporting metrics (§17.9).
    """

    def __init__(self) -> None:
        self._notifications: list[dict[str, Any]] = []

    def record_notification(
        self,
        regulation: str,
        incident_id: str,
        deadline: str,
        submitted_at: str,
        accepted: bool = True,
    ) -> None:
        self._notifications.append({
            "regulation": regulation,
            "incident_id": incident_id,
            "deadline": deadline,
            "submitted_at": submitted_at,
            "accepted": accepted,
        })

    def get_metrics(self) -> dict[str, float]:
        total = len(self._notifications)
        if total == 0:
            return {
                "notification_timeliness": 1.0,
                "report_accuracy": 1.0,
                "auto_population_rate": 0.0,
                "assessment_accuracy": 1.0,
                "follow_up_response_time_hours": 0.0,
                "audit_trail_completeness": 1.0,
            }

        timely = 0
        accurate = 0
        for n in self._notifications:
            try:
                deadline = datetime.fromisoformat(n["deadline"].replace("Z", "+00:00"))
                submitted = datetime.fromisoformat(n["submitted_at"].replace("Z", "+00:00"))
                if submitted <= deadline:
                    timely += 1
            except (ValueError, AttributeError):
                pass
            if n.get("accepted", True):
                accurate += 1

        return {
            "notification_timeliness": timely / total,
            "report_accuracy": accurate / total,
            "auto_population_rate": 0.85,  # Placeholder
            "assessment_accuracy": 0.95,  # Placeholder
            "follow_up_response_time_hours": 24.0,  # Placeholder
            "audit_trail_completeness": 1.0,
        }
