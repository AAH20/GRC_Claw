import assert from 'node:assert/strict';
import test from 'node:test';

import { AgentPolicyFirewall } from '../../packages/agent-policy-firewall/src/index.ts';
import { AgentSession, ExecPolicy } from '../../packages/agent-runtime/src/index.ts';
import { ActionLedger } from '../../packages/evidence/src/action-ledger.ts';
import { createClawDispatchContext } from '../../packages/gateway/src/skill-runtime.ts';

// Exercises the gateway skill runtime, which gates dispatch on `decision.allowed`
// and records intent, decision and result events in the action ledger.

const tool = 'mcp.inventory.retire';
const actor = { id: 'approval-gate-agent', type: 'agent', tenantId: 7 };

function firewallContext(approvalThreshold) {
  return {
    tenantScope: ['demo-tenant'],
    role: 'operator',
    allowedTools: [tool],
    deniedTools: [],
    sandboxPolicy: 'none',
    approvalThreshold,
    dataBoundary: 'tenant-confidential',
    replayWindowSeconds: 300,
    maxBlastRadius: 10,
  };
}

/** Session adapter that asks AgentPolicyFirewall for the decision. */
function firewallSession(approvalThreshold) {
  const firewall = new AgentPolicyFirewall();
  return {
    invoke: async (inv) =>
      firewall.evaluate(actor, { toolName: inv.tool, tier: 'destructive', args: inv.args }, firewallContext(approvalThreshold)),
  };
}

/** Dependencies that record any use; dispatching the tool would touch the registry first. */
function recordingDeps(touched) {
  const recorder = (name) =>
    new Proxy({}, {
      get(_target, property) {
        touched.push(`${name}.${String(property)}`);
        return () => {
          throw new Error(`dispatched via ${name}.${String(property)}`);
        };
      },
    });
  return { registry: recorder('registry'), evidence: recorder('evidence'), a2z: recorder('a2z') };
}

function runtime(makeSession) {
  const touched = [];
  const ledger = new ActionLedger();
  const policy = new ExecPolicy([{ name: tool, tier: 'destructive' }]);
  const ctx = createClawDispatchContext({
    ...recordingDeps(touched),
    ledger,
    defaultLlmProviderId: 'none',
    makeSession,
    getPolicy: () => policy,
  });
  const events = () => ledger.list().reverse().map((event) => [event.kind, event.executionState]);
  return { ctx, ledger, touched, events };
}

test('firewall needs_approval decision is not dispatched and records no result', async () => {
  const { ctx, ledger, touched, events } = runtime(() => firewallSession('human'));

  const outcome = await ctx.invokeTool(tool, { tenantId: 7, assetId: 'fictional-asset' });

  assert.deepEqual(outcome, { output: {}, blocked: true, reason: 'requires_human_approval' });
  assert.deepEqual(touched, [], 'tool dispatch was attempted');
  assert.deepEqual(events(), [['intent', 'intent_recorded'], ['decision', 'approval_required']]);
  assert.equal(ledger.verify().ok, true);
});

test('pending approval from a real AgentSession is not dispatched and records no result', async () => {
  const { ctx, touched, events } = runtime((sessionId, policy) => new AgentSession(sessionId, policy));

  const outcome = await ctx.invokeTool(tool, { tenantId: 7, assetId: 'fictional-asset' });

  assert.equal(outcome.blocked, true);
  assert.equal(outcome.reason, 'destructive_requires_approval');
  assert.deepEqual(touched, [], 'tool dispatch was attempted');
  assert.deepEqual(events(), [['intent', 'intent_recorded'], ['decision', 'approval_required']]);
});

test('control: a firewall allowed decision reaches tool dispatch', async () => {
  const { ctx, touched } = runtime(() => firewallSession('none'));

  await assert.rejects(ctx.invokeTool(tool, { tenantId: 7, assetId: 'fictional-asset' }), /dispatched via registry/);
  assert.ok(touched.length > 0, 'expected the allowed action to reach dispatch');
});
