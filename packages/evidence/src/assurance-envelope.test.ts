import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  ActionLedger,
  createAssuranceEnvelope,
  hashAssuranceEnvelope,
  redactAssuranceEnvelopeForSharing,
  verifyAssuranceEnvelope,
} from './index.js';

describe('assurance envelopes', () => {
  it('creates deterministic, auditor-safe receipts without raw invocation payloads', () => {
    const ledger = new ActionLedger();
    const intent = ledger.recordIntent({
      tenantId: 42,
      sessionId: 'agentic-assurance-test',
      tool: 'evidence.attach',
      args: { controlId: 'CMMC-AC.L1-3.1.1', secret: 'do-not-leak' },
      idempotencyKey: 'receipt-test-key',
    });
    const decision = ledger.recordDecision(intent, {
      allowed: true,
      reason: 'within_policy',
      requiresApproval: false,
    });
    const result = ledger.recordResult(intent, {
      executionState: 'recorded',
      evidenceId: 'ev-test',
      output: { token: 'also-do-not-leak' },
    });

    const envelope = createAssuranceEnvelope({
      intent,
      decision,
      result,
      identity: { agentDid: 'did:grc:test-agent', status: 'verified' },
      assurance: { riskScore: 4, blastRadiusImpact: 2, controlId: 'CMMC-AC.L1-3.1.1' },
    });

    const serialized = JSON.stringify(envelope);
    assert.equal(serialized.includes('do-not-leak'), false);
    assert.equal(serialized.includes('also-do-not-leak'), false);
    assert.equal(envelope.intent.argKeys?.includes('secret'), true);

    const verification = verifyAssuranceEnvelope(envelope);
    assert.equal(verification.ok, true);
    assert.equal(verification.errors.length, 0);
    assert.equal(verification.envelopeHash, hashAssuranceEnvelope(envelope));

    const shared = redactAssuranceEnvelopeForSharing(envelope);
    assert.match(shared.idempotencyKey ?? '', /^redacted:/);
    assert.equal(hashAssuranceEnvelope(envelope), hashAssuranceEnvelope(envelope));
  });

  it('flags structurally incomplete receipts', () => {
    const incomplete = {
      version: 'v1',
      actionId: '',
      tenantId: Number.NaN,
      sessionId: '',
      tool: '',
      createdAt: '',
      updatedAt: '',
      intent: { ledgerHash: '' },
    } as any;

    const verification = verifyAssuranceEnvelope(incomplete);
    assert.equal(verification.ok, false);
    assert.ok(verification.errors.includes('missing_action_id'));
    assert.ok(verification.errors.includes('missing_intent_ledger_hash'));
  });
});
