/**
 * GRC_Claw TypeScript SDK - Enforcement Decisions
 * ============================================
 * Request single and batch enforcement decisions.
 */

import { GRCClawClient, EnforcementVerdict } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function enforcementExamples() {
  // --- Single Decision ---
  const decision = await client.enforcement.decide({
    agentId: 'agent-42',
    action: 'read',
    resource: 's3://data/public/dataset.csv',
    context: { environment: 'production', purpose: 'analytics' },
    policyIds: ['pol-001', 'pol-002'],
    includeEvidence: true,
  });
  console.log(`Decision: ${decision.verdict}`);
  console.log(`  Policy: ${decision.policyId} v${decision.policyVersion}`);
  console.log(`  Reason: ${decision.reason}`);
  console.log(`  Eval time: ${decision.evaluationTimeMs}ms`);

  // --- Batch Decision ---
  const { results, summary } = await client.enforcement.decideBatch([
    { agentId: 'agent-1', action: 'read', resource: 's3://bucket/file1.csv' },
    { agentId: 'agent-2', action: 'write', resource: 's3://bucket/file2.csv' },
    { agentId: 'agent-3', action: 'delete', resource: 's3://bucket/file3.csv' },
  ]);
  console.log(`Batch: ${summary.allowed} allowed, ${summary.denied} denied`);
  for (const r of results) {
    console.log(`  ${r.decisionId}: ${r.verdict}`);
  }

  // --- Get Decision ---
  const fetched = await client.enforcement.get('dec-001');
  console.log(`Decision ${fetched.decisionId}: ${fetched.verdict}`);

  // --- List Decisions ---
  const { data: decisions } = await client.enforcement.list({
    agentId: 'agent-42',
    verdict: EnforcementVerdict.ALLOW,
    limit: 50,
  });
  for (const d of decisions) {
    console.log(`  ${d.decisionId}: ${d.action} on ${d.resource} -> ${d.verdict}`);
  }
}

enforcementExamples().catch(console.error);
