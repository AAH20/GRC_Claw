export type ToolTier = 'read' | 'write' | 'destructive';

export interface ToolDefinition {
  name: string;
  tier: ToolTier;
  allowedPrefixes?: string[];
}

export interface SoDRule {
  conflictRoleA: string;
  conflictRoleB: string;
  ruleName?: string;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface ExecPolicyConfig {
  maxCallsPerTurn: number;
  callTimeoutMs: number;
  defaultSandbox: 'docker' | 'host';
  canaryTools?: string[];
  sodRules?: SoDRule[];
  nonSovereignProviders?: string[];
  sovereignRestrictedTools?: string[];
}

export interface ToolInvocation {
  tool: string;
  args: Record<string, unknown>;
  approvalToken?: string;
  idempotencyKey?: string;
  agentRole?: string; // Added for Swarm Harness (SoD checks)
  llmProviderId?: string; // Added for Sovereign Boundary checks (CMMC/ITAR)
}

export interface ExecDecision {
  allowed: boolean;
  reason: string;
  sandbox: 'docker' | 'host' | 'denied';
  requiresApproval: boolean;
  toxicityScore?: number; // Real-time toxicity feedback
  anomaliesDetected?: string[];
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
  // Enterprise Connector Tools (Nvidia/Nemotron Strategy)
  { name: 'servicenow.create_incident', tier: 'write' },
  { name: 'sap.query_access_logs', tier: 'read' },
  { name: 'nemotron.evaluate_compliance', tier: 'read' },
  // Canary/Honeypot Decoy Tools for Anti-Swarm Testing
  { name: 'connector.canary_override', tier: 'destructive' },
  { name: 'connector.admin_db_override', tier: 'destructive' },
  // UAS Swarm Governance and C-UAS Audit Tools
  { name: 'uas.validate_telemetry', tier: 'read' },
  { name: 'cuas.audit_hardware_status', tier: 'read' },
  // CMMC 2.0 & NIST SP 800-171 Compliance Tools
  { name: 'cmmc.validate_system_boundary', tier: 'read' },
  { name: 'cmmc.generate_audit_evidence', tier: 'write' },
  // Sovereign Airgapped Compute Boundary Verification
  { name: 'sovereign.verify_compute_boundary', tier: 'read' },
];

/** Three-phase exec policy: allowlist → approval → sandbox + Swarm Harness checks */
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
      canaryTools: ['connector.canary_override', 'connector.admin_db_override'],
      sodRules: [
        { conflictRoleA: 'developer', conflictRoleB: 'reviewer', ruleName: 'Dev-Review SoD Conflict' },
        { conflictRoleA: 'developer', conflictRoleB: 'deployer', ruleName: 'Dev-Deploy SoD Conflict' }
      ],
      nonSovereignProviders: ['zhipu-glm', 'moonshot-kimi'],
      sovereignRestrictedTools: [
        'grc.list_controls',
        'grc.get_compliance_score',
        'evidence.read',
        'cmmc.validate_system_boundary',
        'cmmc.generate_audit_evidence'
      ],
      ...config,
    };
  }

  evaluate(inv: ToolInvocation, approvedDestructive = false): ExecDecision {
    // 0. Check Sovereign Boundary compliance (CMMC / ITAR / ISO 42001)
    if (inv.llmProviderId && this.config.nonSovereignProviders?.includes(inv.llmProviderId)) {
      const isRestricted = this.config.sovereignRestrictedTools?.includes(inv.tool) || inv.tool.startsWith('cmmc.');
      if (isRestricted) {
        return {
          allowed: false,
          reason: `sovereign_boundary_violation: non-sovereign LLM provider ${inv.llmProviderId} is denied access to sensitive GRC/CMMC tool ${inv.tool}`,
          sandbox: 'denied',
          requiresApproval: false,
        };
      }
    }

    // 1. Check for Canary / Honeypot Tools (Anti-Swarm Defense)
    const isCanary = this.config.canaryTools?.includes(inv.tool) || inv.tool.includes('.canary') || inv.tool.includes('canary_');
    if (isCanary) {
      return {
        allowed: false,
        reason: 'honeypot_triggered',
        sandbox: 'denied',
        requiresApproval: false,
        anomaliesDetected: ['HONEYPOT_ACCESS_ATTEMPT'],
      };
    }

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
  private toxicityScore = 0;
  
  // Keep track of call history to perform behavioral auditing
  private readonly callHistory: {
    tool: string;
    argsString: string;
    agentRole?: string;
    timestamp: number;
  }[] = [];

  constructor(
    public readonly sessionId: string,
    private readonly policy: ExecPolicy
  ) {}

  async invoke(inv: ToolInvocation): Promise<ExecDecision> {
    const timestamp = Date.now();
    const anomalies: string[] = [];

    // 1. Max calls safety check
    if (this.calls >= this.policy.config.maxCallsPerTurn) {
      const decision: ExecDecision = {
        allowed: false,
        reason: 'max_calls_exceeded',
        sandbox: 'denied',
        requiresApproval: false,
        toxicityScore: this.toxicityScore,
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

    // 2. Behavioral Auditing: Loop Anomaly Detection
    const argsString = JSON.stringify(inv.args);
    const consecutiveRepeats = this.callHistory.slice(-2).filter(
      (h) => h.tool === inv.tool && h.argsString === argsString
    ).length;
    if (consecutiveRepeats >= 2) {
      anomalies.push('LOOP_ANOMALY');
      this.toxicityScore = Math.min(100, this.toxicityScore + 25);
    }

    // 3. Behavioral Auditing: Rapid Discovery / Timing Anomaly
    const lastCall = this.callHistory[this.callHistory.length - 1];
    if (lastCall && (timestamp - lastCall.timestamp) < 50) {
      anomalies.push('RAPID_DISCOVERY_ANOMALY');
      this.toxicityScore = Math.min(100, this.toxicityScore + 15);
    }

    // 4. Swarm Harness: Segregation of Duties (SoD) Checks
    if (inv.agentRole && this.policy.config.sodRules) {
      const activeRoles = new Set(
        this.callHistory
          .map((h) => h.agentRole)
          .filter((r): r is string => !!r)
      );
      
      // Add current role to trace path
      activeRoles.add(inv.agentRole);

      for (const rule of this.policy.config.sodRules) {
        if (activeRoles.has(rule.conflictRoleA) && activeRoles.has(rule.conflictRoleB)) {
          anomalies.push('SOD_CONFLICT_DETECTED');
          this.toxicityScore = Math.min(100, this.toxicityScore + 30);
          
          const decision: ExecDecision = {
            allowed: false,
            reason: `segregation_of_duties_violation: ${rule.ruleName || 'conflict'}`,
            sandbox: 'denied',
            requiresApproval: false,
            toxicityScore: this.toxicityScore,
            anomaliesDetected: anomalies,
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
      }
    }

    // 5. Evaluate base policy rules (canary, allowed prefix, tier limits)
    let decision = this.policy.evaluate(inv);
    
    // Inject behavioral audit results
    if (anomalies.length > 0) {
      decision.anomaliesDetected = [
        ...(decision.anomaliesDetected ?? []),
        ...anomalies
      ];
    }
    
    // Apply toxicity modifiers to decision routing
    if (decision.anomaliesDetected?.includes('HONEYPOT_ACCESS_ATTEMPT')) {
      this.toxicityScore = 100;
    }
    
    decision.toxicityScore = this.toxicityScore;

    // Toxicity Containment Policy:
    // - Toxicity >= 75 -> Immediately deny execution
    // - Toxicity >= 40 -> Contain execution in Docker sandbox (override host setting)
    if (this.toxicityScore >= 75) {
      if (decision.allowed) {
        decision.allowed = false;
        decision.reason = `high_toxicity_containment: score=${this.toxicityScore}`;
      }
      decision.sandbox = 'denied';
    } else if (this.toxicityScore >= 40) {
      decision.sandbox = 'docker'; // Force isolated sandbox containment
    }

    // Store call history
    this.callHistory.push({
      tool: inv.tool,
      argsString,
      agentRole: inv.agentRole,
      timestamp,
    });

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

  getToxicityScore(): number {
    return this.toxicityScore;
  }
}

export * from './hermes-provider.js';
export * from './orchestrator.js';


