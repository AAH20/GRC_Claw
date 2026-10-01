"""
GRC_Claw Python SDK - Compliance Management
============================================
Frameworks, controls, posture, mappings, and crosswalks.
"""

from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- List Frameworks ---
frameworks = client.compliance.list_frameworks()
for fw in frameworks:
    print(f"  {fw.id}: {fw.name} ({fw.control_count} controls)")

# --- List Controls ---
controls = client.compliance.list_controls(
    framework_id="fw-001",
    category="Access Control",
)
for ctrl in controls:
    print(f"  {ctrl.control_key}: {ctrl.title}")

# --- Get Compliance Posture ---
posture = client.compliance.get_posture(
    framework="NIST-800-53",
    target_id="org-acme",
    target_type="organization",
)
print(f"Compliance score: {posture.compliance_score}%")
print(f"  Assessed: {posture.controls_assessed}")
print(f"  Compliant: {posture.controls_compliant}")
print(f"  Non-compliant: {posture.controls_non_compliant}")
print(f"  Not assessed: {posture.controls_not_assessed}")
for gap in posture.gaps:
    print(f"  Gap: {gap.control_title} ({gap.severity})")

# --- Create Mapping ---
mapping = client.compliance.create_mapping(
    control_id="ctrl-001",
    mapping_type="policy",
    coverage="full",
    policy_id="pol-001",
    notes="Policy fully covers this control",
)
print(f"Mapping created: {mapping.id}")

# --- Crosswalk ---
crosswalk = client.compliance.crosswalk(
    control_id="ctrl-001",
    framework="NIST-800-53",
    target_framework="SOC2",
)
print(f"Crosswalk: {crosswalk}")

# --- Generate Compliance Report ---
report = client.compliance.generate_report(
    framework="NIST-800-53",
    time_range={"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"},
    format="json",
    include_evidence=True,
    include_gaps=True,
)
print(f"Report: {report}")