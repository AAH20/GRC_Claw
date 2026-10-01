"""
GRC_Claw Python SDK - Policy Management
========================================
Full CRUD operations for policies, including compile, dry-run, versions, and dependencies.
"""

from grc_claw import GRCClawClient, PolicyCategory, PolicyStatus

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- List Policies ---
policies, pagination = client.policies.list(
    status=PolicyStatus.ACTIVE,
    category=PolicyCategory.PRIVACY,
    limit=50,
)
for p in policies:
    print(f"  {p.id}: {p.name} (v{p.version})")

# --- Create Policy ---
policy = client.policies.create(
    policy_key="AI-ETHICS-001",
    name="Data Access Control Policy",
    category=PolicyCategory.PRIVACY,
    description="Controls access to sensitive data by AI agents",
    framework_tags=["NIST-800-53", "SOC2", "ISO-42001"],
    cedar_policy="""
        permit(principal, action, resource) when {
            principal.role == "analyst" &&
            action == "read" &&
            resource.classification == "public"
        };
    """,
    metadata={"owner": "security-team", "review_cycle": "quarterly"},
)
print(f"Created policy: {policy.id}")

# --- Get Policy ---
policy = client.policies.get(policy_id="pol-001")
print(f"Policy: {policy.name} (status: {policy.status})")

# --- Update Policy ---
updated = client.policies.update(
    policy_id="pol-001",
    name="Data Access Control Policy v2",
    description="Updated with stricter controls",
    cedar_policy="""
        permit(principal, action, resource) when {
            principal.role == "senior-analyst" &&
            action == "read" &&
            resource.classification == "public"
        };
    """,
)
print(f"Updated to version: {updated.version}")

# --- Compile Policy (Cedar -> Rego) ---
compile_result = client.policies.compile(policy_id="pol-001")
print(f"Compilation status: {compile_result.compilation_status}")
print(f"Rego policy:\n{compile_result.rego_policy}")

# --- Dry Run Policy ---
dry_run = client.policies.dry_run(
    policy_id="pol-001",
    test_inputs=[
        {"principal": {"role": "analyst"}, "action": "read", "resource": {"classification": "public"}},
        {"principal": {"role": "intern"}, "action": "read", "resource": {"classification": "confidential"}},
    ],
)
print(f"Dry run: {dry_run.summary.allowed} allowed, {dry_run.summary.denied} denied")

# --- Get Policy Versions ---
versions = client.policies.get_versions(policy_id="pol-001")
for v in versions:
    print(f"  v{v.version}: {v.status} ({v.change_summary})")

# --- Get Policy Dependencies ---
deps = client.policies.get_dependencies(policy_id="pol-001")
print(f"Dependencies: {len(deps.dependencies)}, Dependents: {len(deps.dependents)}")

# --- Delete Policy ---
client.policies.delete(policy_id="pol-001", force=True)
print("Policy deleted")