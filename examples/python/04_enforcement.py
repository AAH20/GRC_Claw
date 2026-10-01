"""
GRC_Claw Python SDK - Enforcement Decisions
============================================
Request single and batch enforcement decisions.
"""

from grc_claw import GRCClawClient, EnforcementVerdict

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Single Decision ---
decision = client.enforcement.decide(
    agent_id="agent-42",
    action="read",
    resource="s3://data/public/dataset.csv",
    context={"environment": "production", "purpose": "analytics"},
    policy_ids=["pol-001", "pol-002"],
    include_evidence=True,
)
print(f"Decision: {decision.verdict}")
print(f"  Policy: {decision.policy_id} v{decision.policy_version}")
print(f"  Reason: {decision.reason}")
print(f"  Evaluation time: {decision.evaluation_time_ms}ms")

# --- Batch Decision ---
decisions_input = [
    {"agent_id": "agent-1", "action": "read", "resource": "s3://bucket/file1.csv"},
    {"agent_id": "agent-2", "action": "write", "resource": "s3://bucket/file2.csv"},
    {"agent_id": "agent-3", "action": "delete", "resource": "s3://bucket/file3.csv"},
]
results, summary = client.enforcement.decide_batch(decisions=decisions_input)
print(f"Batch results: {summary.allowed} allowed, {summary.denied} denied")
for r in results:
    print(f"  {r.decision_id}: {r.verdict}")

# --- Get Decision ---
decision = client.enforcement.get(decision_id="dec-001")
print(f"Decision {decision.decision_id}: {decision.verdict}")

# --- List Decisions ---
decisions, pagination = client.enforcement.list(
    agent_id="agent-42",
    verdict=EnforcementVerdict.ALLOW,
    limit=50,
)
for d in decisions:
    print(f"  {d.decision_id}: {d.action} on {d.resource} -> {d.verdict}")