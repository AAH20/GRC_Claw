import { AgentIdentityManager } from '@grc-claw/agent-identity';
import { SecurityGraph, type BlastRadius, type RiskAssessment } from '@grc-claw/security-graph';
import type { ActionLedgerEvent } from '@grc-claw/evidence';
import type { ToolTier } from '@grc-claw/agent-runtime';

export interface AssuranceSnapshot {
  actionId: string;
  agentDid: string;
  identityStatus: 'provisional';
  toolTier: ToolTier;
  risk: RiskAssessment;
  blastRadius?: BlastRadius;
  gate: { enforced: boolean; allowed: boolean; reason?: string };
}

interface IntentContext {
  agentId?: string;
  tenantId: number;
  sessionId: string;
  tool: string;
  args: Record<string, unknown>;
  toolTier: ToolTier;
}

/**
 * Connects gateway actions to the DID registry and security graph. Gateway-created DIDs are
 * provisional observations: no credential is issued and no external identity is asserted.
 */
export class GatewayAssuranceGraph {
  private readonly identity = new AgentIdentityManager();
  private readonly graph = new SecurityGraph();
  private readonly principals = new Map<string, string>();
  private readonly actions = new Map<string, AssuranceSnapshot>();
  private readonly maxRisk = configuredMaxRisk();

  async observeIntent(intent: ActionLedgerEvent, context: IntentContext): Promise<AssuranceSnapshot> {
    const agentDid = await this.agentDidFor(context.agentId, context.sessionId, context.tenantId);
    const tenantNodeId = `tenant:${context.tenantId}`;
    const toolNodeId = `tool:${context.tool}`;
    const controlId = controlIdFromArgs(context.args);

    this.graph.addNode({
      id: agentDid,
      type: 'agent',
      name: context.agentId?.trim() || `gateway session ${context.sessionId}`,
      riskScore: 0,
      properties: { identityStatus: 'provisional', tenantId: context.tenantId },
      tags: ['gateway', 'provisional-identity'],
    });
    this.graph.addNode({
      id: tenantNodeId,
      type: 'tenant',
      name: `tenant ${context.tenantId}`,
      riskScore: 0,
      properties: { tenantId: context.tenantId },
      tags: ['tenant'],
    });
    this.graph.addNode({
      id: toolNodeId,
      type: 'tool',
      name: context.tool,
      riskScore: context.toolTier === 'destructive' ? 70 : context.toolTier === 'write' ? 35 : 5,
      properties: { toolTier: context.toolTier },
      tags: [context.toolTier],
    });
    this.addEdge(agentDid, tenantNodeId, 'scoped_to', context.sessionId, 'pass', 'gateway tenant scope');
    this.addEdge(
      agentDid,
      toolNodeId,
      'invoked',
      context.sessionId,
      'pending',
      `action=${intent.actionId}; tier=${context.toolTier}`
    );

    let blastRadius: BlastRadius | undefined;
    if (controlId) {
      this.graph.addNode({
        id: controlId,
        type: 'control',
        name: controlId,
        riskScore: context.toolTier === 'destructive' ? 60 : 20,
        properties: { tenantId: context.tenantId },
        tags: ['gateway-target'],
      });
      this.addEdge(toolNodeId, controlId, 'mitigates', context.sessionId, 'pending', `action=${intent.actionId}`);
      blastRadius = this.graph.calculateBlastRadius(controlId);
    }

    const risk = this.graph.assessAgentRisk(agentDid);
    const blocked = this.maxRisk !== undefined && risk.overallRisk >= this.maxRisk;
    const snapshot: AssuranceSnapshot = {
      actionId: intent.actionId,
      agentDid,
      identityStatus: 'provisional',
      toolTier: context.toolTier,
      risk,
      blastRadius,
      gate: blocked
        ? { enforced: true, allowed: false, reason: 'assurance_risk_threshold_exceeded' }
        : { enforced: this.maxRisk !== undefined, allowed: true },
    };
    this.actions.set(intent.actionId, snapshot);
    return snapshot;
  }

  observeDecision(intent: ActionLedgerEvent, allowed: boolean, reason: string): AssuranceSnapshot | undefined {
    const snapshot = this.actions.get(intent.actionId);
    if (!snapshot) return undefined;
    if (!allowed) {
      this.addEdge(
        snapshot.agentDid,
        `tool:${intent.tool}`,
        'violated',
        intent.sessionId,
        'blocked',
        `action=${intent.actionId}; reason=${reason}`
      );
    }
    const risk = this.graph.assessAgentRisk(snapshot.agentDid);
    const updated = { ...snapshot, risk };
    this.actions.set(intent.actionId, updated);
    return updated;
  }

  get(actionId: string): AssuranceSnapshot | undefined {
    return this.actions.get(actionId);
  }

  summary(): { stats: ReturnType<SecurityGraph['getStats']>; identities: ReturnType<AgentIdentityManager['getStats']> } {
    return { stats: this.graph.getStats(), identities: this.identity.getStats() };
  }

  private async agentDidFor(agentId: string | undefined, sessionId: string, tenantId: number): Promise<string> {
    const principal = agentId?.trim() || `session:${sessionId}`;
    const existing = this.principals.get(principal);
    if (existing) return existing;
    const did = (await this.identity.createAgentDID({
      controller: 'did:grc:gateway',
      tenantScope: [String(tenantId)],
      sovereignBoundary: 'global',
    })).id;
    this.principals.set(principal, did);
    return did;
  }

  private addEdge(
    source: string,
    target: string,
    relationship: 'invoked' | 'violated' | 'mitigates' | 'scoped_to',
    sessionId: string,
    result: 'pass' | 'blocked' | 'pending',
    details: string
  ): void {
    this.graph.addEdge({
      source,
      target,
      relationship,
      metadata: { timestamp: new Date().toISOString(), sessionId, result, confidence: 1, details },
    });
  }
}

function configuredMaxRisk(): number | undefined {
  const value = process.env.GRC_CLAW_ASSURANCE_MAX_RISK?.trim();
  if (!value) return undefined;
  const risk = Number(value);
  return Number.isFinite(risk) && risk >= 0 && risk <= 100 ? risk : undefined;
}

function controlIdFromArgs(args: Record<string, unknown>): string | undefined {
  const controlId = args.controlId ?? args.control_id;
  return typeof controlId === 'string' && controlId.trim() ? controlId.trim() : undefined;
}
