/**
 * GRC_Claw TypeScript SDK - Client Setup & Configuration
 * =======================================================
 * Demonstrates how to initialize the GRC_Claw client with various configurations.
 */

import { GRCClawClient, Environment } from '@grc-claw/sdk';

// --- Basic Setup ---
const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: Environment.PRODUCTION,
});

// --- Custom Timeout & Retries ---
const clientCustom = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: Environment.STAGING,
  timeout: 60,
  maxRetries: 5,
});

// --- Development Environment ---
const clientDev = new GRCClawClient({
  apiKey: 'grc_test_xyz789...',
  tenantId: 'org-acme',
  environment: Environment.DEVELOPMENT,
});

// --- Using Environment Variables ---
const clientEnv = new GRCClawClient({
  apiKey: process.env.GRC_API_KEY!,
  tenantId: process.env.GRC_TENANT_ID!,
  environment: (process.env.GRC_ENV as Environment) || Environment.PRODUCTION,
});

// --- List Policies ---
async function listPolicies() {
  const { data, pagination } = await client.policies.list({ limit: 10 });
  console.log(`Found ${pagination.total} policies`);
  for (const p of data) {
    console.log(`  ${p.id}: ${p.name} (v${p.version})`);
  }
}

listPolicies();
