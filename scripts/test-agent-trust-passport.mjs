/**
 * @domain assurance
 * @layer verification
 * @summary Verifies Agent Trust Passport v1 aggregates action receipts without raw payload leakage.
 * @see packages/evidence/src/agent-trust-passport.ts
 */
import assert from 'node:assert/strict';
import {
  ActionLedger,
  createAgentTrustPassport,
  createAssuranceEnvelope,
} from '../packages/evidence/dist/index.js';

const ledger = new ActionLedger();
const intent = ledger.recordIntent({
  tenantId: 11,
  sessionId: 'agent-trust-passport-script',
  tool: 'kubernetes.manifest.review',
  args: { namespace: 'prod', apiKey: 'never-leak' },
  idempotencyKey: 'agent-trust-passport-script-1',
});
const decision = ledger.recordDecision(intent, { allowed: false, reason: 'prod_requires_dual_control', requiresApproval: true });
const envelope = createAssuranceEnvelope({
  intent,
  decision,
  identity: { agentDid: 'did:grc:test:agent', status: 'verified' },
  assurance: { riskScore: 8, controlId: 'AC.3' },
});
const passport = createAgentTrustPassport({
  generatedAt: '2026-07-17T00:00:00.000Z',
  system: {
    organization: 'A2Z SOC',
    systemName: 'Kubernetes production agent',
    environment: 'production',
    owner: 'cloud-security',
    dataBoundary: 'tenant_confidential',
  },
  agents: [
    {
      id: 'k8s-agent',
      name: 'Kubernetes Assurance Agent',
      provider: 'local',
      adapter: 'kubernetes',
      toolAllowlist: ['kubernetes.manifest.review'],
      approvalMode: 'dual_control',
    },
  ],
  envelopes: [envelope],
  controlMappings: [
    { framework: 'SOC_2', controlId: 'CC6.1', status: 'evidenced', evidenceRefs: [envelope.actionId] },
    { framework: 'CMMC', controlId: 'AC.L2-3.1.2', status: 'limited_evidence', evidenceRefs: [] },
  ],
});

assert.equal(passport.summary.deniedActions, 1);
assert.equal(passport.summary.approvalRequiredActions, 1);
assert.equal(passport.verification.ok, true);
assert.equal(JSON.stringify(passport).includes('never-leak'), false);
console.log('agent trust passport: 4 passed, 0 failed');
