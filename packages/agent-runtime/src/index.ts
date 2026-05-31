export type ToolTier = 'read' | 'write' | 'destructive';

export interface ToolDefinition {
  name: string;
  tier: ToolTier;
  allowedPrefixes?: string[];
}

export interface ExecPolicyConfig {
  maxCallsPerTurn: number;
  callTimeoutMs: number;
  defaultSandbox: 'docker' | 'host';
}

export interface ToolInvocation {
  tool: string;
  args: Record<string, unknown>;
  approvalToken?: string;
  idempotencyKey?: string;
}

export interface ExecDecision {
  allowed: boolean;
  reason: string;
  sandbox: 'docker' | 'host' | 'denied';
  requiresApproval: boolean;
}

export const BUILTIN_AGENT_TOOLS: ToolDefinition[] = [
  { name: 'grc.list_controls', tier: 'read' },
  { name: 'grc.get_compliance_score', tier: 'read' },
  { name: 'evidence.read', tier: 'read' },
  { name: 'soc.query_events', tier: 'read', allowedPrefixes: ['GET'] },
  { name: 'evidence.attach', tier: 'write' },
  { name: 'control.update_status', tier: 'write' },
  { name: 'soar.run_playbook', tier: 'destructive' },
  { name: 'firewall.apply_rule', tier: 'destructive' },
  { name: 'sentinel.get_incident', tier: 'read' },
  { name: 'sentinel.run_playbook', tier: 'destructive' },
  { name: 'aws.guardduty.list_findings', tier: 'read' },
  { name: 'chronicle.soar.run_playbook', tier: 'destructive' },
];

/** Three-phase exec policy: allowlist → approval → sandbox */
export class ExecPolicy {
  readonly config: ExecPolicyConfig;

  constructor(
    private readonly tools: ToolDefinition[] = BUILTIN_AGENT_TOOLS,
    config: Partial<ExecPolicyConfig> = {}
  ) {
    this.config = {
      maxCallsPerTurn: 12,
      callTimeoutMs: 30_000,
      defaultSandbox: 'docker',
      ...config,
    };
  }

  evaluate(inv: ToolInvocation, approvedDestructive = false): ExecDecision {
    const def = this.tools.find((t) => t.name === inv.tool);
    if (!def) {
      return { allowed: false, reason: 'tool_not_in_allowlist', sandbox: 'denied', requiresApproval: false };
    }

    if (def.tier === 'destructive') {
      if (!inv.approvalToken && !approvedDestructive) {
        return {
          allowed: false,
          reason: 'destructive_requires_approval',
          sandbox: 'denied',
          requiresApproval: true,
        };
      }
      return {
        allowed: true,
        reason: 'destructive_approved',
        sandbox: this.config.defaultSandbox,
        requiresApproval: true,
      };
    }

    if (def.tier === 'write' && !inv.idempotencyKey) {
      return {
        allowed: false,
        reason: 'write_requires_idempotency_key',
        sandbox: 'denied',
        requiresApproval: false,
      };
    }

    return {
      allowed: true,
      reason: def.tier === 'read' ? 'read_allowed' : 'write_allowed',
      sandbox: def.tier === 'read' ? 'docker' : this.config.defaultSandbox,
      requiresApproval: false,
    };
  }
}

export interface AgentAuditEntry {
  at: string;
  sessionId: string;
  tool: string;
  decision: ExecDecision;
  argsRedacted: Record<string, unknown>;
}

export class AgentSession {
  private calls = 0;
  private readonly audit: AgentAuditEntry[] = [];

  constructor(
    public readonly sessionId: string,
    private readonly policy: ExecPolicy
  ) {}

  async invoke(inv: ToolInvocation): Promise<ExecDecision> {
    if (this.calls >= this.policy.config.maxCallsPerTurn) {
      const decision: ExecDecision = {
        allowed: false,
        reason: 'max_calls_exceeded',
        sandbox: 'denied',
        requiresApproval: false,
      };
      this.audit.push({
        at: new Date().toISOString(),
        sessionId: this.sessionId,
        tool: inv.tool,
        decision,
        argsRedacted: { keys: Object.keys(inv.args) },
      });
      return decision;
    }
    this.calls++;
    const decision = this.policy.evaluate(inv);
    this.audit.push({
      at: new Date().toISOString(),
      sessionId: this.sessionId,
      tool: inv.tool,
      decision,
      argsRedacted: { keys: Object.keys(inv.args) },
    });
    return decision;
  }

  getAuditLog(): AgentAuditEntry[] {
    return [...this.audit];
  }
}
