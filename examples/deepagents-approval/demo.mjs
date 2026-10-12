import firewallModule from '../../packages/agent-policy-firewall/src/index.ts';
import { toDeepAgentsApprovalResult } from '../../packages/deepagents-approval-adapter/src/index.ts';

const { AgentPolicyFirewall } = firewallModule;

const actor = { id: 'demo-agent', type: 'agent', role: 'developer', tenantId: 7 };
const context = {
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

const cases = [
  ['inventory.read', 'read'],
  ['control.update', 'destructive'],
  ['customer.export', 'read'],
];

for (const [toolName, tier] of cases) {
  const result = toDeepAgentsApprovalResult(new AgentPolicyFirewall(), {
    actor,
    context,
    request: { toolName, tier, args: { synthetic: true } },
  });
  console.log(JSON.stringify({
    action: toolName,
    outcome: result.decision.outcome,
    state: result.state,
    interruptOn: result.interruptOn,
    receiptHash: result.receipt.receiptHash,
  }));
}
