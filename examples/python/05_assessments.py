"""
GRC_Claw Python SDK - Assessment Management
============================================
Create, update, and report on assessments.
"""

from grc_claw import GRCClawClient, AssessmentType, AssessmentStatus

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- List Assessments ---
assessments, pagination = client.assessments.list(
    assessment_type=AssessmentType.RISK,
    status=AssessmentStatus.IN_PROGRESS,
    limit=50,
)
for a in assessments:
    print(f"  {a.id}: {a.title} ({a.status})")

# --- Create Assessment ---
assessment = client.assessments.create(
    assessment_key="RISK-2024-Q1",
    title="Q1 2024 Risk Assessment",
    assessment_type=AssessmentType.RISK,
    target_id="org-acme",
    target_type="organization",
    description="Quarterly risk assessment for all AI agents",
    methodology="NIST RMF",
    lead_assessor="security-team",
    metadata={"quarter": "Q1", "year": 2024},
)
print(f"Created assessment: {assessment.id}")

# --- Get Assessment ---
assessment = client.assessments.get(assessment_id="asm-001")
print(f"Assessment: {assessment.title}, status: {assessment.status}")

# --- Update Assessment ---
updated = client.assessments.update(
    assessment_id="asm-001",
    status=AssessmentStatus.IN_PROGRESS,
    score=85.0,
    risk_level="medium",
)
print(f"Updated assessment: score={updated.score}, risk={updated.risk_level}")

# --- Add Finding ---
finding = client.assessments.add_finding(
    assessment_id="asm-001",
    finding_key="FIND-001",
    title="Unrestricted data access by Agent-42",
    severity="high",
    category="access_control",
    description="Agent-42 has access to confidential data without approval",
    policy_id="pol-001",
    evidence_ids=["evd-001", "evd-002"],
    remediation="Implement role-based access control",
    due_date="2024-02-15T00:00:00Z",
)
print(f"Finding added: {finding.id}")

# --- Generate Report ---
report = client.assessments.generate_report(
    assessment_id="asm-001",
    format="pdf",
    include_evidence=True,
    include_remediation=True,
)
print(f"Report generated: {report}")