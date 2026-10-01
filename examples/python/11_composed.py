"""
GRC_Claw Python SDK - Composed/Aggregated APIs
================================================
Dashboard, agent 360, compliance report, and executive summary.
"""

from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Dashboard Overview ---
dashboard = client.system.request("GET", "/v1.0/composed/dashboard")
print(f"Compliance score: {dashboard['compliance_summary']['overall_score']}%")
print(f"Active agents: {dashboard['active_agents']['total']}")
print(f"Open findings: {dashboard['open_findings']['total']}")
print(f"Risk alerts: {dashboard['risk_alerts']['active']}")

# --- Agent 360 View ---
agent_360 = client.system.request("GET", "/v1.0/composed/agents/agent-1/360")
print(f"Agent: {agent_360['agent']['name']}")
print(f"  Policies: {len(agent_360['policies'])}")
print(f"  Enforcements (24h): {agent_360['enforcements']['total_24h']}")
print(f"  Evidence: {agent_360['evidence']['total_submitted']}")
print(f"  Assessments: {agent_360['assessments']['completed']}")

# --- Compliance Report ---
report = client.system.request("GET", "/v1.0/composed/compliance-report")
for fw in report["frameworks"]:
    print(f"  {fw['name']}: {fw['score']}% ({fw['status']})")

# --- Executive Summary ---
summary = client.system.request("GET", "/v1.0/composed/executive-summary")
print(f"Overall compliance: {summary['overall_compliance_score']}")
print(f"Risk posture: {summary['risk_posture']}")
print(f"Agent governance: {summary['agent_governance']}")