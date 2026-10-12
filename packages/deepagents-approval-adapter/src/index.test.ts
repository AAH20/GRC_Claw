import assert from 'node:assert/strict';
import test from 'node:test';
import firewallModule from '../../agent-policy-firewall/src/index.ts';
import type { FirewallActor, FirewallContext, FirewallToolRequest } from '../../agent-policy-firewall/src/index.ts';
import { assertExecutable, createDeepAgentsApprovalPredicate, toDeepAgentsApprovalResult } from './index.ts';

const { AgentPolicyFirewall } = firewallModule;

const actor: FirewallActor = { id: 'deepagents-demo', type: 'agent', role: 'developer', tenantId: 7 };
const context: FirewallContext = {
  tenantScope: ['demo-tenant'],
  role: 'developer',
  allowedTools: ['inventory.read', 'control.update', 'customer.export'],
  deniedTools: ['customer.export'],
  sandboxPolicy: 'none',
  approvalThreshold: 'human',
  dataBoundary: 'tenant-confidential',
  replayWindowSeconds: 300,
  maxBlastRadius: 10,
  controlImpactIds: ['SOC2-CC6.1'],
};

function request(toolName: string, tier: FirewallToolRequest['tier']): FirewallToolRequest {
  return { toolName, tier, args: { synthetic: true } };
}

test('allowed decisions execute without an interrupt', () => {
  const result = toDeepAgentsApprovalResult(new AgentPolicyFirewall(), {
    actor,
    context,
    request: request('inventory.read', 'read'),
  });
  assert.equal(result.state, 'execute');
  assert.equal(result.interruptOn, false);
  assert.equal(result.decision.outcome, 'allowed');
  assert.doesNotThrow(() => assertExecutable(result));
});

test('needs_approval becomes a resumable DeepAgents interrupt', () => {
  const result = toDeepAgentsApprovalResult(new AgentPolicyFirewall(), {
    actor,
    context,
    request: request('control.update', 'destructive'),
  });
  assert.equal(result.state, 'interrupt');
  assert.equal(result.interruptOn, true);
  assert.equal(result.decision.outcome, 'needs_approval');
  assert.equal(result.decision.requiresApproval, true);
  assert.throws(() => assertExecutable(result), /tool execution blocked/);
});

test('denied decisions fail closed even when a caller checks allowed', () => {
  const result = toDeepAgentsApprovalResult(new AgentPolicyFirewall(), {
    actor,
    context,
    request: request('customer.export', 'read'),
  });
  assert.equal(result.state, 'deny');
  assert.equal(result.interruptOn, false);
  assert.equal(result.decision.allowed, false);
  assert.equal(result.decision.outcome, 'denied');
  assert.throws(() => assertExecutable(result), /tool execution blocked/);
});

test('predicate preserves a receipt for the interrupt boundary', () => {
  const predicate = createDeepAgentsApprovalPredicate(new AgentPolicyFirewall(), { actor, context });
  const result = predicate(request('control.update', 'destructive'));
  assert.equal(result.state, 'interrupt');
  assert.equal(result.receipt.request.toolName, 'control.update');
  assert.equal(result.receipt.decision.outcome, 'needs_approval');
  assert.equal(result.receipt.decision.receiptHash, result.decision.receiptHash);
});
