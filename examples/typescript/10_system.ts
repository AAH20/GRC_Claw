/**
 * GRC_Claw TypeScript SDK - System & Health
 * ======================================
 * Health checks, readiness, and metrics.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function systemExamples() {
  // --- Health Check ---
  const health = await client.system.health();
  console.log(`Status: ${health.status}`);
  console.log(`Version: ${health.version}`);
  for (const [name, info] of Object.entries(health.components)) {
    console.log(`  ${name}: ${info.status}`);
  }

  // --- Readiness Check ---
  const ready = await client.system.ready();
  console.log(`Ready: ${ready.ready}`);
  for (const [name, info] of Object.entries(ready.checks)) {
    console.log(`  ${name}: ${info.status}`);
  }

  // --- Metrics ---
  const metrics = await client.system.metrics();
  console.log(`Metrics:\n${metrics}`);
}

systemExamples().catch(console.error);
