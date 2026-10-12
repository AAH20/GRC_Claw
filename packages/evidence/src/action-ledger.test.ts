import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { ActionLedger, type ActionDecisionOutcome } from './action-ledger.js';

function recordDecision(input: { allowed: boolean; reason: string; requiresApproval: boolean; outcome?: ActionDecisionOutcome }) {
  const ledger = new ActionLedger();
  const intent = ledger.recordIntent({
    tenantId: 7,
    sessionId: 'ledger-decision-test',
    tool: 'inventory.retire',
    args: { assetId: 'fictional-asset' },
    idempotencyKey: 'ledger-decision-test-1',
  });
  return { ledger, decision: ledger.recordDecision(intent, input) };
}

describe('ActionLedger.recordDecision with an explicit outcome (firewall path)', () => {
  it('records needs_approval as approval_required', () => {
    // AgentPolicyFirewall shape for an action that passed policy but awaits approval.
    const { decision } = recordDecision({
      allowed: true,
      reason: 'approved_by_firewall',
      requiresApproval: true,
      outcome: 'needs_approval',
    });
    assert.equal(decision.executionState, 'approval_required');
    assert.equal(decision.requiresApproval, true);
  });

  it('records allowed as executing', () => {
    const { decision } = recordDecision({ allowed: true, reason: 'approved_by_firewall', requiresApproval: false, outcome: 'allowed' });
    assert.equal(decision.executionState, 'executing');
  });

  it('records denied as denied', () => {
    const { decision } = recordDecision({ allowed: false, reason: 'tool_explicitly_denied', requiresApproval: false, outcome: 'denied' });
    assert.equal(decision.executionState, 'denied');
  });
});

describe('ActionLedger.recordDecision without an outcome (gateway / agent-runtime path)', () => {
  // Inputs mirror the ExecPolicy.evaluate decisions that the gateway passes to the ledger.
  it('records a destructive action without an approval token as approval_required', () => {
    const { decision } = recordDecision({ allowed: false, reason: 'destructive_requires_approval', requiresApproval: true });
    assert.equal(decision.executionState, 'approval_required');
  });

  it('keeps an approved destructive action as executing', () => {
    const { decision } = recordDecision({ allowed: true, reason: 'destructive_approved', requiresApproval: true });
    assert.equal(decision.executionState, 'executing');
  });

  it('records an allowed action as executing', () => {
    const { decision } = recordDecision({ allowed: true, reason: 'read_allowed', requiresApproval: false });
    assert.equal(decision.executionState, 'executing');
  });

  it('records a denied action as denied', () => {
    const { decision } = recordDecision({ allowed: false, reason: 'tool_not_in_allowlist', requiresApproval: false });
    assert.equal(decision.executionState, 'denied');
  });
});

describe('ActionLedger hash chain', () => {
  it('verifies after decisions from both paths', () => {
    const ledger = new ActionLedger();
    const firewallIntent = ledger.recordIntent({ tenantId: 7, sessionId: 's', tool: 'inventory.retire', args: { assetId: 'a' } });
    ledger.recordDecision(firewallIntent, {
      allowed: true,
      reason: 'approved_by_firewall',
      requiresApproval: true,
      outcome: 'needs_approval',
    });
    const gatewayIntent = ledger.recordIntent({ tenantId: 7, sessionId: 's', tool: 'host.isolate', args: { hostId: 'h' } });
    ledger.recordDecision(gatewayIntent, { allowed: false, reason: 'destructive_requires_approval', requiresApproval: true });

    assert.deepEqual(ledger.verify(), { ok: true, checked: 4 });
    assert.deepEqual(
      ledger.list().reverse().map((event) => event.executionState),
      ['intent_recorded', 'approval_required', 'intent_recorded', 'approval_required'],
    );
  });
});
