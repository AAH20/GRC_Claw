"""
GRC_Claw Python SDK - Agent Registry
======================================
Register, update, and manage AI agents.
"""

from grc_claw import GRCClawClient, AgentLifecycleStage, RiskTier

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- List Agents ---
agents, pagination = client.agents.list(
    lifecycle_stage=AgentLifecycleStage.ACTIVE,
    risk_tier=RiskTier.LIMITED,
    limit=50,
)
for a in agents:
    print(f"  {a.id}: {a.name} ({a.risk_tier})")

# --- Register Agent ---
agent = client.agents.register(
    name="Data Analyst Agent",
    type="agent",
    framework="langchain",
    risk_tier=RiskTier.LIMITED,
    owner="data-team",
    capabilities=[
        {
            "name": "read_data",
            "description": "Read data from approved sources",
            "permissions": ["s3:GetObject"],
            "resource_scope": "s3://data/public/*",
        }
    ],
)
print(f"Agent registered: {agent.id}")

# --- Get Agent ---
agent = client.agents.get(agent_id="agent-1")
print(f"Agent: {agent.name}, stage: {agent.lifecycle_stage}")

# --- Update Agent ---
updated = client.agents.update(
    agent_id="agent-1",
    lifecycle_stage=AgentLifecycleStage.ACTIVE,
    risk_tier=RiskTier.MINIMAL,
)
print(f"Updated agent: {updated.lifecycle_stage}")

# --- Update Trust Score ---
agent = client.agents.update_trust_score(
    agent_id="agent-1",
    value=85,
    grade="B",
    reason="Completed security review",
)
print(f"Trust score: {agent.trust_score.value} ({agent.trust_score.grade})")

# --- Bind Policies ---
agent = client.agents.bind_policies(
    agent_id="agent-1",
    policy_ids=["pol-001", "pol-002"],
)
print(f"Policy bindings: {agent.policy_bindings}")