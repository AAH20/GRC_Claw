import { createHash } from 'node:crypto';

export type FirewallActionTier = 'read' | 'write' | 'destructive' | 'provision' | 'decommission';

export type SandboxPolicy = 'none' | 'docker' | 'microvm' | 'enclave' | 'denied';

export type ApprovalThreshold = 'none' | 'human' | 'dual_control' | 'board' | 'government_buyer';

export type DataBoundary = 'public' | 'tenant-confidential' | 'cui' | 'phi' | 'pci' | 'gdpr' | 'sovereign' | 'airgapped';

export interface FirewallActor {
  id: string;
  type: 'human' | 'agent' | 'service' | 'mcp_tool' | 'browser_agent' | 'cloud_connector' | 'soar_playbook' | 'remediation_bot' | 'marketplace_pack';
  tenantId?: number;
  orgSlug?: string;
  role?: string;
  did?: string;
  trustScore?: number;
}

export interface FirewallToolRequest {
  toolName: string;
  tier: FirewallActionTier;
  args: Record<string, unknown>;
  idempotencyKey?: string;
  correlationId?: string;
  model?: string;
  llmProviderId?: string;
  thought?: string;
}

export interface FirewallContext {
  tenantScope: string[];
  role: string;
  allowedTools: string[];
  deniedTools: string[];
  sandboxPolicy: SandboxPolicy;
  approvalThreshold: ApprovalThreshold;
  dataBoundary: DataBoundary;
  replayWindowSeconds: number;
  maxBlastRadius: number;
  controlImpactIds?: string[];
}

export interface FirewallDecision {
  allowed: boolean;
  reason: string;
  sandbox: SandboxPolicy;
  requiresApproval: boolean;
  approvalThreshold: ApprovalThreshold;
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
  version: 'v1';
  receiptId: string;
  timestamp: string;
  actor: FirewallActor;
  request: FirewallToolRequest;
  context: FirewallContext;
  decision: FirewallDecision;
  receiptHash: string;
}

export interface CanaryTrap {
  toolName: string;
  triggerCount: number;
  lastTriggered?: string;
  sourceIp?: string;
  actorId?: string;
}

export interface SoDRule {
  conflictRoleA: string;
  conflictRoleB: string;
  ruleName: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface ReplayEntry {
  idempotencyKey: string;
  firstSeen: string;
  lastSeen: string;
  count: number;
  actorId: string;
}

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, v]) => v !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => [k, stable(v)]),
    );
  }
  return value;
}

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

function generateReceiptId(): string {
  return `fw_receipt:${sha256({ ts: Date.now(), rand: Math.random().toString(36).slice(2) }).slice(0, 16)}`;
}

export class AgentPolicyFirewall {
  private canaryTraps: Map<string, CanaryTrap> = new Map();
  private sodRules: SoDRule[];
  private replayWindow: Map<string, ReplayEntry> = new Map();
  private blockedActors: Set<string> = new Set();
  private config: {
    maxBlastRadius: number;
    replayWindowSeconds: number;
    toxicityDenyThreshold: number;
    toxicitySandboxThreshold: number;
    canaryToolNames: string[];
  };

  constructor(config?: Partial<AgentPolicyFirewall['config']>) {
    this.config = {
      maxBlastRadius: 10,
      replayWindowSeconds: 300,
      toxicityDenyThreshold: 75,
      toxicitySandboxThreshold: 40,
      canaryToolNames: ['connector.canary_override', 'connector.admin_db_override'],
      ...config,
    };
    this.sodRules = [
      { conflictRoleA: 'auditor', conflictRoleB: 'developer', ruleName: 'auditor-developer-separation', severity: 'HIGH' },
      { conflictRoleA: 'approver', conflictRoleB: 'executor', ruleName: 'segregation-of-duties', severity: 'HIGH' },
      { conflictRoleA: 'admin', conflictRoleB: 'readonly', ruleName: 'admin-readonly-conflict', severity: 'MEDIUM' },
    ];
  }

  evaluate(
    actor: FirewallActor,
    request: FirewallToolRequest,
    context: FirewallContext,
  ): FirewallDecision {
    const anomalies: string[] = [];
    let blastRadiusScore = 0;
    let replayDetected = false;
    let canaryTriggered = false;
    let sodViolation = false;

    // 1. Blocked actor check
    if (this.blockedActors.has(actor.id)) {
      return this.deny(actor, request, 'actor_blocked', context, anomalies);
    }

    // 2. Canary/honeypot trap check
    if (this.config.canaryToolNames.includes(request.toolName)) {
      canaryTriggered = true;
      this.recordCanaryTrap(request.toolName, actor);
      anomalies.push('canary_tool_triggered');
      return this.deny(actor, request, 'canary_trap_triggered', context, anomalies);
    }

    // 3. Tool allowlist check
    if (context.deniedTools.includes(request.toolName)) {
      return this.deny(actor, request, 'tool_explicitly_denied', context, anomalies);
    }
    if (context.allowedTools.length > 0 && !context.allowedTools.includes(request.toolName)) {
      return this.deny(actor, request, 'tool_not_in_allowlist', context, anomalies);
    }

    // 4. Tier-based authorization
    const tierAuthorized = this.checkTierAuthorization(request.tier, context);
    if (!tierAuthorized) {
      return this.deny(actor, request, `tier_${request.tier}_not_authorized`, context, anomalies);
    }

    // 5. Segregation of Duties check
    if (actor.role) {
      for (const rule of this.sodRules) {
        if (
          (actor.role === rule.conflictRoleA && context.role === rule.conflictRoleB) ||
          (actor.role === rule.conflictRoleB && context.role === rule.conflictRoleA)
        ) {
          sodViolation = true;
          anomalies.push(`sod_violation:${rule.ruleName}`);
          if (rule.severity === 'HIGH') {
            return this.deny(actor, request, `sod_violation:${rule.ruleName}`, context, anomalies);
          }
        }
      }
    }

    // 6. Replay detection
    if (request.idempotencyKey) {
      const existing = this.replayWindow.get(request.idempotencyKey);
      if (existing) {
        const elapsed = (Date.now() - new Date(existing.firstSeen).getTime()) / 1000;
        if (elapsed < this.config.replayWindowSeconds) {
          replayDetected = true;
          existing.count++;
          existing.lastSeen = new Date().toISOString();
          anomalies.push('replay_detected');
          return this.deny(actor, request, 'replay_detected', context, anomalies);
        }
        this.replayWindow.delete(request.idempotencyKey);
      }
      this.replayWindow.set(request.idempotencyKey, {
        idempotencyKey: request.idempotencyKey,
        firstSeen: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        count: 1,
        actorId: actor.id,
      });
    }

    // 7. Blast radius scoring
    blastRadiusScore = this.calculateBlastRadius(request, context);
    if (blastRadiusScore > this.config.maxBlastRadius) {
      anomalies.push('blast_radius_exceeded');
      return this.deny(actor, request, 'blast_radius_exceeded', context, anomalies);
    }

    // 8. Approval threshold check
    const requiresApproval = this.requiresApproval(request.tier, context.approvalThreshold);

    // 9. Sandbox policy
    const sandbox = this.resolveSandbox(request.tier, context.sandboxPolicy);

    // 10. Build decision
    const decision: FirewallDecision = {
      allowed: true,
      reason: 'approved_by_firewall',
      sandbox,
      requiresApproval,
      approvalThreshold: context.approvalThreshold,
      blastRadiusScore,
      controlImpact: context.controlImpactIds ?? [],
      replayDetected,
      canaryTriggered,
      sodViolation,
      anomaliesDetected: anomalies,
      receiptHash: '',
    };

    decision.receiptHash = this.hashDecision(actor, request, decision);
    return decision;
  }

  private checkTierAuthorization(tier: FirewallActionTier, context: FirewallContext): boolean {
    const tierLevels: Record<FirewallActionTier, number> = {
      read: 0,
      write: 1,
      destructive: 2,
      provision: 3,
      decommission: 4,
    };
    const contextMaxTier = context.dataBoundary === 'airgapped' || context.dataBoundary === 'sovereign'
      ? 'read'
      : context.dataBoundary === 'cui' || context.dataBoundary === 'phi'
        ? 'write'
        : 'destructive';
    return tierLevels[tier] <= tierLevels[contextMaxTier as FirewallActionTier];
  }

  private calculateBlastRadius(request: FirewallToolRequest, context: FirewallContext): number {
    let score = 0;
    if (request.tier === 'destructive') score += 5;
    else if (request.tier === 'write') score += 2;
    if (context.controlImpactIds && context.controlImpactIds.length > 3) score += 3;
    if (context.dataBoundary === 'cui' || context.dataBoundary === 'phi') score += 2;
    if (context.dataBoundary === 'sovereign' || context.dataBoundary === 'airgapped') score += 4;
    return score;
  }

  private requiresApproval(tier: FirewallActionTier, threshold: ApprovalThreshold): boolean {
    if (threshold === 'none') return false;
    if (threshold === 'human' && (tier === 'destructive' || tier === 'provision')) return true;
    if (threshold === 'dual_control' && tier !== 'read') return true;
    if (threshold === 'board' || threshold === 'government_buyer') return true;
    return false;
  }

  private resolveSandbox(tier: FirewallActionTier, preferred: SandboxPolicy): SandboxPolicy {
    if (preferred === 'denied') return 'denied';
    if (tier === 'destructive') return 'docker';
    if (tier === 'provision') return preferred === 'none' ? 'docker' : preferred;
    return preferred;
  }

  private deny(
    actor: FirewallActor,
    request: FirewallToolRequest,
    reason: string,
    context: FirewallContext,
    anomalies: string[],
  ): FirewallDecision {
    return {
      allowed: false,
      reason,
      sandbox: 'denied',
      requiresApproval: false,
      approvalThreshold: context.approvalThreshold,
      blastRadiusScore: 0,
      controlImpact: [],
      replayDetected: false,
      canaryTriggered: reason === 'canary_trap_triggered',
      sodViolation: reason.startsWith('sod_violation'),
      anomaliesDetected: anomalies,
      receiptHash: '',
    };
  }

  private hashDecision(actor: FirewallActor, request: FirewallToolRequest, decision: FirewallDecision): string {
    return sha256({ actor: actor.id, tool: request.toolName, allowed: decision.allowed, reason: decision.reason, ts: Date.now() });
  }

  private recordCanaryTrap(toolName: string, actor: FirewallActor): void {
    const existing = this.canaryTraps.get(toolName);
    if (existing) {
      existing.triggerCount++;
      existing.lastTriggered = new Date().toISOString();
      existing.actorId = actor.id;
    } else {
      this.canaryTraps.set(toolName, {
        toolName,
        triggerCount: 1,
        lastTriggered: new Date().toISOString(),
        actorId: actor.id,
      });
    }
  }

  createReceipt(actor: FirewallActor, request: FirewallToolRequest, context: FirewallContext, decision: FirewallDecision): FirewallReceipt {
    const receiptId = generateReceiptId();
    const timestamp = new Date().toISOString();
    const receiptHash = sha256({ receiptId, timestamp, actor: actor.id, tool: request.toolName, allowed: decision.allowed });

    return {
      version: 'v1',
      receiptId,
      timestamp,
      actor,
      request,
      context,
      decision,
      receiptHash,
    };
  }

  blockActor(actorId: string): void {
    this.blockedActors.add(actorId);
  }

  unblockActor(actorId: string): void {
    this.blockedActors.delete(actorId);
  }

  getCanaryTraps(): CanaryTrap[] {
    return [...this.canaryTraps.values()];
  }

  getReplayEntries(): ReplayEntry[] {
    return [...this.replayWindow.values()];
  }

  addSoDRule(rule: SoDRule): void {
    this.sodRules.push(rule);
  }

  getSoDRules(): SoDRule[] {
    return [...this.sodRules];
  }

  getStats(): {
    totalReceipts: number;
    blockedActors: number;
    canaryTriggers: number;
    replayDetections: number;
    sodRules: number;
  } {
    return {
      totalReceipts: 0,
      blockedActors: this.blockedActors.size,
      canaryTriggers: [...this.canaryTraps.values()].reduce((sum, t) => sum + t.triggerCount, 0),
      replayDetections: [...this.replayWindow.values()].filter((e) => e.count > 1).length,
      sodRules: this.sodRules.length,
    };
  }
}

export function formatFirewallReceiptForEvidenceGraph(receipt: FirewallReceipt): Record<string, unknown> {
  return {
    objectKind: 'node',
    objectType: 'policy_decision',
    label: `Firewall: ${receipt.request.toolName} → ${receipt.decision.allowed ? 'ALLOWED' : 'DENIED'}`,
    source: 'agent-policy-firewall',
    payload: {
      receipt_id: receipt.receiptId,
      actor_id: receipt.actor.id,
      actor_type: receipt.actor.type,
      tool: receipt.request.toolName,
      tier: receipt.request.tier,
      allowed: receipt.decision.allowed,
      reason: receipt.decision.reason,
      sandbox: receipt.decision.sandbox,
      blast_radius: receipt.decision.blastRadiusScore,
      control_impact: receipt.decision.controlImpact,
      anomalies: receipt.decision.anomaliesDetected,
    },
  };
}
