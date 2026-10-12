import assert from 'node:assert/strict';
import test from 'node:test';
import {
  assertExecutable,
  createDeepAgentsApprovalPredicate,
  toDeepAgentsApprovalResult,
  type FirewallActor,
  type FirewallContext,
  type FirewallDecision,
  type FirewallPort,
  type FirewallReceipt,
  type FirewallToolRequest,
} from './index.js';

class FixtureFirewall implements FirewallPort {
  evaluate(_actor: FirewallActor, request: FirewallToolRequest, _context: FirewallContext): FirewallDecision {
    const denied = request.toolName === 'customer.export';
    const pending = request.toolName === 'control.update';
    const outcome = denied ? 'denied' : pending ? 'needs_approval' : 'allowed';
    return {
      allowed: outcome !== 'denied',
      outcome,
      reason: denied ? 'tool_explicitly_denied' : pending ? 'requires_human_approval' : 'approved_by_firewall',
      sandbox: pending ? 'docker' : 'none',
      requiresApproval: pending,
      approvalThreshold: pending ? 'human' : 'none',
      blastRadiusScore: pending ? 5 : 0,
      controlImpact: ['SOC2-CC6.1'],
      replayDetected: false,
      canaryTriggered: false,
      sodViolation: false,
      anomaliesDetected: [],
      receiptHash: `decision:${outcome}`,
    };
  }

  createReceipt(_actor: FirewallActor, request: FirewallToolRequest, _context: FirewallContext, decision: FirewallDecision): FirewallReceipt {
    return {
      receiptId: `fixture:${request.toolName}`,
      request,
      decision,
      receiptHash: `receipt:${decision.outcome}`,
    };
  }
}

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
  const result = toDeepAgentsApprovalResult(new FixtureFirewall(), {
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
  const result = toDeepAgentsApprovalResult(new FixtureFirewall(), {
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
  const result = toDeepAgentsApprovalResult(new FixtureFirewall(), {
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
  const predicate = createDeepAgentsApprovalPredicate(new FixtureFirewall(), { actor, context });
  const result = predicate(request('control.update', 'destructive'));
  assert.equal(result.state, 'interrupt');
  assert.equal(result.receipt.request.toolName, 'control.update');
  assert.equal(result.receipt.decision.outcome, 'needs_approval');
  assert.equal(result.receipt.decision.receiptHash, result.decision.receiptHash);
});
