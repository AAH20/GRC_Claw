#!/usr/bin/env python3
"""
GRC_Claw Compliance Scoring Demo
=================================
Demonstrates the complete compliance scoring workflow:
  1. MAP    - Map controls to frameworks and evidence
  2. SCORE  - Calculate compliance scores with weighted controls
  3. REPORT - Generate compliance reports with findings and recommendations

Usage:
    python compliance_scoring_demo.py
"""

import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ── Enums & Types ──────────────────────────────────────────────────────────

class ControlStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FrameworkCode(Enum):
    ISO27001 = "iso27001"
    NIST_CSF = "nist-csf"
    SOC2 = "soc2"
    ISO42001 = "iso42001"
    CMMC = "cmmc"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci-dss"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class ComplianceControl:
    id: str
    control_code: str
    title: str
    framework_code: str
    domain: str = ""
    severity: str = "MEDIUM"
    status: str = "not_started"
    evidence_count: int = 0
    score: float = 0.0
    issues: list = field(default_factory=list)
    weight: float = 1.0


@dataclass
class ComplianceScore:
    tenant_id: int
    framework_code: str
    score_percent: float
    failing_controls: int
    total_controls: int
    passing_controls: int = 0
    not_applicable: int = 0


@dataclass
class ComplianceFinding:
    id: str
    control_id: str
    severity: str
    title: str
    description: str
    remediation: str = ""
    detected_at: str = ""


@dataclass
class ComplianceReport:
    id: str
    tenant_id: int
    framework_code: str
    generated_at: str
    overall_score: float
    controls: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ── Compliance Engine ─────────────────────────────────────────────────────

class ComplianceEngine:
    """Maps controls, scores compliance, and generates reports."""

    def __init__(self):
        self.controls: dict[str, ComplianceControl] = {}
        self.findings: dict[str, list[ComplianceFinding]] = {}

    def add_control(self, control: ComplianceControl):
        self.controls[control.id] = control

    def map_control_to_framework(self, control_id: str, framework_code: str) -> dict:
        """Map a control to a compliance framework."""
        control = self.controls.get(control_id)
        if not control:
            return {"error": "Control not found"}

        # Framework-specific mappings
        mappings = {
            "iso27001": {"family": "A.9", "domain": "Access Control"},
            "nist-csf": {"family": "PR.AC", "domain": "Identity Management"},
            "soc2": {"family": "CC6", "domain": "Logical Access"},
            "iso42001": {"family": "A.8", "domain": "AI Data Quality"},
            "cmmc": {"family": "AC", "domain": "Access Control"},
            "gdpr": {"family": "Art.32", "domain": "Security of Processing"},
            "hipaa": {"family": "164.312", "domain": "Technical Safeguards"},
            "pci-dss": {"family": "Req.7", "domain": "Access Control"},
        }

        mapping = mappings.get(framework_code, {"family": "Unknown", "domain": "Unknown"})

        return {
            "control_id": control_id,
            "control_code": control.control_code,
            "title": control.title,
            "framework": framework_code,
            "framework_family": mapping["family"],
            "domain": mapping["domain"],
            "severity": control.severity,
            "status": control.status,
            "evidence_count": control.evidence_count,
        }

    def score_control(self, control_id: str) -> dict:
        """Score a single control based on evidence and status."""
        control = self.controls.get(control_id)
        if not control:
            return {"error": "Control not found"}

        # Scoring logic
        status_scores = {
            ControlStatus.NOT_STARTED.value: 0,
            ControlStatus.IN_PROGRESS.value: 40,
            ControlStatus.IMPLEMENTED.value: 100,
            ControlStatus.NOT_APPLICABLE.value: 100,
            ControlStatus.FAILED.value: 0,
        }

        base_score = status_scores.get(control.status, 0)

        # Evidence bonus
        evidence_bonus = min(20, control.evidence_count * 5)

        # Issue penalty
        issue_penalty = sum(
            {"LOW": 5, "MEDIUM": 10, "HIGH": 20, "CRITICAL": 40}.get(i.get("severity", "LOW") if isinstance(i, dict) else getattr(i, "severity", "LOW"), 0)
            for i in control.issues
        )

        final_score = max(0, min(100, base_score + evidence_bonus - issue_penalty))
        control.score = final_score

        return {
            "control_id": control_id,
            "title": control.title,
            "status": control.status,
            "base_score": base_score,
            "evidence_bonus": evidence_bonus,
            "issue_penalty": issue_penalty,
            "final_score": final_score,
            "weight": control.weight,
        }

    def score_framework(self, tenant_id: int, framework_code: str) -> ComplianceScore:
        """Calculate overall compliance score for a framework."""
        framework_controls = [
            c for c in self.controls.values()
            if c.framework_code == framework_code
        ]

        if not framework_controls:
            return ComplianceScore(
                tenant_id=tenant_id,
                framework_code=framework_code,
                score_percent=0,
                failing_controls=0,
                total_controls=0,
            )

        total_weight = sum(c.weight for c in framework_controls)
        weighted_score = sum(c.score * c.weight for c in framework_controls)
        overall = weighted_score / total_weight if total_weight > 0 else 0

        failing = sum(1 for c in framework_controls if c.score < 60)
        passing = sum(1 for c in framework_controls if c.score >= 60)
        na = sum(1 for c in framework_controls if c.status == ControlStatus.NOT_APPLICABLE.value)

        return ComplianceScore(
            tenant_id=tenant_id,
            framework_code=framework_code,
            score_percent=round(overall, 1),
            failing_controls=failing,
            total_controls=len(framework_controls),
            passing_controls=passing,
            not_applicable=na,
        )

    def generate_report(self, tenant_id: int, framework_code: str) -> ComplianceReport:
        """Generate a comprehensive compliance report."""
        report_id = f"report-{uuid.uuid4().hex[:12]}"
        score = self.score_framework(tenant_id, framework_code)

        # Get framework controls
        controls = [
            c for c in self.controls.values()
            if c.framework_code == framework_code
        ]

        # Generate findings
        findings = []
        for control in controls:
            if control.score < 60:
                severity = Severity.CRITICAL.value if control.score < 30 else Severity.HIGH.value if control.score < 50 else Severity.MEDIUM.value
                finding = ComplianceFinding(
                    id=f"finding-{uuid.uuid4().hex[:8]}",
                    control_id=control.id,
                    severity=severity,
                    title=f"Non-compliant: {control.title}",
                    description=f"Control {control.control_code} scored {control.score}% (threshold: 60%)",
                    remediation=self._get_remediation(control),
                    detected_at=datetime.utcnow().isoformat(),
                )
                findings.append(finding)

        # Generate recommendations
        recommendations = self._generate_recommendations(controls, findings)

        # Summary
        summary = {
            "total_controls": score.total_controls,
            "passing": score.passing_controls,
            "failing": score.failing_controls,
            "not_applicable": score.not_applicable,
            "overall_score": score.score_percent,
            "critical_findings": sum(1 for f in findings if f.severity == Severity.CRITICAL.value),
            "high_findings": sum(1 for f in findings if f.severity == Severity.HIGH.value),
            "medium_findings": sum(1 for f in findings if f.severity == Severity.MEDIUM.value),
            "low_findings": sum(1 for f in findings if f.severity == Severity.LOW.value),
        }

        return ComplianceReport(
            id=report_id,
            tenant_id=tenant_id,
            framework_code=framework_code,
            generated_at=datetime.utcnow().isoformat(),
            overall_score=score.score_percent,
            controls=[asdict(c) for c in controls],
            findings=[asdict(f) for f in findings],
            recommendations=recommendations,
            summary=summary,
        )

    def _get_remediation(self, control: ComplianceControl) -> str:
        """Get remediation guidance for a control."""
        remediations = {
            "AC-2": "Implement account management procedures with automated provisioning/deprovisioning",
            "AC-3": "Enforce least-privilege access control policy across all systems",
            "AC-6": "Review and restrict privileged access; implement just-in-time elevation",
            "AU-6": "Deploy centralized log management with real-time analysis and alerting",
            "AU-12": "Enable audit logging for all critical systems and sensitive operations",
            "CM-8": "Establish configuration management baseline and change control process",
            "RA-5": "Implement continuous vulnerability scanning with automated remediation",
            "SC-13": "Deploy TLS 1.3 for all communications; enforce certificate pinning",
            "SI-4": "Deploy SIEM with automated incident detection and response playbooks",
        }
        return remediations.get(control.control_code, f"Review and implement controls for {control.title}")

    def _generate_recommendations(self, controls: list, findings: list) -> list:
        """Generate prioritized recommendations."""
        recs = []

        # Critical findings first
        critical = [f for f in findings if f.severity == Severity.CRITICAL.value]
        if critical:
            recs.append({
                "priority": 1,
                "category": "critical",
                "title": f"Address {len(critical)} critical findings immediately",
                "description": "Critical findings represent significant compliance gaps requiring immediate attention",
                "estimated_effort": "2-4 weeks",
            })

        # High findings
        high = [f for f in findings if f.severity == Severity.HIGH.value]
        if high:
            recs.append({
                "priority": 2,
                "category": "high",
                "title": f"Remediate {len(high)} high-severity findings",
                "description": "High-severity findings should be addressed in the next sprint",
                "estimated_effort": "1-2 weeks",
            })

        # Evidence gaps
        no_evidence = [c for c in controls if c.evidence_count == 0 and c.status != ControlStatus.NOT_APPLICABLE.value]
        if no_evidence:
            recs.append({
                "priority": 3,
                "category": "evidence",
                "title": f"Collect evidence for {len(no_evidence)} controls",
                "description": "Controls without evidence cannot be verified for compliance",
                "estimated_effort": "3-5 days",
            })

        # Not started controls
        not_started = [c for c in controls if c.status == ControlStatus.NOT_STARTED.value]
        if not_started:
            recs.append({
                "priority": 4,
                "category": "implementation",
                "title": f"Begin implementation of {len(not_started)} not-started controls",
                "description": "These controls have not been started and need implementation plans",
                "estimated_effort": "4-8 weeks",
            })

        return recs


# ── Demo Runner ────────────────────────────────────────────────────────────

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_demo():
    print_header("GRC_Claw Compliance Scoring Demo")
    print("Demonstrating: MAP → SCORE → REPORT")

    engine = ComplianceEngine()
    TENANT_ID = 1

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1: MAP
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 1: MAP — Control-to-Framework Mapping")

    print_section("Registering Controls")

    controls_data = [
        # ISO 27001 controls
        ("AC-2", "Account Management", "iso27001", "Access Control", "HIGH", "implemented", 3, []),
        ("AC-3", "Access Enforcement", "iso27001", "Access Control", "HIGH", "implemented", 2, []),
        ("AC-6", "Least Privilege", "iso27001", "Access Control", "MEDIUM", "in_progress", 1, [{"severity": "MEDIUM", "description": "Privileged access review overdue"}]),
        ("AU-6", "Audit Review", "iso27001", "Audit", "HIGH", "implemented", 4, []),
        ("AU-12", "Audit Generation", "iso27001", "Audit", "MEDIUM", "not_started", 0, []),
        ("CM-8", "Configuration Management", "iso27001", "Operations", "MEDIUM", "in_progress", 2, []),
        ("RA-5", "Vulnerability Scanning", "iso27001", "Risk", "HIGH", "implemented", 5, []),
        ("SC-13", "Cryptographic Protection", "iso27001", "Communications", "HIGH", "implemented", 3, []),
        ("SI-4", "Information Monitoring", "iso27001", "Operations", "MEDIUM", "failed", 1, [{"severity": "HIGH", "description": "SIEM not deployed"}]),

        # SOC 2 controls
        ("CC6.1", "Logical Access Controls", "soc2", "Access Control", "HIGH", "implemented", 4, []),
        ("CC6.2", "Access Removal", "soc2", "Access Control", "HIGH", "implemented", 2, []),
        ("CC6.3", "Access Restrictions", "soc2", "Access Control", "MEDIUM", "in_progress", 1, []),
        ("CC7.1", "Security Operations", "soc2", "Monitoring", "HIGH", "implemented", 3, []),
        ("CC7.2", "Incident Detection", "soc2", "Monitoring", "HIGH", "in_progress", 2, [{"severity": "MEDIUM", "description": "Alert tuning needed"}]),

        # CMMC controls
        ("AC.L1-3.1.1", "Account Management", "cmmc", "Access Control", "HIGH", "implemented", 3, []),
        ("AC.L1-3.1.2", "Access Enforcement", "cmmc", "Access Control", "HIGH", "in_progress", 1, []),
        ("AU.L1-3.3.1", "Audit Logging", "cmmc", "Audit", "MEDIUM", "not_started", 0, []),
        ("CM.L1-3.4.1", "Configuration Management", "cmmc", "Configuration", "MEDIUM", "in_progress", 2, []),
        ("IA.L1-3.5.1", "MFA Enforcement", "cmmc", "Identification", "HIGH", "implemented", 4, []),

        # ISO 42001 controls
        ("A.6", "AI Risk Assessment", "iso42001", "AI Governance", "HIGH", "in_progress", 1, []),
        ("A.8", "Data Quality", "iso42001", "AI Data", "MEDIUM", "not_started", 0, []),
    ]

    for ctrl_data in controls_data:
        control = ComplianceControl(
            id=f"ctrl-{uuid.uuid4().hex[:8]}",
            control_code=ctrl_data[0],
            title=ctrl_data[1],
            framework_code=ctrl_data[2],
            domain=ctrl_data[3],
            severity=ctrl_data[4],
            status=ctrl_data[5],
            evidence_count=ctrl_data[6],
            issues=ctrl_data[7],
            weight=1.5 if ctrl_data[4] == "HIGH" else 1.0,
        )
        engine.add_control(control)
        print(f"  ✓ {ctrl_data[0]}: {ctrl_data[1]} ({ctrl_data[2]})")

    print_section("Mapping Controls to Frameworks")
    iso_controls = [c for c in engine.controls.values() if c.framework_code == "iso27001"]
    for ctrl in iso_controls[:5]:
        mapping = engine.map_control_to_framework(ctrl.id, "iso27001")
        print(f"  • {mapping['control_code']} → {mapping['framework_family']} ({mapping['domain']})")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2: SCORE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 2: SCORE — Calculating Compliance Scores")

    print_section("Individual Control Scoring")
    for ctrl in list(engine.controls.values())[:8]:
        result = engine.score_control(ctrl.id)
        status_icon = "✓" if result['final_score'] >= 60 else "✗"
        print(f"  {status_icon} {ctrl.control_code}: {result['final_score']}% (base={result['base_score']}, evidence=+{result['evidence_bonus']}, issues=-{result['issue_penalty']})")

    print_section("Framework-Level Scoring")
    frameworks = ["iso27001", "soc2", "cmmc", "iso42001"]
    for fw in frameworks:
        score = engine.score_framework(TENANT_ID, fw)
        status_icon = "✓" if score.score_percent >= 70 else "⚠" if score.score_percent >= 50 else "✗"
        print(f"  {status_icon} {fw.upper()}: {score.score_percent}% ({score.passing_controls}/{score.total_controls} passing, {score.failing_controls} failing)")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 3: REPORT
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 3: REPORT — Generating Compliance Reports")

    print_section("ISO 27001 Compliance Report")
    report = engine.generate_report(TENANT_ID, "iso27001")
    print(f"  Report ID: {report.id}")
    print(f"  Generated: {report.generated_at}")
    print(f"  Overall Score: {report.overall_score}%")
    print(f"\n  Summary:")
    for key, value in report.summary.items():
        print(f"    {key}: {value}")

    print_section("Findings")
    for finding in report.findings:
        sev = finding.get("severity", "low") if isinstance(finding, dict) else finding.severity
        title = finding.get("title", "") if isinstance(finding, dict) else finding.title
        desc = finding.get("description", "") if isinstance(finding, dict) else finding.description
        rem = finding.get("remediation", "") if isinstance(finding, dict) else finding.remediation
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
        print(f"  {severity_icon} [{sev.upper()}] {title}")
        print(f"     {desc}")
        print(f"     Remediation: {rem}")

    print_section("Recommendations")
    for rec in report.recommendations:
        print(f"  {rec['priority']}. [{rec['category'].upper()}] {rec['title']}")
        print(f"     {rec['description']}")
        print(f"     Estimated effort: {rec['estimated_effort']}")

    print_section("SOC 2 Compliance Report")
    soc2_report = engine.generate_report(TENANT_ID, "soc2")
    print(f"  Overall Score: {soc2_report.overall_score}%")
    print(f"  Findings: {len(soc2_report.findings)}")
    print(f"  Recommendations: {len(soc2_report.recommendations)}")

    print_section("CMMC Compliance Report")
    cmmc_report = engine.generate_report(TENANT_ID, "cmmc")
    print(f"  Overall Score: {cmmc_report.overall_score}%")
    print(f"  Findings: {len(cmmc_report.findings)}")

    print_section("ISO 42001 Compliance Report")
    iso42001_report = engine.generate_report(TENANT_ID, "iso42001")
    print(f"  Overall Score: {iso42001_report.overall_score}%")
    print(f"  Findings: {len(iso42001_report.findings)}")

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════
    print_header("DEMO COMPLETE")
    print(f"""
Summary:
  • Mapped {len(engine.controls)} controls across {len(frameworks)} frameworks
  • Scored all controls with weighted evidence and issue penalties
  • Generated 4 compliance reports (ISO 27001, SOC 2, CMMC, ISO 42001)
  • Identified {sum(len(r.findings) for r in [report, soc2_report, cmmc_report, iso42001_report])} total findings
  • Generated {sum(len(r.recommendations) for r in [report, soc2_report, cmmc_report, iso42001_report])} recommendations

Key Capabilities Demonstrated:
  ✓ Control registration with severity and weight
  ✓ Framework-to-control mapping (ISO 27001, SOC 2, CMMC, ISO 42001)
  ✓ Evidence-based control scoring with bonuses/penalties
  ✓ Framework-level compliance scoring
  ✓ Automated finding generation with severity classification
  ✓ Prioritized remediation recommendations
  ✓ Comprehensive compliance reporting
""")


if __name__ == "__main__":
    run_demo()
