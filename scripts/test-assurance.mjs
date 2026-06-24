/** Gateway assurance graph contract test. */
import assert from 'node:assert/strict';
import { ActionLedger } from '../packages/evidence/dist/index.js';
import { GatewayAssuranceGraph } from '../packages/gateway/dist/assurance.js';

function intent() {
  return new ActionLedger().recordIntent({
    tenantId: 7,
    sessionId: 'assurance-session',
    tool: 'evidence.attach',
    args: { controlId: 'AC.1', uri: 'test://evidence' },
    idempotencyKey: `assurance-${crypto.randomUUID()}`,
  });
}

const originalThreshold = process.env.GRC_CLAW_ASSURANCE_MAX_RISK;
try {
  delete process.env.GRC_CLAW_ASSURANCE_MAX_RISK;
  const observed = new GatewayAssuranceGraph().observeIntent(intent(), {
    agentId: 'qa-agent',
    tenantId: 7,
    sessionId: 'assurance-session',
    tool: 'evidence.attach',
    args: { controlId: 'AC.1' },
    toolTier: 'write',
  });
  assert.match(observed.agentDid, /^did:grc:/);
  assert.equal(observed.identityStatus, 'provisional');
  assert.equal(observed.gate.allowed, true);
  assert.equal(observed.blastRadius?.controlId, 'AC.1');

  process.env.GRC_CLAW_ASSURANCE_MAX_RISK = '0';
  const blocked = new GatewayAssuranceGraph().observeIntent(intent(), {
    tenantId: 7,
    sessionId: 'blocked-session',
    tool: 'evidence.attach',
    args: { controlId: 'AC.2' },
    toolTier: 'write',
  });
  assert.equal(blocked.gate.allowed, false);
  assert.equal(blocked.gate.reason, 'assurance_risk_threshold_exceeded');
  console.log('assurance graph: 6 passed, 0 failed');
} finally {
  if (originalThreshold === undefined) delete process.env.GRC_CLAW_ASSURANCE_MAX_RISK;
  else process.env.GRC_CLAW_ASSURANCE_MAX_RISK = originalThreshold;
}
