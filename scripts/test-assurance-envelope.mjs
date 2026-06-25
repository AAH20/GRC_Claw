/**
 * @domain assurance
 * @layer verification
 * @summary Proves envelope receipts retain hashes and never raw invocation payloads.
 * @see docs/AGENTIC_AI_SECURITY.md
 */
import assert from 'node:assert/strict';
import { ActionLedger, createAssuranceEnvelope } from '../packages/evidence/dist/index.js';

const ledger = new ActionLedger();
const intent = ledger.recordIntent({
  tenantId: 7,
  sessionId: 'envelope-session',
  tool: 'evidence.attach',
  args: { controlId: 'AC.1', secret: 'never-persist-this' },
  idempotencyKey: 'envelope-test-1',
});
const decision = ledger.recordDecision(intent, { allowed: true, reason: 'write_allowed', requiresApproval: false });
const result = ledger.recordResult(intent, {
  executionState: 'recorded',
  output: { secret: 'never-persist-this-either' },
  evidenceId: 'ev-test',
});
const envelope = createAssuranceEnvelope({
  intent,
  decision,
  result,
  identity: { agentDid: 'did:grc:test', status: 'provisional' },
  assurance: { riskScore: 6, controlId: 'AC.1' },
});

assert.equal(envelope.actionId, intent.actionId);
assert.equal(envelope.policy?.allowed, true);
assert.equal(envelope.result?.executionState, 'recorded');
assert.equal(envelope.intent.argsHash, intent.argsHash);
assert.equal(JSON.stringify(envelope).includes('never-persist-this'), false);
assert.equal(JSON.stringify(envelope).includes('never-persist-this-either'), false);
console.log('assurance envelope: 6 passed, 0 failed');
