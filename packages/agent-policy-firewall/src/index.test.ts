import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { AgentPolicyFirewall, type ApprovalThreshold, type FirewallContext } from './index.js';

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

  it('returns needs_approval for a destructive action under a human approval threshold', () => {
    const decision = new AgentPolicyFirewall().evaluate(
      actor,
      { toolName: 'inventory.retire', tier: 'destructive', args: { assetId: 'a' } },
      context('human'),
    );
    assert.equal(decision.outcome, 'needs_approval');
    assert.equal(decision.requiresApproval, true);
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
