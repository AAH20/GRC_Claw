/**
 * GRC_Claw TypeScript SDK - Compliance Management
 * ============================================
 * Frameworks, controls, posture, mappings, and crosswalks.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function complianceExamples() {
  // --- List Frameworks ---
  const { data: frameworks } = await client.compliance.listFrameworks();
  for (const fw of frameworks) {
    console.log(`  ${fw.id}: ${fw.name} (${fw.controlCount} controls)`);
  }

  // --- List Controls ---
  const { data: controls } = await client.compliance.listControls('fw-001', {
    category: 'Access Control',
  });
  for (const ctrl of controls) {
    console.log(`  ${ctrl.controlKey}: ${ctrl.title}`);
  }

  // --- Get Posture ---
  const posture = await client.compliance.getPosture({
    framework: 'NIST-800-53',
    targetId: 'org-acme',
    targetType: 'organization',
  });
  console.log(`Score: ${posture.complianceScore}%`);
  console.log(`  Assessed: ${posture.controlsAssessed}`);
  console.log(`  Compliant: ${posture.controlsCompliant}`);
  console.log(`  Non-compliant: ${posture.controlsNonCompliant}`);
  for (const gap of posture.gaps) {
    console.log(`  Gap: ${gap.controlTitle} (${gap.severity})`);
  }

  // --- Create Mapping ---
  const mapping = await client.compliance.createMapping({
    controlId: 'ctrl-001',
    mappingType: 'policy',
    coverage: 'full',
    policyId: 'pol-001',
    notes: 'Policy fully covers this control',
  });
  console.log(`Mapping: ${mapping.id}`);

  // --- Crosswalk ---
  const crosswalk = await client.compliance.crosswalk({
    controlId: 'ctrl-001',
    framework: 'NIST-800-53',
    targetFramework: 'SOC2',
  });
  console.log(`Crosswalk: ${JSON.stringify(crosswalk)}`);

  // --- Generate Report ---
  const report = await client.compliance.generateReport({
    framework: 'NIST-800-53',
    timeRange: { start: '2024-01-01T00:00:00Z', end: '2024-01-31T23:59:59Z' },
    format: 'json',
    includeEvidence: true,
    includeGaps: true,
  });
  console.log(`Report: ${JSON.stringify(report)}`);
}

complianceExamples().catch(console.error);
