/**
 * GRC_Claw TypeScript SDK - Policy Management
 * ==========================================
 * Full CRUD operations for policies, including compile, dry-run, versions, and dependencies.
 */

import { GRCClawClient, PolicyCategory, PolicyStatus } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function policyExamples() {
  // --- List Policies ---
  const { data: policies, pagination } = await client.policies.list({
    status: PolicyStatus.ACTIVE,
    category: PolicyCategory.PRIVACY,
    limit: 50,
  });
  for (const p of policies) {
    console.log(`  ${p.id}: ${p.name} (v${p.version})`);
  }

  // --- Create Policy ---
  const policy = await client.policies.create({
    policyKey: 'AI-ETHICS-001',
    name: 'Data Access Control Policy',
    category: PolicyCategory.PRIVACY,
    description: 'Controls access to sensitive data by AI agents',
    frameworkTags: ['NIST-800-53', 'SOC2', 'ISO-42001'],
    cedarPolicy: `
      permit(principal, action, resource) when {
        principal.role == "analyst" &&
        action == "read" &&
        resource.classification == "public"
      };
    `,
    metadata: { owner: 'security-team', reviewCycle: 'quarterly' },
  });
  console.log(`Created policy: ${policy.id}`);

  // --- Get Policy ---
  const fetched = await client.policies.get('pol-001');
  console.log(`Policy: ${fetched.name} (status: ${fetched.status})`);

  // --- Update Policy ---
  const updated = await client.policies.update('pol-001', {
    name: 'Data Access Control Policy v2',
    description: 'Updated with stricter controls',
  });
  console.log(`Updated to version: ${updated.version}`);

  // --- Compile Policy ---
  const compiled = await client.policies.compile('pol-001');
  console.log(`Compilation: ${compiled.compilationStatus}`);

  // --- Dry Run ---
  const dryRun = await client.policies.dryRun('pol-001', [
    { principal: { role: 'analyst' }, action: 'read', resource: { classification: 'public' } },
    { principal: { role: 'intern' }, action: 'read', resource: { classification: 'confidential' } },
  ]);
  console.log(`Dry run: ${dryRun.summary.allowed} allowed, ${dryRun.summary.denied} denied`);

  // --- Get Versions ---
  const { data: versions } = await client.policies.getVersions('pol-001');
  for (const v of versions) {
    console.log(`  v${v.version}: ${v.status}`);
  }

  // --- Get Dependencies ---
  const deps = await client.policies.getDependencies('pol-001');
  console.log(`Dependencies: ${deps.dependencies.length}, Dependents: ${deps.dependents.length}`);

  // --- Delete ---
  await client.policies.delete('pol-001', true);
  console.log('Policy deleted');
}

policyExamples().catch(console.error);
