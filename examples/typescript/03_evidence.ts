/**
 * GRC_Claw TypeScript SDK - Evidence Management
 * ============================================
 * Submit, search, verify, and export evidence.
 */

import { GRCClawClient, EvidenceType, VerificationLevel } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function evidenceExamples() {
  // --- Submit Evidence ---
  const evidence = await client.evidence.submit({
    source: { type: 'automated_scan', system: 'nessus', collectionMethod: 'api' },
    evidenceType: EvidenceType.ARTIFACT,
    content: { format: 'application/json', data: '{"scan_id": "scan-123", "findings": 5}' },
    policyId: 'pol-001',
    assessmentId: 'asm-001',
    context: { environment: 'production', region: 'us-east-1', metadata: { scanDate: '2024-01-15' } },
    controlMapping: { controlId: 'AC-2', framework: 'NIST-800-53', controlTitle: 'Account Management' },
  });
  console.log(`Evidence submitted: ${evidence.evidenceId}`);

  // --- Search Evidence ---
  const { data: results, pagination } = await client.evidence.search({
    policyId: 'pol-001',
    evidenceType: EvidenceType.ARTIFACT,
    framework: 'NIST-800-53',
    verificationLevel: VerificationLevel.L2,
    environment: 'production',
    limit: 50,
  });
  for (const ev of results) {
    console.log(`  ${ev.evidenceId}: ${ev.evidenceType}`);
  }

  // --- Get Evidence ---
  const fetched = await client.evidence.get('evd-001');
  console.log(`Evidence: ${fetched.evidenceId}, status: ${fetched.validation?.status}`);

  // --- Verify Evidence ---
  const verification = await client.evidence.verify('evd-001');
  console.log(`Verification: ${JSON.stringify(verification.verificationResult)}`);

  // --- Export ---
  const exportPkg = await client.evidence.export({
    framework: 'NIST-800-53',
    timeRange: { start: '2024-01-01T00:00:00Z', end: '2024-01-31T23:59:59Z' },
    format: 'json',
    includeChainOfCustody: true,
  });
  console.log(`Export: ${exportPkg.packageId}, status: ${exportPkg.status}`);

  // --- Check Export Status ---
  const status = await client.evidence.getExport(exportPkg.packageId);
  console.log(`Export status: ${status.status}`);
  if (status.downloadUrl) console.log(`Download: ${status.downloadUrl}`);
}

evidenceExamples().catch(console.error);
