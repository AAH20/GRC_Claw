import assert from 'node:assert/strict';
import test from 'node:test';
import {
  createTrustTransaction,
  hashTrustTransaction,
  redactTrustTransactionForSharing,
  verifyTrustTransaction,
} from './index.js';

test('creates deterministic, verifiable Trust Transaction envelopes', () => {
  const transaction = createTrustTransaction({
    kind: 'agent_intent',
    status: 'approved',
    tenantId: 72,
    orgSlug: 'a2z-soc',
    actor: { id: 'agent:grc-copilot', type: 'agent', tenantId: 72, did: 'did:grc:copilot' },
    action: {
      name: 'collect_evidence',
      tool: 'evidence.collect',
      idempotencyKey: 'collect-evidence-001',
      correlationId: 'case-001',
    },
    policy: {
      policyId: 'agent-policy-firewall/default',
      decision: 'allow',
      sandboxPolicy: 'tenant-read-write-no-secrets',
      approvalThreshold: 'human',
      replayWindowSeconds: 300,
      rollbackPlanId: 'rollback:evidence-collect',
    },
    dataBoundary: 'tenant-confidential',
    evidence: {
      graphId: 'graph:evidence:001',
      graphObjectHash: 'hash:graph-object',
      controlIds: ['AC.L1-3.1.1'],
      frameworkCodes: ['CMMC', 'NIST-800-171'],
    },
    exportTargets: ['evidence_graph', 'verifier_room'],
    createdAt: '2026-06-30T00:00:00.000Z',
  });

  assert.equal(transaction.version, 'v1');
  assert.equal(transaction.transactionHash, hashTrustTransaction(transaction));
  assert.deepEqual(verifyTrustTransaction(transaction), {
    ok: true,
    transactionId: transaction.transactionId,
    errors: [],
  });
});

test('rejects unsupported Copilot answers and redacts shareable transactions', () => {
  const unsupported = createTrustTransaction({
    kind: 'copilot_answer',
    status: 'blocked',
    actor: { id: 'agent:grc-copilot', type: 'agent', did: 'did:grc:copilot' },
    action: { name: 'answer_compliance_question', idempotencyKey: 'question-001' },
    dataBoundary: 'tenant-confidential',
    createdAt: '2026-06-30T00:00:00.000Z',
  });

  assert.deepEqual(verifyTrustTransaction(unsupported).errors, ['copilot_answer_missing_proof']);

  const redacted = redactTrustTransactionForSharing(unsupported);
  assert.equal(redacted.tenantId, undefined);
  assert.match(redacted.actor.id, /^redacted:/);
  assert.match(redacted.actor.did ?? '', /^redacted:/);
  assert.match(redacted.action.idempotencyKey ?? '', /^redacted:/);
});
