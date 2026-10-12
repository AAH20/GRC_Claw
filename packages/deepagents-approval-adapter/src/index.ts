export interface FirewallActor {
  id: string;
  type: 'human' | 'agent' | 'service' | 'mcp_tool' | 'browser_agent' | 'cloud_connector' | 'soar_playbook' | 'remediation_bot' | 'marketplace_pack';
  role?: string;
  tenantId?: number;
}

export interface FirewallToolRequest {
  toolName: string;
  tier: 'read' | 'write' | 'destructive' | 'provision' | 'decommission';
  args: Record<string, unknown>;
  idempotencyKey?: string;
}

export interface FirewallContext {
  tenantScope: string[];
  role: string;
  allowedTools: string[];
  deniedTools: string[];
  sandboxPolicy: 'none' | 'docker' | 'microvm' | 'enclave' | 'denied';
  approvalThreshold: 'none' | 'human' | 'dual_control' | 'board' | 'government_buyer';
  dataBoundary: 'public' | 'tenant-confidential' | 'cui' | 'phi' | 'pci' | 'gdpr' | 'sovereign' | 'airgapped';
  replayWindowSeconds: number;
  maxBlastRadius: number;
  controlImpactIds?: string[];
}

export type FirewallOutcome = 'allowed' | 'denied' | 'needs_approval';

export interface FirewallDecision {
  allowed: boolean;
  outcome: FirewallOutcome;
  reason: string;
  sandbox: 'none' | 'docker' | 'microvm' | 'enclave' | 'denied';
  requiresApproval: boolean;
  approvalThreshold: 'none' | 'human' | 'dual_control' | 'board' | 'government_buyer';
  blastRadiusScore: number;
  controlImpact: string[];
  replayDetected: boolean;
  canaryTriggered: boolean;
  sodViolation: boolean;
  toxicityScore?: number;
  anomaliesDetected: string[];
  receiptHash: string;
}

export interface FirewallReceipt {
  receiptId: string;
  request: FirewallToolRequest;
  decision: FirewallDecision;
  receiptHash: string;
}

/** Structural port keeps this adapter independent of a specific firewall package version. */
export interface FirewallPort {
  evaluate(actor: FirewallActor, request: FirewallToolRequest, context: FirewallContext): FirewallDecision;
  createReceipt(actor: FirewallActor, request: FirewallToolRequest, context: FirewallContext, decision: FirewallDecision): FirewallReceipt;
}

/** The only states a DeepAgents tool boundary may observe. */
export type DeepAgentsExecutionState = 'execute' | 'interrupt' | 'deny';

export interface DeepAgentsApprovalResult {
  state: DeepAgentsExecutionState;
  /** DeepAgents can use this value as the interrupt_on predicate result. */
  interruptOn: boolean;
  decision: FirewallDecision;
  receipt: FirewallReceipt;
}

export interface DeepAgentsApprovalRequest {
  actor: FirewallActor;
  request: FirewallToolRequest;
  context: FirewallContext;
}

/**
 * Converts a GRC_Claw firewall decision into an explicit DeepAgents boundary.
 *
 * The adapter deliberately checks `outcome`, not only `allowed`. This keeps
 * pending approvals from reaching a tool implementation when a caller uses
 * the legacy boolean field.
 */
export function toDeepAgentsApprovalResult(
  firewall: FirewallPort,
  input: DeepAgentsApprovalRequest,
): DeepAgentsApprovalResult {
  const decision = firewall.evaluate(input.actor, input.request, input.context);
  const receipt = firewall.createReceipt(input.actor, input.request, input.context, decision);

  if (decision.outcome === 'allowed') {
    return { state: 'execute', interruptOn: false, decision, receipt };
  }
  if (decision.outcome === 'needs_approval') {
    return { state: 'interrupt', interruptOn: true, decision, receipt };
  }
  return { state: 'deny', interruptOn: false, decision, receipt };
}

/**
 * A small predicate suitable for a DeepAgents interrupt_on integration.
 * The full result is retained so the caller can persist the receipt before
 * deciding whether to resume the graph.
 */
export function createDeepAgentsApprovalPredicate(
  firewall: FirewallPort,
  base: Omit<DeepAgentsApprovalRequest, 'request'>,
): (request: FirewallToolRequest) => DeepAgentsApprovalResult {
  return (request) => toDeepAgentsApprovalResult(firewall, { ...base, request });
}

export function assertExecutable(result: DeepAgentsApprovalResult): void {
  if (result.state !== 'execute' || result.decision.outcome !== 'allowed') {
    throw new Error(`tool execution blocked: ${result.decision.outcome}:${result.decision.reason}`);
  }
}
