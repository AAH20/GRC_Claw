import assert from 'node:assert/strict';
import { ActionLedger } from './action-ledger.js';
import { createAssuranceEnvelope } from './assurance-envelope.js';
import { createAgentTrustPassport } from './agent-trust-passport.js';

const ledger = new ActionLedger();
const intent = ledger.recordIntent({
  tenantId: 42,
  sessionId: 'trust-passport-session',
  tool: 'terraform.plan',
  args: { workspace: 'prod', secret: 'never-export-this' },
  idempotencyKey: 'trust-passport-test-1',
});
const decision = ledger.recordDecision(intent, {
  allowed: true,
  reason: 'human_approval_required_for_prod_iac',
  requiresApproval: true,
});
const result = ledger.recordResult(intent, {
  executionState: 'verified',
  output: { token: 'never-export-this-either' },
  evidenceId: 'ev-iac-plan-001',
  targetReceipt: 'github-pr:123',
});
const envelope = createAssuranceEnvelope({
  intent,
  decision,
  result,
  identity: { agentDid: 'did:grc:agent:devops-001', status: 'verified' },
  assurance: { riskScore: 7, controlId: 'CM.2' },
});

const passport = createAgentTrustPassport({
  generatedAt: '2026-07-17T00:00:00.000Z',
  system: {
    organization: 'A2Z SOC Demo',
    systemName: 'Production IaC Agent',
    environment: 'production',
    owner: 'platform-security',
    dataBoundary: 'tenant_confidential',
  },
  agents: [
    {
      id: 'devops-agent-001',
      name: 'Forward Deployed DevSecOps Agent',
      provider: 'open-router-compatible',
      model: 'deepseek-v4-compatible',
      adapter: 'stakpak_style_devops_agent',
      toolAllowlist: ['terraform.plan', 'evidence.export'],
      approvalMode: 'human',
    },
  ],
  envelopes: [envelope],
  controlMappings: [
    {
      framework: 'NIST_800_171',
      controlId: '3.4.3',
      status: 'evidenced',
      evidenceRefs: ['ev-iac-plan-001'],
    },
    {
      framework: 'ISO_42001',
      controlId: 'A.6.2',
      status: 'limited_evidence',
      evidenceRefs: [],
      limitation: 'Human oversight procedure exists, but external approval record is pending.',
    },
  ],
  risks: [
    {
      id: 'risk-prod-agent-change',
      severity: 'high',
      title: 'Production IaC agent requires explicit approval evidence before apply.',
      mitigation: 'Keep agent in plan-only mode until change approval and rollback receipt are attached.',
      owner: 'platform-security',
    },
  ],
});

assert.equal(passport.version, 'agent-trust-passport/v1');
assert.equal(passport.summary.totalAgents, 1);
assert.equal(passport.summary.totalEnvelopes, 1);
assert.equal(passport.summary.evidencedClaims, 1);
assert.equal(passport.summary.limitedClaims, 1);
assert.equal(passport.summary.approvalRequiredActions, 1);
assert.equal(passport.summary.verifiedEnvelopeCount, 1);
assert.equal(passport.verification.ok, true);
assert.equal(JSON.stringify(passport).includes('never-export-this'), false);
assert.equal(passport.buyerPacket.buyerQuestionsAnswered.length >= 5, true);
