/**
 * GRC_Claw TypeScript SDK - Async Operations
 * =======================================
 * Using the SDK with async/await for concurrent operations.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function asyncExamples() {
  // --- Concurrent API Calls ---
  const [policiesResult, agentsResult, health] = await Promise.all([
    client.policies.list({ limit: 10 }),
    client.agents.list({ limit: 10 }),
    client.system.health(),
  ]);

  console.log(`Health: ${health.status}`);
  console.log(`Policies: ${policiesResult.pagination.total}`);
  console.log(`Agents: ${agentsResult.data.length}`);

  // --- Concurrent Enforcement Decisions ---
  const decisions = await Promise.all(
    Array.from({ length: 10 }, (_, i) =>
      client.enforcement.decide({
        agentId: `agent-${i}`,
        action: 'read',
        resource: `s3://bucket/file${i}.csv`,
      })
    )
  );

  for (const d of decisions) {
    console.log(`  ${d.decisionId}: ${d.verdict}`);
  }
}

asyncExamples().catch(console.error);
