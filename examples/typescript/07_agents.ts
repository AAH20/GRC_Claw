/**
 * GRC_Claw TypeScript SDK - Agent Registry
 * ======================================
 * Register, update, and manage AI agents.
 */

import { GRCClawClient, AgentLifecycleStage, RiskTier } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function agentExamples() {
  // --- List Agents ---
  const { data: agents } = await client.agents.list({
    lifecycleStage: AgentLifecycleStage.ACTIVE,
    riskTier: RiskTier.LIMITED,
    limit: 50,
  });
  for (const a of agents) {
    console.log(`  ${a.id}: ${a.name} (${a.riskTier})`);
  }

  // --- Register Agent ---
  const agent = await client.agents.register({
    name: 'Data Analyst Agent',
    type: 'agent',
    framework: 'langchain',
    riskTier: RiskTier.LIMITED,
    owner: 'data-team',
    capabilities: [
      {
        name: 'read_data',
        description: 'Read data from approved sources',
        permissions: ['s3:GetObject'],
        resourceScope: 's3://data/public/*',
      },
    ],
  });
  console.log(`Agent registered: ${agent.id}`);

  // --- Get Agent ---
  const fetched = await client.agents.get('agent-1');
  console.log(`Agent: ${fetched.name}, stage: ${fetched.lifecycleStage}`);

  // --- Update Agent ---
  const updated = await client.agents.update('agent-1', {
    lifecycleStage: AgentLifecycleStage.ACTIVE,
    riskTier: RiskTier.MINIMAL,
  });
  console.log(`Updated: ${updated.lifecycleStage}`);

  // --- Update Trust Score ---
  const scored = await client.agents.updateTrustScore('agent-1', {
    value: 85,
    grade: 'B',
    reason: 'Completed security review',
  });
  console.log(`Trust score: ${scored.trustScore?.value} (${scored.trustScore?.grade})`);

  // --- Bind Policies ---
  const bound = await client.agents.bindPolicies('agent-1', ['pol-001', 'pol-002']);
  console.log(`Policy bindings: ${bound.policyBindings}`);
}

agentExamples().catch(console.error);
