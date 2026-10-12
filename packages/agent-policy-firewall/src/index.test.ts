import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  AgentPolicyFirewall,
  formatFirewallReceiptForEvidenceGraph,
  verifyFirewallReceipt,
  type ApprovalThreshold,
  type FirewallContext,
  type FirewallDecision,
  type FirewallReceipt,
} from './index.js';

const actor = { id: 'outcome-test-agent', type: 'agent' as const, tenantId: 7 };

function context(approvalThreshold: ApprovalThreshold): FirewallContext {
  return {
    tenantScope: ['demo-tenant'],
    role: 'operator',
    allowedTools: ['inventory.read', 'inventory.retire'],
    deniedTools: ['customer.export'],
    sandboxPolicy: 'none',
    approvalThreshold,
    dataBoundary: 'tenant-confidential',
    replayWindowSeconds: 300,
    maxBlastRadius: 10,
  };
}

describe('AgentPolicyFirewall outcome', () => {
  it('returns allowed for a permitted action that needs no approval', () => {
    const decision = new AgentPolicyFirewall().evaluate(
      actor,
      { toolName: 'inventory.read', tier: 'read', args: { assetId: 'a' } },
      context('human'),
    );
    assert.equal(decision.outcome, 'allowed');
    assert.equal(decision.allowed, true);
    assert.equal(decision.requiresApproval, false);
  });

  it('returns a fail-closed needs_approval for a destructive action under a human approval threshold', () => {
    const decision = new AgentPolicyFirewall().evaluate(
      actor,
      { toolName: 'inventory.retire', tier: 'destructive', args: { assetId: 'a' } },
      context('human'),
    );
    assert.equal(decision.outcome, 'needs_approval');
    assert.equal(decision.allowed, false);
    assert.equal(decision.requiresApproval, true);
    assert.equal(decision.reason, 'requires_human_approval');
  });

  it('returns allowed for the same destructive action when no approval threshold applies', () => {
    const decision = new AgentPolicyFirewall().evaluate(
      actor,
      { toolName: 'inventory.retire', tier: 'destructive', args: { assetId: 'a' } },
      context('none'),
    );
    assert.equal(decision.outcome, 'allowed');
    assert.equal(decision.requiresApproval, false);
  });

  it('returns denied for an explicitly denied tool', () => {
    const decision = new AgentPolicyFirewall().evaluate(
      actor,
      { toolName: 'customer.export', tier: 'read', args: { dataset: 'd' } },
      context('human'),
    );
    assert.equal(decision.outcome, 'denied');
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'tool_explicitly_denied');
  });
});

describe('AgentPolicyFirewall receipt integrity', () => {
  function pendingReceipt(): FirewallReceipt {
    const firewall = new AgentPolicyFirewall();
    const request = { toolName: 'inventory.retire', tier: 'destructive' as const, args: { assetId: 'a' } };
    const decision = firewall.evaluate(actor, request, context('human'));
    return firewall.createReceipt(actor, request, context('human'), decision);
  }

  function withDecision(receipt: FirewallReceipt, change: Partial<FirewallDecision>): FirewallReceipt {
    return { ...receipt, decision: { ...receipt.decision, ...change } };
  }

  it('verifies an unmodified receipt', () => {
    assert.equal(verifyFirewallReceipt(pendingReceipt()), true);
  });

  it('fails verification when needs_approval is changed to allowed', () => {
    const receipt = pendingReceipt();
    assert.equal(receipt.decision.outcome, 'needs_approval');
    assert.equal(verifyFirewallReceipt(withDecision(receipt, { outcome: 'allowed' })), false);
    assert.equal(verifyFirewallReceipt(withDecision(receipt, { outcome: 'allowed', allowed: true })), false);
  });

  it('fails verification when any other bound decision field changes', () => {
    const receipt = pendingReceipt();
    const changes: Partial<FirewallDecision>[] = [
      { allowed: true },
      { reason: 'approved_by_firewall' },
      { requiresApproval: false },
      { approvalThreshold: 'none' },
      { sandbox: 'none' },
      { blastRadiusScore: 0 },
    ];
    for (const change of changes) {
      assert.equal(verifyFirewallReceipt(withDecision(receipt, change)), false, `unbound field: ${Object.keys(change)[0]}`);
    }
  });

  it('labels a pending decision as NEEDS_APPROVAL in the evidence graph', () => {
    const node = formatFirewallReceiptForEvidenceGraph(pendingReceipt());
    assert.equal(node.label, 'Firewall: inventory.retire → NEEDS_APPROVAL');
    const payload = node.payload as Record<string, unknown>;
    assert.equal(payload.outcome, 'needs_approval');
    assert.equal(payload.requires_approval, true);
  });
});
