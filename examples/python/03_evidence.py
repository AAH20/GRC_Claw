"""
GRC_Claw Python SDK - Evidence Management
==========================================
Submit, search, verify, and export evidence.
"""

from grc_claw import GRCClawClient, EvidenceType, VerificationLevel

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Submit Evidence ---
evidence = client.evidence.submit(
    source={
        "type": "automated_scan",
        "system": "nessus",
        "collection_method": "api",
    },
    evidence_type=EvidenceType.ARTIFACT,
    content={
        "format": "application/json",
        "data": '{"scan_id": "scan-123", "findings": 5, "severity": "high"}',
    },
    policy_id="pol-001",
    assessment_id="asm-001",
    context={
        "environment": "production",
        "region": "us-east-1",
        "metadata": {"scan_date": "2024-01-15"},
    },
    control_mapping={
        "control_id": "AC-2",
        "framework": "NIST-800-53",
        "control_title": "Account Management",
    },
)
print(f"Evidence submitted: {evidence.evidence_id}")

# --- Search Evidence ---
results, pagination = client.evidence.search(
    policy_id="pol-001",
    evidence_type=EvidenceType.ARTIFACT,
    framework="NIST-800-53",
    verification_level=VerificationLevel.L2,
    environment="production",
    limit=50,
)
for ev in results:
    print(f"  {ev.evidence_id}: {ev.evidence_type} (L{ev.verification_level})")

# --- Get Evidence ---
evidence = client.evidence.get(evidence_id="evd-001")
print(f"Evidence: {evidence.evidence_id}, status: {evidence.validation.status}")

# --- Verify Evidence ---
verification = client.evidence.verify(evidence_id="evd-001")
print(f"Verification: {verification.verification_result}")

# --- Export Evidence Package ---
export = client.evidence.export(
    framework="NIST-800-53",
    time_range={"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"},
    format="json",
    include_chain_of_custody=True,
)
print(f"Export package: {export.package_id}, status: {export.status}")

# --- Check Export Status ---
export_status = client.evidence.get_export(package_id=export.package_id)
print(f"Export status: {export_status.status}")
if export_status.download_url:
    print(f"Download URL: {export_status.download_url}")