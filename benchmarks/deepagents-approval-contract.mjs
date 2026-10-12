import { performance } from 'node:perf_hooks';
import firewallModule from '../packages/agent-policy-firewall/src/index.ts';
import { toDeepAgentsApprovalResult } from '../packages/deepagents-approval-adapter/src/index.ts';

const { AgentPolicyFirewall } = firewallModule;
const actor = { id: 'benchmark-agent', type: 'agent', role: 'developer', tenantId: 7 };
const context = {
  tenantScope: ['benchmark-tenant'],
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

const scenarios = [
  { toolName: 'inventory.read', tier: 'read', expected: 'allowed' },
  { toolName: 'control.update', tier: 'destructive', expected: 'needs_approval' },
  { toolName: 'customer.export', tier: 'read', expected: 'denied' },
];
const iterations = 1_000;
const counts = { allowed: 0, needs_approval: 0, denied: 0 };
const started = performance.now();

for (let i = 0; i < iterations; i += 1) {
  const scenario = scenarios[i % scenarios.length];
  const result = toDeepAgentsApprovalResult(new AgentPolicyFirewall(), {
    actor,
    context,
    request: { toolName: scenario.toolName, tier: scenario.tier, args: { iteration: i } },
  });
  counts[result.decision.outcome] += 1;
  if (result.decision.outcome !== scenario.expected) throw new Error(`unexpected outcome for ${scenario.toolName}`);
}

const elapsedMs = performance.now() - started;
console.log(JSON.stringify({
  benchmark: 'deepagents-approval-contract',
  iterations,
  outcomes: counts,
  elapsedMs: Number(elapsedMs.toFixed(2)),
  decisionsPerSecond: Math.round(iterations / (elapsedMs / 1000)),
  receipt: 'generated for every decision',
}, null, 2));
