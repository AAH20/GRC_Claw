/**
 * GRC_Claw TypeScript SDK - Assessment Management
 * ============================================
 * Create, update, and report on assessments.
 */

import { GRCClawClient, AssessmentType, AssessmentStatus } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function assessmentExamples() {
  // --- List Assessments ---
  const { data: assessments } = await client.assessments.list({
    assessmentType: AssessmentType.RISK,
    status: AssessmentStatus.IN_PROGRESS,
    limit: 50,
  });
  for (const a of assessments) {
    console.log(`  ${a.id}: ${a.title} (${a.status})`);
  }

  // --- Create Assessment ---
  const assessment = await client.assessments.create({
    assessmentKey: 'RISK-2024-Q1',
    title: 'Q1 2024 Risk Assessment',
    assessmentType: AssessmentType.RISK,
    targetId: 'org-acme',
    targetType: 'organization',
    description: 'Quarterly risk assessment for all AI agents',
    methodology: 'NIST RMF',
    leadAssessor: 'security-team',
    metadata: { quarter: 'Q1', year: 2024 },
  });
  console.log(`Created: ${assessment.id}`);

  // --- Get Assessment ---
  const fetched = await client.assessments.get('asm-001');
  console.log(`Assessment: ${fetched.title}, status: ${fetched.status}`);

  // --- Update Assessment ---
  const updated = await client.assessments.update('asm-001', {
    status: AssessmentStatus.IN_PROGRESS,
    score: 85.0,
    riskLevel: 'medium',
  });
  console.log(`Updated: score=${updated.score}, risk=${updated.riskLevel}`);

  // --- Add Finding ---
  const finding = await client.assessments.addFinding('asm-001', {
    findingKey: 'FIND-001',
    title: 'Unrestricted data access by Agent-42',
    severity: 'high',
    category: 'access_control',
    description: 'Agent-42 has access to confidential data without approval',
    policyId: 'pol-001',
    evidenceIds: ['evd-001', 'evd-002'],
    remediation: 'Implement role-based access control',
    dueDate: '2024-02-15T00:00:00Z',
  });
  console.log(`Finding: ${finding.id}`);

  // --- Generate Report ---
  const report = await client.assessments.generateReport('asm-001', {
    format: 'pdf',
    includeEvidence: true,
    includeRemediation: true,
  });
  console.log(`Report: ${JSON.stringify(report)}`);
}

assessmentExamples().catch(console.error);
