"""
Workflow templates for GRC_Claw.

Pre-built workflow templates for common GRC processes including
compliance assessments, policy enforcement, evidence collection,
audit preparation, and incident response.
"""

from __future__ import annotations

import logging
from typing import Any

from .schema import (
    StepCondition,
    StepType,
    TriggerType,
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


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


def _vendor_assessment_workflow() -> WorkflowDefinition:
    """Template for third-party vendor risk assessment."""
    return WorkflowDefinition(
        name="Vendor Assessment",
        description="Third-party vendor risk assessment workflow",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.MANUAL,
        steps=[
            WorkflowStep(
                id="identify_vendor",
                name="Identify Vendor",
                type=StepType.ACTION,
                description="Identify vendor and scope of assessment",
                agent="vendor_agent",
                tool="identify_vendor",
                parameters={},
                next_steps=["send_questionnaire"],
            ),
            WorkflowStep(
                id="send_questionnaire",
                name="Send Security Questionnaire",
                type=StepType.ACTION,
                description="Send security assessment questionnaire",
                agent="vendor_agent",
                tool="send_questionnaire",
                parameters={"template": "vendor_security_assessment"},
                depends_on=["identify_vendor"],
                next_steps=["review_responses"],
            ),
            WorkflowStep(
                id="review_responses",
                name="Review Questionnaire Responses",
                type=StepType.ACTION,
                description="Review and score questionnaire responses",
                agent="assessment_agent",
                tool="review_responses",
                parameters={},
                depends_on=["send_questionnaire"],
                next_steps=["conduct_due_diligence"],
            ),
            WorkflowStep(
                id="conduct_due_diligence",
                name="Conduct Due Diligence",
                type=StepType.PARALLEL,
                description="Conduct due diligence activities",
                agent="due_diligence_agent",
                tool="conduct_due_diligence",
                parameters={"check_financials": True, "check_litigation": True},
                depends_on=["review_responses"],
                next_steps=["risk_rating"],
            ),
            WorkflowStep(
                id="risk_rating",
                name="Assign Risk Rating",
                type=StepType.DECISION,
                description="Assign overall vendor risk rating",
                parameters={"scale": "low_medium_high_critical"},
                depends_on=["conduct_due_diligence"],
                next_steps=["approve_vendor"],
            ),
            WorkflowStep(
                id="approve_vendor",
                name="Approve or Reject Vendor",
                type=StepType.HUMAN_APPROVAL,
                description="Approve or reject vendor based on risk rating",
                parameters={"approvers": ["procurement", "security", "legal"]},
                depends_on=["risk_rating"],
                next_steps=["onboard_vendor"],
            ),
            WorkflowStep(
                id="onboard_vendor",
                name="Onboard Vendor",
                type=StepType.ACTION,
                description="Onboard approved vendor",
                agent="onboarding_agent",
                tool="onboard_vendor",
                parameters={},
                depends_on=["approve_vendor"],
            ),
        ],
        tags=["vendor", "assessment", "third_party"],
        timeout_seconds=259200.0,
    )


def _control_testing_workflow() -> WorkflowDefinition:
    """Template for testing compliance controls."""
    return WorkflowDefinition(
        name="Control Testing",
        description="Test operating effectiveness of compliance controls",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.SCHEDULED,
        cron_expression="0 0 1 * *",
        steps=[
            WorkflowStep(
                id="select_controls",
                name="Select Controls for Testing",
                type=StepType.ACTION,
                description="Select controls to test based on risk",
                agent="testing_agent",
                tool="select_controls",
                parameters={"rotation": "annual", "risk_based": True},
                next_steps=["design_tests"],
            ),
            WorkflowStep(
                id="design_tests",
                name="Design Test Procedures",
                type=StepType.ACTION,
                description="Design test procedures for selected controls",
                agent="testing_agent",
                tool="design_tests",
                parameters={},
                depends_on=["select_controls"],
                next_steps=["execute_tests"],
            ),
            WorkflowStep(
                id="execute_tests",
                name="Execute Tests",
                type=StepType.PARALLEL,
                description="Execute test procedures",
                agent="testing_agent",
                tool="execute_tests",
                parameters={"sample_size": 25},
                depends_on=["design_tests"],
                next_steps=["evaluate_results"],
            ),
            WorkflowStep(
                id="evaluate_results",
                name="Evaluate Test Results",
                type=StepType.DECISION,
                description="Evaluate test results for operating effectiveness",
                parameters={"pass_threshold": 0.95},
                depends_on=["execute_tests"],
                next_steps=["document_results"],
            ),
            WorkflowStep(
                id="document_results",
                name="Document Test Results",
                type=StepType.ACTION,
                description="Document test results and conclusions",
                agent="testing_agent",
                tool="document_results",
                parameters={},
                depends_on=["evaluate_results"],
                next_steps=["report_deficiencies"],
            ),
            WorkflowStep(
                id="report_deficiencies",
                name="Report Control Deficiencies",
                type=StepType.NOTIFICATION,
                description="Report any control deficiencies",
                parameters={"channels": ["email"]},
                depends_on=["document_results"],
            ),
        ],
        tags=["control", "testing", "compliance"],
        timeout_seconds=604800.0,
    )


def _policy_review_workflow() -> WorkflowDefinition:
    """Template for periodic policy review and update."""
    return WorkflowDefinition(
        name="Policy Review",
        description="Periodic policy review and update workflow",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.SCHEDULED,
        cron_expression="0 0 1 1 *",
        steps=[
            WorkflowStep(
                id="identify_policies",
                name="Identify Policies for Review",
                type=StepType.ACTION,
                description="Find policies due for review",
                agent="policy_agent",
                tool="list_policies_due",
                parameters={"review_period_months": 12},
                next_steps=["assign_reviewers"],
            ),
            WorkflowStep(
                id="assign_reviewers",
                name="Assign Reviewers",
                type=StepType.ACTION,
                description="Assign policy reviewers",
                agent="policy_agent",
                tool="assign_reviewers",
                parameters={},
                depends_on=["identify_policies"],
                next_steps=["conduct_review"],
            ),
            WorkflowStep(
                id="conduct_review",
                name="Conduct Policy Review",
                type=StepType.ACTION,
                description="Review policy for relevance and accuracy",
                agent="reviewer_agent",
                tool="review_policy",
                parameters={"check_regulatory_alignment": True},
                depends_on=["assign_reviewers"],
                next_steps=["draft_updates"],
            ),
            WorkflowStep(
                id="draft_updates",
                name="Draft Policy Updates",
                type=StepType.ACTION,
                description="Draft necessary policy changes",
                agent="policy_agent",
                tool="draft_policy_update",
                parameters={},
                depends_on=["conduct_review"],
                next_steps=["legal_review"],
            ),
            WorkflowStep(
                id="legal_review",
                name="Legal Review",
                type=StepType.HUMAN_APPROVAL,
                description="Legal team review of policy changes",
                parameters={"approvers": ["legal_team"]},
                depends_on=["draft_updates"],
                next_steps=["approve_policy"],
            ),
            WorkflowStep(
                id="approve_policy",
                name="Approve Updated Policy",
                type=StepType.HUMAN_APPROVAL,
                description="Final approval of updated policy",
                parameters={"approvers": ["policy_owner", "compliance_manager"]},
                depends_on=["legal_review"],
                next_steps=["publish_policy"],
            ),
            WorkflowStep(
                id="publish_policy",
                name="Publish Policy",
                type=StepType.ACTION,
                description="Publish updated policy to document repository",
                agent="publishing_agent",
                tool="publish_policy",
                parameters={"notify_stakeholders": True},
                depends_on=["approve_policy"],
                next_steps=["acknowledge_receipt"],
            ),
            WorkflowStep(
                id="acknowledge_receipt",
                name="Acknowledge Receipt",
                type=StepType.NOTIFICATION,
                description="Collect acknowledgment from affected personnel",
                parameters={"deadline_days": 30},
                depends_on=["publish_policy"],
            ),
        ],
        tags=["policy", "review", "governance"],
        timeout_seconds=259200.0,
    )


def _risk_remediation_workflow() -> WorkflowDefinition:
    """Template for risk assessment and remediation tracking."""
    return WorkflowDefinition(
        name="Risk Remediation",
        description="Assess risks and track remediation efforts",
        version="1.0.0",
        status=WorkflowStatus.ACTIVE,
        trigger=TriggerType.MANUAL,
        steps=[
            WorkflowStep(
                id="identify_risks",
                name="Identify Risks",
                type=StepType.ACTION,
                description="Identify and catalog risks",
                agent="risk_agent",
                tool="identify_risks",
                parameters={},
                next_steps=["assess_risks"],
            ),
            WorkflowStep(
                id="assess_risks",
                name="Assess Risk Severity",
                type=StepType.ACTION,
                description="Assess likelihood and impact of each risk",
                agent="risk_agent",
                tool="assess_risk",
                parameters={"scoring_method": "qualitative"},
                depends_on=["identify_risks"],
                next_steps=["prioritize_risks"],
            ),
            WorkflowStep(
                id="prioritize_risks",
                name="Prioritize Risks",
                type=StepType.DECISION,
                description="Prioritize risks based on severity",
                parameters={"threshold": "medium"},
                depends_on=["assess_risks"],
                next_steps=["develop_mitigation"],
            ),
            WorkflowStep(
                id="develop_mitigation",
                name="Develop Mitigation Plan",
                type=StepType.ACTION,
                description="Create mitigation plans for high-priority risks",
                agent="risk_agent",
                tool="create_mitigation_plan",
                parameters={},
                depends_on=["prioritize_risks"],
                next_steps=["assign_owners"],
            ),
            WorkflowStep(
                id="assign_owners",
                name="Assign Risk Owners",
                type=StepType.ACTION,
                description="Assign owners to each risk",
                agent="risk_agent",
                tool="assign_risk_owner",
                parameters={},
                depends_on=["develop_mitigation"],
                next_steps=["implement_mitigation"],
            ),
            WorkflowStep(
                id="implement_mitigation",
                name="Implement Mitigation",
                type=StepType.ACTION,
                description="Execute mitigation activities",
                agent="remediation_agent",
                tool="implement_mitigation",
                parameters={},
                depends_on=["assign_owners"],
                next_steps=["monitor_progress"],
            ),
            WorkflowStep(
                id="monitor_progress",
                name="Monitor Remediation Progress",
                type=StepType.WAIT,
                description="Monitor remediation implementation",
                parameters={"check_interval_days": 30, "escalate_after_days": 90},
                depends_on=["implement_mitigation"],
                next_steps=["verify_mitigation"],
            ),
            WorkflowStep(
                id="verify_mitigation",
                name="Verify Mitigation Effectiveness",
                type=StepType.ACTION,
                description="Verify that mitigation has reduced risk",
                agent="risk_agent",
                tool="verify_mitigation",
                parameters={},
                depends_on=["monitor_progress"],
                next_steps=["update_risk_register"],
            ),
            WorkflowStep(
                id="update_risk_register",
                name="Update Risk Register",
                type=StepType.ACTION,
                description="Update risk register with current status",
                agent="risk_agent",
                tool="update_risk_register",
                parameters={},
                depends_on=["verify_mitigation"],
            ),
        ],
        tags=["risk", "remediation", "assessment"],
        timeout_seconds=7776000.0,
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
        self.register(WorkflowTemplate(
            name="vendor_assessment",
            description="Third-party vendor risk assessment workflow",
            category="risk",
            definition_factory=_vendor_assessment_workflow,
            tags=["vendor", "assessment", "third_party"],
        ))
        self.register(WorkflowTemplate(
            name="control_testing",
            description="Control operating effectiveness testing workflow",
            category="compliance",
            definition_factory=_control_testing_workflow,
            tags=["control", "testing", "compliance"],
        ))
        self.register(WorkflowTemplate(
            name="policy_review",
            description="Periodic policy review and update workflow",
            category="governance",
            definition_factory=_policy_review_workflow,
            tags=["policy", "review", "governance"],
        ))
        self.register(WorkflowTemplate(
            name="risk_remediation",
            description="Risk assessment and remediation tracking workflow",
            category="risk",
            definition_factory=_risk_remediation_workflow,
            tags=["risk", "remediation", "assessment"],
        ))

    def register(self, template: WorkflowTemplate) -> None:
        self._templates[template.name] = template
        logger.debug("registered workflow template '%s'", template.name)

    def get(self, name: str) -> WorkflowTemplate | None:
        return self._templates.get(name)

    def list_templates(
        self,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[WorkflowTemplate]:
        results = list(self._templates.values())
        if category is not None:
            results = [t for t in results if t.category == category]
        if tag is not None:
            results = [t for t in results if tag in t.tags]
        return results

    def search_templates(self, query: str) -> list[WorkflowTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for t in self._templates.values():
            if (query_lower in t.name.lower()
                or query_lower in t.description.lower()
                or any(query_lower in tag.lower() for tag in t.tags)):
                results.append(t)
        return results

    def get_categories(self) -> list[str]:
        """Get all unique template categories."""
        return sorted(set(t.category for t in self._templates.values()))

    def instantiate(
        self,
        name: str,
        workflow_name: str | None = None,
        **overrides: Any,
    ) -> WorkflowDefinition:
        template = self._templates.get(name)
        if template is None:
            raise KeyError(f"workflow template '{name}' not found")
        return template.instantiate(workflow_name or name, **overrides)

    def get_stats(self) -> dict[str, Any]:
        """Get template registry statistics."""
        categories: dict[str, int] = {}
        for t in self._templates.values():
            categories[t.category] = categories.get(t.category, 0) + 1
        return {
            "total_templates": len(self._templates),
            "by_category": categories,
            "template_names": list(self._templates.keys()),
        }
