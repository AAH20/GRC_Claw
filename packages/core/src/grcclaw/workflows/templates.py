"""
Workflow templates for GRC_Claw.

Pre-built workflow templates for common GRC processes including
compliance assessments, policy enforcement, evidence collection,
audit preparation, and incident response.
"""

from __future__ import annotations

from typing import Any, Optional

from .schema import (
    RetryPolicy,
    StepCondition,
    StepType,
    TriggerType,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowStatus,
    WorkflowTemplate,
)


def _compliance_assessment_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Compliance Assessment",
        description="Automated compliance assessment against configured frameworks",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.MANUAL,
        steps=[
            WorkflowStep(
                id="scope",
                name="Define Assessment Scope",
                type=StepType.ACTION,
                description="Determine assessment scope, frameworks, and assets",
                agent="compliance_agent",
                tool="define_scope",
                parameters={"frameworks": ["SOC2", "ISO27001", "GDPR"]},
                next_steps=["collect_evidence"],
            ),
            WorkflowStep(
                id="collect_evidence",
                name="Collect Evidence",
                type=StepType.ACTION,
                description="Gather compliance evidence from target systems",
                agent="evidence_agent",
                tool="collect",
                parameters={"evidence_types": ["policies", "configs", "logs"]},
                depends_on=["scope"],
                next_steps=["analyze_gaps"],
            ),
            WorkflowStep(
                id="analyze_gaps",
                name="Analyze Compliance Gaps",
                type=StepType.ACTION,
                description="Analyze collected evidence for compliance gaps",
                agent="compliance_agent",
                tool="gap_analysis",
                parameters={"severity_threshold": "medium"},
                depends_on=["collect_evidence"],
                next_steps=["generate_report"],
            ),
            WorkflowStep(
                id="generate_report",
                name="Generate Assessment Report",
                type=StepType.ACTION,
                description="Produce comprehensive compliance assessment report",
                agent="reporting_agent",
                tool="generate_report",
                parameters={"format": "pdf", "include_remediations": True},
                depends_on=["analyze_gaps"],
                next_steps=["notify_stakeholders"],
            ),
            WorkflowStep(
                id="notify_stakeholders",
                name="Notify Stakeholders",
                type=StepType.NOTIFICATION,
                description="Send assessment results to compliance team",
                parameters={
                    "message": "Compliance assessment completed. Review the report for details.",
                    "channels": ["email", "slack"],
                },
                depends_on=["generate_report"],
            ),
        ],
        tags=["compliance", "assessment", "audit"],
        timeout_seconds=7200.0,
    )


def _policy_enforcement_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Policy Enforcement",
        description="Detect and remediate policy violations across infrastructure",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.EVENT,
        steps=[
            WorkflowStep(
                id="detect_violations",
                name="Detect Policy Violations",
                type=StepType.ACTION,
                description="Scan infrastructure for policy violations",
                agent="policy_agent",
                tool="detect_violations",
                parameters={"policy_set": "default", "scan_depth": "full"},
                next_steps=["classify_severity"],
            ),
            WorkflowStep(
                id="classify_severity",
                name="Classify Violation Severity",
                type=StepType.DECISION,
                description="Classify violations by severity and blast radius",
                agent="policy_agent",
                tool="classify",
                parameters={"severity_levels": ["critical", "high", "medium", "low"]},
                depends_on=["detect_violations"],
                next_steps=["auto_remediate_critical"],
            ),
            WorkflowStep(
                id="auto_remediate_critical",
                name="Auto-Remediate Critical Violations",
                type=StepType.ACTION,
                description="Automatically remediate critical policy violations",
                agent="remediation_agent",
                tool="auto_remediate",
                parameters={"severity": "critical", "dry_run": False},
                depends_on=["classify_severity"],
                condition=StepCondition(
                    expression="len(context.get('critical_violations', [])) > 0"
                ),
                next_steps=["create_tickets"],
            ),
            WorkflowStep(
                id="create_tickets",
                name="Create Remediation Tickets",
                type=StepType.ACTION,
                description="Create tickets for non-critical violations",
                agent="ticketing_agent",
                tool="create_tickets",
                parameters={"assignee": "security_team", "priority": "high"},
                depends_on=["classify_severity"],
                next_steps=["notify_team"],
            ),
            WorkflowStep(
                id="notify_team",
                name="Notify Security Team",
                type=StepType.NOTIFICATION,
                description="Alert security team of enforcement actions",
                parameters={
                    "message": "Policy enforcement completed. Review tickets for remediation.",
                    "channels": ["slack", "pagerduty"],
                },
                depends_on=["create_tickets", "auto_remediate_critical"],
            ),
        ],
        tags=["policy", "enforcement", "remediation"],
        timeout_seconds=3600.0,
    )


def _evidence_collection_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Evidence Collection",
        description="Collect and validate GRC evidence from multiple sources",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.SCHEDULED,
        cron_expression="0 2 * * *",
        steps=[
            WorkflowStep(
                id="discover_sources",
                name="Discover Evidence Sources",
                type=StepType.ACTION,
                description="Discover available evidence sources and systems",
                agent="evidence_agent",
                tool="discover_sources",
                parameters={"source_types": ["cloud", "on_prem", "saas"]},
                next_steps=["collect_cloud"],
            ),
            WorkflowStep(
                id="collect_cloud",
                name="Collect Cloud Evidence",
                type=StepType.PARALLEL,
                description="Collect evidence from cloud providers in parallel",
                agent="evidence_agent",
                tool="collect_cloud",
                parameters={"providers": ["aws", "azure", "gcp"]},
                depends_on=["discover_sources"],
                next_steps=["collect_saas"],
            ),
            WorkflowStep(
                id="collect_saas",
                name="Collect SaaS Evidence",
                type=StepType.ACTION,
                description="Collect evidence from SaaS applications",
                agent="evidence_agent",
                tool="collect_saas",
                parameters={"apps": ["okta", "workspace", "github"]},
                depends_on=["collect_cloud"],
                next_steps=["validate_evidence"],
            ),
            WorkflowStep(
                id="validate_evidence",
                name="Validate Evidence Integrity",
                type=StepType.ACTION,
                description="Validate evidence completeness and integrity",
                agent="evidence_agent",
                tool="validate",
                parameters={"checksums": True, "completeness_check": True},
                depends_on=["collect_saas"],
                next_steps=["store_evidence"],
            ),
            WorkflowStep(
                id="store_evidence",
                name="Store Evidence",
                type=StepType.ACTION,
                description="Store validated evidence in evidence repository",
                agent="evidence_agent",
                tool="store",
                parameters={"retention_days": 2555, "encryption": "aes256"},
                depends_on=["validate_evidence"],
                next_steps=["update_catalog"],
            ),
            WorkflowStep(
                id="update_catalog",
                name="Update Evidence Catalog",
                type=StepType.ACTION,
                description="Update evidence catalog with new evidence metadata",
                agent="evidence_agent",
                tool="update_catalog",
                parameters={},
                depends_on=["store_evidence"],
            ),
        ],
        tags=["evidence", "collection", "compliance"],
        timeout_seconds=5400.0,
    )


def _audit_preparation_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Audit Preparation",
        description="Prepare organization for upcoming compliance audit",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.MANUAL,
        steps=[
            WorkflowStep(
                id="audit_scope",
                name="Define Audit Scope",
                type=StepType.ACTION,
                description="Define audit scope, criteria, and timeline",
                agent="compliance_agent",
                tool="define_audit_scope",
                parameters={"audit_type": "external", "frameworks": ["SOC2"]},
                next_steps=["gap_analysis"],
            ),
            WorkflowStep(
                id="gap_analysis",
                name="Perform Gap Analysis",
                type=StepType.ACTION,
                description="Analyze current state against audit requirements",
                agent="compliance_agent",
                tool="gap_analysis",
                parameters={"depth": "comprehensive"},
                depends_on=["audit_scope"],
                next_steps=["collect_evidence"],
            ),
            WorkflowStep(
                id="collect_evidence",
                name="Collect Audit Evidence",
                type=StepType.ACTION,
                description="Collect all required audit evidence",
                agent="evidence_agent",
                tool="collect_for_audit",
                parameters={"evidence_standards": ["auditor_approved"]},
                depends_on=["gap_analysis"],
                next_steps=["review_evidence"],
            ),
            WorkflowStep(
                id="review_evidence",
                name="Review Evidence Completeness",
                type=StepType.HUMAN_APPROVAL,
                description="Manual review of evidence completeness by compliance lead",
                parameters={
                    "prompt": "Review collected audit evidence for completeness and accuracy",
                    "reviewer": "compliance_lead",
                },
                depends_on=["collect_evidence"],
                next_steps=["remediate_gaps"],
            ),
            WorkflowStep(
                id="remediate_gaps",
                name="Remediate Identified Gaps",
                type=StepType.ACTION,
                description="Address gaps identified during evidence review",
                agent="remediation_agent",
                tool="remediate",
                parameters={"priority": "high", "deadline": "audit_date"},
                depends_on=["review_evidence"],
                next_steps=["final_review"],
            ),
            WorkflowStep(
                id="final_review",
                name="Final Audit Readiness Review",
                type=StepType.HUMAN_APPROVAL,
                description="Final review and sign-off before audit",
                parameters={
                    "prompt": "Confirm audit readiness and approve evidence package",
                    "reviewer": "ciso",
                },
                depends_on=["remediate_gaps"],
                next_steps=["package_evidence"],
            ),
            WorkflowStep(
                id="package_evidence",
                name="Package Evidence for Auditor",
                type=StepType.ACTION,
                description="Package and deliver evidence to auditor",
                agent="evidence_agent",
                tool="package",
                parameters={"format": "zip", "encryption": "pgp", "manifest": True},
                depends_on=["final_review"],
            ),
        ],
        tags=["audit", "preparation", "compliance"],
        timeout_seconds=14400.0,
    )


def _incident_response_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Incident Response",
        description="Automated incident response and remediation workflow",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.EVENT,
        steps=[
            WorkflowStep(
                id="detect",
                name="Detect Incident",
                type=StepType.ACTION,
                description="Detect and classify security incident",
                agent="security_agent",
                tool="detect",
                parameters={"severity_classification": True},
                next_steps=["triage"],
            ),
            WorkflowStep(
                id="triage",
                name="Triage Incident",
                type=StepType.DECISION,
                description="Triage incident severity and assign response team",
                agent="security_agent",
                tool="triage",
                parameters={"escalation_matrix": "standard"},
                depends_on=["detect"],
                next_steps=["contain"],
            ),
            WorkflowStep(
                id="contain",
                name="Contain Incident",
                type=StepType.ACTION,
                description="Contain incident to prevent further damage",
                agent="security_agent",
                tool="contain",
                parameters={"isolation": True, "preserve_evidence": True},
                depends_on=["triage"],
                next_steps=["investigate"],
            ),
            WorkflowStep(
                id="investigate",
                name="Investigate Root Cause",
                type=StepType.ACTION,
                description="Investigate root cause and scope of incident",
                agent="security_agent",
                tool="investigate",
                parameters={"forensics": True, "timeline_reconstruction": True},
                depends_on=["contain"],
                next_steps=["remediate"],
            ),
            WorkflowStep(
                id="remediate",
                name="Remediate Incident",
                type=StepType.ACTION,
                description="Remediate incident and restore services",
                agent="security_agent",
                tool="remediate",
                parameters={"restore_from_backup": True, "patch_vulnerabilities": True},
                depends_on=["investigate"],
                next_steps=["notify"],
            ),
            WorkflowStep(
                id="notify",
                name="Notify Stakeholders",
                type=StepType.NOTIFICATION,
                description="Notify stakeholders of incident status",
                parameters={
                    "message": "Incident response in progress. Status update attached.",
                    "channels": ["email", "slack", "pagerduty"],
                    "recipients": ["security_team", "management", "legal"],
                },
                depends_on=["remediate"],
                next_steps=["post_mortem"],
            ),
            WorkflowStep(
                id="post_mortem",
                name="Conduct Post-Mortem",
                type=StepType.HUMAN_APPROVAL,
                description="Schedule and conduct post-incident review",
                parameters={
                    "prompt": "Schedule post-incident review meeting",
                    "reviewer": "incident_commander",
                },
                depends_on=["notify"],
            ),
        ],
        tags=["incident", "response", "security"],
        timeout_seconds=7200.0,
    )


def _risk_assessment_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Risk Assessment",
        description="Comprehensive risk assessment and scoring workflow",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.MANUAL,
        steps=[
            WorkflowStep(
                id="identify_assets",
                name="Identify Assets",
                type=StepType.ACTION,
                description="Identify and catalog organizational assets",
                agent="risk_agent",
                tool="identify_assets",
                parameters={"asset_types": ["data", "systems", "people", "processes"]},
                next_steps=["identify_threats"],
            ),
            WorkflowStep(
                id="identify_threats",
                name="Identify Threats",
                type=StepType.ACTION,
                description="Identify potential threats to assets",
                agent="risk_agent",
                tool="identify_threats",
                parameters={"threat_library": "mitre_attack"},
                depends_on=["identify_assets"],
                next_steps=["assess_vulnerabilities"],
            ),
            WorkflowStep(
                id="assess_vulnerabilities",
                name="Assess Vulnerabilities",
                type=StepType.ACTION,
                description="Assess vulnerabilities and control gaps",
                agent="risk_agent",
                tool="assess_vulnerabilities",
                parameters={"scan_types": ["network", "application", "config"]},
                depends_on=["identify_threats"],
                next_steps=["score_risks"],
            ),
            WorkflowStep(
                id="score_risks",
                name="Score and Prioritize Risks",
                type=StepType.ACTION,
                description="Score risks and prioritize remediation",
                agent="risk_agent",
                tool="score_risks",
                parameters={"scoring_method": "fair", "risk_appetite": "moderate"},
                depends_on=["assess_vulnerabilities"],
                next_steps=["generate_risk_register"],
            ),
            WorkflowStep(
                id="generate_risk_register",
                name="Generate Risk Register",
                type=StepType.ACTION,
                description="Generate comprehensive risk register",
                agent="reporting_agent",
                tool="generate_risk_register",
                parameters={"format": "xlsx", "include_mitigations": True},
                depends_on=["score_risks"],
                next_steps=["approve_risk_register"],
            ),
            WorkflowStep(
                id="approve_risk_register",
                name="Approve Risk Register",
                type=StepType.HUMAN_APPROVAL,
                description="Risk committee approval of risk register",
                parameters={
                    "prompt": "Review and approve the risk register",
                    "reviewer": "risk_committee",
                },
                depends_on=["generate_risk_register"],
            ),
        ],
        tags=["risk", "assessment", "governance"],
        timeout_seconds=7200.0,
    )


def _continuous_compliance_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="Continuous Compliance Monitoring",
        description="Continuous monitoring of compliance posture",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.SCHEDULED,
        cron_expression="0 */6 * * *",
        steps=[
            WorkflowStep(
                id="scan_posture",
                name="Scan Compliance Posture",
                type=StepType.ACTION,
                description="Scan current compliance posture across all frameworks",
                agent="compliance_agent",
                tool="scan_posture",
                parameters={"frameworks": ["SOC2", "ISO27001", "GDPR", "HIPAA"]},
                next_steps=["detect_drift"],
            ),
            WorkflowStep(
                id="detect_drift",
                name="Detect Configuration Drift",
                type=StepType.ACTION,
                description="Detect drift from compliant baseline",
                agent="compliance_agent",
                tool="detect_drift",
                parameters={"baseline": "last_known_good"},
                depends_on=["scan_posture"],
                next_steps=["assess_impact"],
            ),
            WorkflowStep(
                id="assess_impact",
                name="Assess Drift Impact",
                type=StepType.DECISION,
                description="Assess compliance impact of detected drift",
                agent="compliance_agent",
                tool="assess_impact",
                parameters={"impact_levels": ["none", "low", "medium", "high", "critical"]},
                depends_on=["detect_drift"],
                next_steps=["auto_remediate"],
            ),
            WorkflowStep(
                id="auto_remediate",
                name="Auto-Remediate Drift",
                type=StepType.ACTION,
                description="Auto-remediate low-risk configuration drift",
                agent="remediation_agent",
                tool="auto_remediate",
                parameters={"max_severity": "medium", "dry_run": False},
                depends_on=["assess_impact"],
                condition=StepCondition(
                    expression="context.get('drift_severity', 'none') in ['low', 'medium']"
                ),
                next_steps=["update_dashboard"],
            ),
            WorkflowStep(
                id="update_dashboard",
                name="Update Compliance Dashboard",
                type=StepType.ACTION,
                description="Update compliance monitoring dashboard",
                agent="reporting_agent",
                tool="update_dashboard",
                parameters={"real_time": True},
                depends_on=["assess_impact"],
                next_steps=["alert_if_critical"],
            ),
            WorkflowStep(
                id="alert_if_critical",
                name="Alert on Critical Drift",
                type=StepType.NOTIFICATION,
                description="Send alerts for critical compliance drift",
                parameters={
                    "message": "Critical compliance drift detected. Immediate action required.",
                    "channels": ["pagerduty", "slack", "email"],
                },
                depends_on=["update_dashboard"],
                condition=StepCondition(
                    expression="context.get('drift_severity', 'none') == 'critical'"
                ),
            ),
        ],
        tags=["compliance", "monitoring", "continuous"],
        timeout_seconds=3600.0,
    )


class WorkflowTemplates:
    """Registry of pre-built workflow templates."""

    def __init__(self):
        self._templates: dict[str, WorkflowTemplate] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(WorkflowTemplate(
            name="compliance_assessment",
            description="Automated compliance assessment against configured frameworks",
            category="compliance",
            definition_factory=_compliance_assessment_workflow,
            tags=["compliance", "assessment", "audit"],
        ))
        self.register(WorkflowTemplate(
            name="policy_enforcement",
            description="Detect and remediate policy violations across infrastructure",
            category="enforcement",
            definition_factory=_policy_enforcement_workflow,
            tags=["policy", "enforcement", "remediation"],
        ))
        self.register(WorkflowTemplate(
            name="evidence_collection",
            description="Collect and validate GRC evidence from multiple sources",
            category="evidence",
            definition_factory=_evidence_collection_workflow,
            tags=["evidence", "collection", "compliance"],
        ))
        self.register(WorkflowTemplate(
            name="audit_preparation",
            description="Prepare organization for upcoming compliance audit",
            category="audit",
            definition_factory=_audit_preparation_workflow,
            tags=["audit", "preparation", "compliance"],
        ))
        self.register(WorkflowTemplate(
            name="incident_response",
            description="Automated incident response and remediation workflow",
            category="incident",
            definition_factory=_incident_response_workflow,
            tags=["incident", "response", "security"],
        ))
        self.register(WorkflowTemplate(
            name="risk_assessment",
            description="Comprehensive risk assessment and scoring workflow",
            category="risk",
            definition_factory=_risk_assessment_workflow,
            tags=["risk", "assessment", "governance"],
        ))
        self.register(WorkflowTemplate(
            name="continuous_compliance",
            description="Continuous monitoring of compliance posture",
            category="compliance",
            definition_factory=_continuous_compliance_workflow,
            tags=["compliance", "monitoring", "continuous"],
        ))

    def register(self, template: WorkflowTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[WorkflowTemplate]:
        return self._templates.get(name)

    def list_templates(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[WorkflowTemplate]:
        results = list(self._templates.values())
        if category is not None:
            results = [t for t in results if t.category == category]
        if tag is not None:
            results = [t for t in results if tag in t.tags]
        return results

    def instantiate(
        self,
        name: str,
        workflow_name: Optional[str] = None,
        **overrides: Any,
    ) -> WorkflowDefinition:
        template = self._templates.get(name)
        if template is None:
            raise KeyError(f"workflow template '{name}' not found")
        return template.instantiate(workflow_name or name, **overrides)
