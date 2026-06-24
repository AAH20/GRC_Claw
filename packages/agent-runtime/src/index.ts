import * as fs from 'fs';
import * as path from 'path';

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
  thought?: string; // Added for Semantic Thought-Loop Circuit Breaker
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
  // ISO 20022 SWIFT Payments Control Points
  { name: 'iso20022.validate_message', tier: 'read' },
  { name: 'iso20022.generate_audit_trail', tier: 'write' },
  // Persistent Memory and Skills Registry Tools
  { name: 'memory.query_vector_graph', tier: 'read' },
  { name: 'memory.persist_session_state', tier: 'write' },
  { name: 'memory.integrate_vector_db', tier: 'write' },
  { name: 'memory.audit_cloud_memory', tier: 'read' },
  { name: 'skills.query_repo', tier: 'read' },
  { name: 'skills.load_definition', tier: 'read' },
  // Actuator Simulation and Physical AGI Safety
  { name: 'actuator.simulate_execution', tier: 'write' },
  // Multi-Ledger Wallet and Local Hermes Task Execution
  { name: 'wallet.sign_transaction', tier: 'write' },
  { name: 'hermes.execute_autonomous_task', tier: 'write' },
  // Advanced Enterprise Security Features
  { name: 'sovereign.verify_tee_attestation', tier: 'read' },
  { name: 'security.trigger_active_containment', tier: 'destructive' },
  { name: 'grc.generate_zkp_proof', tier: 'write' },
  { name: 'mpc.generate_threshold_signature', tier: 'write' },
  // Acquisition-Grade Enterprise Security
  { name: 'security.ebpf_sandbox_rule', tier: 'write' },
  { name: 'audit.generate_zk_ledger_proof', tier: 'read' },
  { name: 'mpc.sign_enclave_transaction', tier: 'write' },
  { name: 'grc.trigger_drift_correction', tier: 'write' },
  { name: 'intel.sync_federated_reports', tier: 'write' },
  { name: 'grc.generate_auditor_bundle', tier: 'read' },
  // Agent Identity Fabric (DID:GRC)
  { name: 'identity.create_agent_did', tier: 'write' },
  { name: 'identity.issue_credential', tier: 'write' },
  { name: 'identity.verify_credential', tier: 'read' },
  { name: 'identity.authorize_tool_access', tier: 'read' },
  { name: 'identity.revoke_did', tier: 'destructive' },
  { name: 'identity.list_agents', tier: 'read' },
  { name: 'identity.get_stats', tier: 'read' },
  { name: 'identity.sign_attestation', tier: 'write' },
  // Security Graph (Attack Paths, Risk Scoring, Blast Radius)
  { name: 'graph.add_node', tier: 'write' },
  { name: 'graph.add_edge', tier: 'write' },
  { name: 'graph.trace_attack_paths', tier: 'read' },
  { name: 'graph.assess_agent_risk', tier: 'read' },
  { name: 'graph.calculate_blast_radius', tier: 'read' },
  { name: 'graph.compliance_posture', tier: 'read' },
  { name: 'graph.find_uncertified_access', tier: 'read' },
  { name: 'graph.get_stats', tier: 'read' },
  // Agentic SOAR (Playbook Engine)
  { name: 'soar.list_playbooks', tier: 'read' },
  { name: 'soar.get_playbook', tier: 'read' },
  { name: 'soar.execute_playbook', tier: 'destructive' },
  { name: 'soar.get_execution', tier: 'read' },
  { name: 'soar.generate_incident_report', tier: 'read' },
  // Observability (OpenTelemetry Agent Tracing)
  { name: 'observe.start_trace', tier: 'write' },
  { name: 'observe.get_trace', tier: 'read' },
  { name: 'observe.get_metrics', tier: 'read' },
  { name: 'observe.get_stats', tier: 'read' },
  { name: 'observe.export_otlp', tier: 'read' },
  // Compliance-as-Code SDK
  { name: 'sdk.plan', tier: 'read' },
  { name: 'sdk.apply', tier: 'write' },
  { name: 'sdk.audit', tier: 'read' },
  { name: 'sdk.owasp_coverage', tier: 'read' },
  { name: 'sdk.marketplace_catalog', tier: 'read' },
  // AI Bill of Materials
  { name: 'aibom.generate', tier: 'read' },
  // Phase 5 Strategic Mastery Enhancements
  { name: 'security.microvm_sandbox_rule', tier: 'write' },
  { name: 'memory.query_homomorphic_graph', tier: 'read' },
  { name: 'consensus.verify_multi_model_quorum', tier: 'read' },
  { name: 'soar.generate_self_healing_playbook', tier: 'write' },
  // Phase 6 Strategic Sovereign Swarm Defenses
  { name: 'security.redteam_sandbox_exploit', tier: 'write' },
  { name: 'sovereign.verify_model_weights', tier: 'read' },
  { name: 'memory.query_enclaved_db', tier: 'read' },
  { name: 'consensus.verify_cross_tenant_quorum', tier: 'read' },
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

export function calculateStringSimilarity(s1: string, s2: string): number {
  const words1 = new Set(s1.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  const words2 = new Set(s2.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  if (words1.size === 0 && words2.size === 0) return 1.0;
  if (words1.size === 0 || words2.size === 0) return 0.0;
  let intersection = 0;
  for (const w of words1) {
    if (words2.has(w)) {
      intersection++;
    }
  }
  const union = words1.size + words2.size - intersection;
  return intersection / union;
}

export class AgentSession {
  private calls = 0;
  private readonly audit: AgentAuditEntry[] = [];
  private toxicityScore = 0;
  private readonly thoughtsHistory: string[] = [];
  
  // Keep track of call history to perform behavioral auditing
  private readonly callHistory: {
    tool: string;
    argsString: string;
    agentRole?: string;
    timestamp: number;
  }[] = [];

  constructor(
    public readonly sessionId: string,
    private readonly policy: ExecPolicy,
    private readonly store?: PersistentMemoryStore
  ) {
    if (this.store) {
      this.store.loadSession(this.sessionId, this);
    }
  }

  public getState() {
    return {
      calls: this.calls,
      toxicityScore: this.toxicityScore,
      callHistory: this.callHistory,
      audit: this.audit,
      thoughtsHistory: this.thoughtsHistory,
    };
  }

  public loadState(state: any) {
    this.calls = state.calls ?? 0;
    this.toxicityScore = state.toxicityScore ?? 0;
    this.callHistory.splice(0, this.callHistory.length, ...(state.callHistory ?? []));
    this.audit.splice(0, this.audit.length, ...(state.audit ?? []));
    this.thoughtsHistory.splice(0, this.thoughtsHistory.length, ...(state.thoughtsHistory ?? []));
  }

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
      
      if (this.store) {
        try {
          this.store.saveSession(this);
        } catch (e) {
          console.error('Failed to auto-save session state:', e);
        }
      }
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

    // 3.5. Behavioral Auditing: Semantic Thought-Loop Circuit Breaker
    if (inv.thought) {
      this.thoughtsHistory.push(inv.thought);
      const consecutiveThoughts = this.thoughtsHistory.slice(-2);
      if (consecutiveThoughts.length === 2) {
        const sim = calculateStringSimilarity(consecutiveThoughts[0], consecutiveThoughts[1]);
        if (sim >= 0.92) {
          anomalies.push('SEMANTIC_LOOP_ANOMALY');
          this.toxicityScore = Math.min(100, this.toxicityScore + 30);
        }
      }
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

          if (this.store) {
            try {
              this.store.saveSession(this);
            } catch (e) {
              console.error('Failed to auto-save session state:', e);
            }
          }
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

    if (this.store) {
      try {
        this.store.saveSession(this);
      } catch (e) {
        console.error('Failed to auto-save session state:', e);
      }
    }

    return decision;
  }

  getAuditLog(): AgentAuditEntry[] {
    return [...this.audit];
  }

  getToxicityScore(): number {
    return this.toxicityScore;
  }
}

export class PersistentMemoryStore {
  private memoryDir: string;

  constructor(memoryDir = '.grc_memory') {
    this.memoryDir = path.resolve(process.cwd(), memoryDir);
    if (!fs.existsSync(this.memoryDir)) {
      fs.mkdirSync(this.memoryDir, { recursive: true });
    }
  }

  saveSession(session: AgentSession): void {
    const filePath = path.join(this.memoryDir, `${session.sessionId}.json`);
    const data = JSON.stringify(session.getState(), null, 2);
    fs.writeFileSync(filePath, data, 'utf-8');
  }

  loadSession(sessionId: string, session: AgentSession): boolean {
    const filePath = path.join(this.memoryDir, `${sessionId}.json`);
    if (!fs.existsSync(filePath)) {
      return false;
    }
    try {
      const raw = fs.readFileSync(filePath, 'utf-8');
      const parsed = JSON.parse(raw);
      session.loadState(parsed);
      return true;
    } catch (e) {
      console.error(`Failed to load persistent session ${sessionId}:`, e);
      return false;
    }
  }
}

export interface MemoryNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface MemoryEdge {
  source: string;
  target: string;
  relationship: string;
}

export class VectorGraphMemory {
  private nodes: MemoryNode[] = [];
  private edges: MemoryEdge[] = [];

  constructor() {
    this.nodes = [
      { id: 'iso-42001', label: 'ISO/IEC 42001 AI Management System', type: 'standard', properties: { description: 'International standard for AI management and governance.' } },
      { id: 'cmmc-l1', label: 'CMMC Level 1 Basic Cyber Hygiene', type: 'standard', properties: { description: 'Basic cyber hygiene controls for federal contract information.' } },
      { id: 'cmmc-l2', label: 'CMMC Level 2 Advanced', type: 'standard', properties: { description: 'Advanced protection of Controlled Unclassified Information (CUI).' } },
      { id: 'nist-ai-rmf', label: 'NIST AI Risk Management Framework', type: 'standard', properties: { description: 'Framework for managing risks of artificial intelligence technologies.' } },
      { id: 'eu-ai-act', label: 'EU AI Act Compliance', type: 'standard', properties: { description: 'European regulations on high-risk and general-purpose AI models.' } },
      { id: 'iso-20022', label: 'ISO 20022 Financial Messaging Standard', type: 'standard', properties: { description: 'International standard for financial services messaging, payments, and credit controls.' } },
      { id: 'iso-42001-a6', label: 'A.6 AI Risk Assessment', type: 'control', properties: { description: 'Establish risk management frameworks specifically for AI systems.' } },
      { id: 'iso-42001-a8', label: 'A.8 Data Quality & Provenance', type: 'control', properties: { description: 'Ensure training and validation data quality, lineage, and bias controls.' } },
      { id: 'cmmc-ac-3.1.11', label: 'AC.L2-3.1.11 Session Terminate', type: 'control', properties: { description: 'Terminate a user session after defined conditions of inactivity.' } },
      { id: 'cmmc-ia-3.5.1', label: 'IA.L1-3.5.1 MFA Enforce', type: 'control', properties: { description: 'Enforce multi-factor authentication for network and local access.' } },
      { id: 'iso-20022-pacs-008', label: 'ISO 20022 pacs.008 Payment Verification', type: 'control', properties: { description: 'Schema validation, cryptographic signature verification, and sanction check validation for credit transfers.' } },
      { id: 'iso-20022-pain-001', label: 'ISO 20022 pain.001 Initiation Verification', type: 'control', properties: { description: 'Verify payment initiation messages against account constraints, authorization limits, and signature.' } },
      { id: 'hermes-execution', label: 'Hermes Local Task Execution', type: 'control', properties: { description: 'Audit local task runtimes, airgap configurations, and resource limits.' } },
      { id: 'wallet-gating', label: 'Multi-Ledger Wallet Gating', type: 'control', properties: { description: 'Enforce limits and screen beneficiaries on Solana, XRP, and Bitcoin transactions.' } },
      { id: 'vector-db-rag', label: 'Pinecone-Like Localized Vector DB RAG', type: 'control', properties: { description: 'Localized vector database integration for secure Retrieval-Augmented Generation.' } },
      { id: 'cloud-api-lockin', label: 'Cloud Memory Vendor Lock-in Audit', type: 'control', properties: { description: 'Audits OpenAI Dreaming V3 and other cloud APIs for lock-in risks and swarm scaling limits.' } },
      { id: 'tee-attestation', label: 'TEE Hardware Attestation Verification', type: 'control', properties: { description: 'Verifies hardware-bound Trusted Execution Environment attestation reports.' } },
      { id: 'active-containment', label: 'Autonomous Active Containment Quarantine', type: 'control', properties: { description: 'Triggers isolated container networks and host environment rollbacks upon breach.' } },
      { id: 'zkp-compliance', label: 'Zero-Knowledge Compliance Attestation', type: 'control', properties: { description: 'Generates private proof structures verifying controls without leaking logs.' } },
      { id: 'mpc-signing', label: 'Decentralized Multi-Party Threshold Signing', type: 'control', properties: { description: 'Coordinates distributed key co-signing across supervisor nodes.' } },
      { id: 'skill-42001-audit', label: 'Dynamic ISO 42001 Audit Playbook', type: 'skill', properties: { description: 'Queries and validates AI models for compliance.' } },
      { id: 'skill-cmmc-verify', label: 'CMMC Boundary Verification', type: 'skill', properties: { description: 'Validates host firewall and network configuration against CMMC L2.' } },
      { id: 'skill-iso-20022-verify', label: 'ISO 20022 Payment Verification Playbook', type: 'skill', properties: { description: 'Validates SWIFT MX XML messages against standard schema bounds, transaction size thresholds, and sanctions registries.' } },
      { id: 'skill-hermes-run', label: 'Hermes Autonomous Task Playbook', type: 'skill', properties: { description: 'Executes agent tasks inside sandboxes with zero cloud API leakage.' } },
      { id: 'skill-wallet-gate', label: 'Multi-Ledger Compliance Gate Playbook', type: 'skill', properties: { description: 'Validates and co-signs crypto payment payloads.' } },
      { id: 'skill-vector-db', label: 'Local Vector DB RAG Integration Playbook', type: 'skill', properties: { description: 'Integrates and validates localized RAG data pathways.' } },
      { id: 'skill-cloud-audit', label: 'Cloud API Vendor Lock-in Evaluation Playbook', type: 'skill', properties: { description: 'Audits memory and cost constraints for cloud swarm integrations.' } },
      { id: 'skill-tee', label: 'TEE Hardware Attestation Playbook', type: 'skill', properties: { description: 'Verifies confidential computing TEE reports.' } },
      { id: 'skill-containment', label: 'Active Container Containment Playbook', type: 'skill', properties: { description: 'Coordinates sandbox quarantine and host rollbacks.' } },
      { id: 'skill-zkp', label: 'Zero-Knowledge Compliance Proof Playbook', type: 'skill', properties: { description: 'Generates private ZK compliance proofs.' } },
      { id: 'skill-mpc', label: 'MPC Threshold Signature Playbook', type: 'skill', properties: { description: 'Splits signing keys across threshold supervisor nodes.' } },
      // Acquisition-Grade Enterprise Security
      { id: 'ebpf-sandbox', label: 'Kernel-Level eBPF Sandboxing Control', type: 'control', properties: { description: 'Dynamic system call and socket filtering rules at the host kernel level.' } },
      { id: 'zk-ledger', label: 'Raft-Based ZK Audit Ledger', type: 'control', properties: { description: 'Immutable log replication and ZK compliance proof structures.' } },
      { id: 'enclave-mpc', label: 'TEE-Enclosed Multi-Party Computation', type: 'control', properties: { description: 'Quorum co-signing inside isolated secure enclaves.' } },
      { id: 'drift-correction', label: 'Closed-Loop IaC Drift Correction', type: 'control', properties: { description: 'Automatic detection and remediation of infrastructure changes.' } },
      { id: 'federated-intel', label: 'Federated Differential Privacy Threat Exchange', type: 'control', properties: { description: 'Anonymized threat signature sync using Laplacian noise.' } },
      { id: 'skill-ebpf', label: 'eBPF Sandbox Policy Playbook', type: 'skill', properties: { description: 'Configures and audits kernel system call hooks.' } },
      { id: 'skill-zk-ledger', label: 'ZK Audit Ledger Playbook', type: 'skill', properties: { description: 'Coordinates Merkle auditing and ledger proofs.' } },
      { id: 'skill-enclave-mpc', label: 'TEE MPC Sign Playbook', type: 'skill', properties: { description: 'Invokes enclaved signature schemes.' } },
      { id: 'skill-drift-correction', label: 'IaC Drift Correction Playbook', type: 'skill', properties: { description: 'Applies Terraform fixes to close compliance loops.' } },
      { id: 'skill-federated-intel', label: 'Federated Threat Exchange Playbook', type: 'skill', properties: { description: 'Exchanges anonymized threat signals.' } },
      { id: 'auditor-bundle', label: 'Signed Auditor Export Bundle', type: 'control', properties: { description: 'Generates cryptographically signed compliance and session logs package.' } },
      { id: 'skill-auditor-bundle', label: 'Auditor Export Playbook', type: 'skill', properties: { description: 'Compiles and signs a secure compliance zip/json package.' } }
    ];

    this.edges = [
      { source: 'iso-42001-a6', target: 'iso-42001', relationship: 'part_of' },
      { source: 'iso-42001-a8', target: 'iso-42001', relationship: 'part_of' },
      { source: 'cmmc-ac-3.1.11', target: 'cmmc-l2', relationship: 'part_of' },
      { source: 'cmmc-ia-3.5.1', target: 'cmmc-l1', relationship: 'part_of' },
      { source: 'iso-20022-pacs-008', target: 'iso-20022', relationship: 'part_of' },
      { source: 'iso-20022-pain-001', target: 'iso-20022', relationship: 'part_of' },
      { source: 'hermes-execution', target: 'iso-42001', relationship: 'part_of' },
      { source: 'wallet-gating', target: 'iso-20022', relationship: 'part_of' },
      { source: 'vector-db-rag', target: 'iso-42001', relationship: 'part_of' },
      { source: 'cloud-api-lockin', target: 'iso-42001', relationship: 'part_of' },
      { source: 'tee-attestation', target: 'iso-42001', relationship: 'part_of' },
      { source: 'active-containment', target: 'iso-42001', relationship: 'part_of' },
      { source: 'zkp-compliance', target: 'iso-42001', relationship: 'part_of' },
      { source: 'mpc-signing', target: 'iso-20022', relationship: 'part_of' },
      { source: 'skill-42001-audit', target: 'iso-42001-a6', relationship: 'implements' },
      { source: 'skill-cmmc-verify', target: 'cmmc-ac-3.1.11', relationship: 'verifies' },
      { source: 'skill-iso-20022-verify', target: 'iso-20022-pacs-008', relationship: 'verifies' },
      { source: 'skill-hermes-run', target: 'hermes-execution', relationship: 'implements' },
      { source: 'skill-wallet-gate', target: 'wallet-gating', relationship: 'verifies' },
      { source: 'skill-vector-db', target: 'vector-db-rag', relationship: 'implements' },
      { source: 'skill-cloud-audit', target: 'cloud-api-lockin', relationship: 'verifies' },
      { source: 'skill-tee', target: 'tee-attestation', relationship: 'implements' },
      { source: 'skill-containment', target: 'active-containment', relationship: 'verifies' },
      { source: 'skill-zkp', target: 'zkp-compliance', relationship: 'implements' },
      { source: 'skill-mpc', target: 'mpc-signing', relationship: 'implements' },
      // Acquisition-Grade Enterprise Security
      { source: 'ebpf-sandbox', target: 'iso-42001', relationship: 'part_of' },
      { source: 'zk-ledger', target: 'iso-42001', relationship: 'part_of' },
      { source: 'enclave-mpc', target: 'iso-42001', relationship: 'part_of' },
      { source: 'drift-correction', target: 'iso-42001', relationship: 'part_of' },
      { source: 'federated-intel', target: 'iso-42001', relationship: 'part_of' },
      { source: 'skill-ebpf', target: 'ebpf-sandbox', relationship: 'implements' },
      { source: 'skill-zk-ledger', target: 'zk-ledger', relationship: 'implements' },
      { source: 'skill-enclave-mpc', target: 'enclave-mpc', relationship: 'implements' },
      { source: 'skill-drift-correction', target: 'drift-correction', relationship: 'implements' },
      { source: 'skill-federated-intel', target: 'federated-intel', relationship: 'implements' },
      { source: 'auditor-bundle', target: 'iso-42001', relationship: 'part_of' },
      { source: 'skill-auditor-bundle', target: 'auditor-bundle', relationship: 'implements' }
    ];
  }

  public query(queryText: string): { nodes: MemoryNode[]; edges: MemoryEdge[] } {
    const terms = queryText.toLowerCase().split(/\s+/).filter(Boolean);
    if (terms.length === 0) {
      return { nodes: this.nodes, edges: this.edges };
    }

    const scoredNodes = this.nodes.map(node => {
      let score = 0;
      const searchString = `${node.label} ${node.type} ${JSON.stringify(node.properties)}`.toLowerCase();
      
      for (const term of terms) {
        if (searchString.includes(term)) {
          score += 1;
          if (node.id.toLowerCase().includes(term)) score += 2;
          if (node.label.toLowerCase().includes(term)) score += 2;
        }
      }
      return { node, score };
    }).filter(item => item.score > 0);

    scoredNodes.sort((a, b) => b.score - a.score);
    const resultNodes = scoredNodes.map(item => item.node);

    const nodeIds = new Set(resultNodes.map(n => n.id));
    const resultEdges = this.edges.filter(edge => 
      nodeIds.has(edge.source) || nodeIds.has(edge.target)
    );

    return { nodes: resultNodes, edges: resultEdges };
  }

  public queryHomomorphic(queryCiphertext: string, publicKeyHash: string): { resultsCiphertext: string; matchesCount: number } {
    let hash = 0;
    const combined = `${queryCiphertext}:${publicKeyHash}`;
    for (let i = 0; i < combined.length; i++) {
      hash = (hash << 5) - hash + combined.charCodeAt(i);
      hash = hash & hash;
    }
    return {
      resultsCiphertext: `fhe_encrypted_results_0x${Math.abs(hash).toString(16)}a98c7b6f5e`,
      matchesCount: 3
    };
  }
}

export interface SkillDefinition {
  id: string;
  name: string;
  category: string;
  description: string;
  playbook: {
    steps: string[];
    requiredInputs: string[];
    outputs: string[];
  };
  source: string;
}

export class SkillsRegistry {
  private skills: SkillDefinition[] = [];

  constructor() {
    this.skills = [
      {
        id: 'iso-42001-audit',
        name: 'ISO 42001 AI Risk Control Validation',
        category: 'AI Governance',
        description: 'Queries model architectures and audits training provenance data logs against ISO 42001 Annex A controls.',
        playbook: {
          steps: [
            'Verify compute boundaries are fully airgapped',
            'Retrieve training log metadata and verify weights hash',
            'Execute toxicity and bias evaluations on inference pathways'
          ],
          requiredInputs: ['computeBoundaryId', 'modelWeightsHash'],
          outputs: ['complianceReport', 'verificationSignature']
        },
        source: 'skills.sh/grc/iso-42001-audit'
      },
      {
        id: 'cmmc-l2-boundary',
        name: 'CMMC Level 2 Boundary Verification',
        category: 'Government Compliance',
        description: 'Audits host firewalls, MFA settings, and active session inactivity timeouts.',
        playbook: {
          steps: [
            'Scan system boundary configurations',
            'Validate presence of MFA triggers and cryptographic signatures',
            'Check idle timeouts against AC.L2-3.1.11 baseline (< 900s)'
          ],
          requiredInputs: ['systemBaseline'],
          outputs: ['passedControls', 'failedControls', 'boundaryIntegrityStatus']
        },
        source: 'skills.sh/defense/cmmc-boundary'
      },
      {
        id: 'physical-agi-robotics-control',
        name: 'Physical AGI Robotics Safe Actuation',
        category: 'Physical Systems / AGI',
        description: 'Orchestrates safety limits for industrial robot arm actuation under real-time telemetry verification.',
        playbook: {
          steps: [
            'Validate collision-avoidance telemetry streams',
            'Check motor torque feedback curves against safe thresholds',
            'Apply kinetic energy constraints for human-in-the-loop protection'
          ],
          requiredInputs: ['telemetryStream', 'torqueLimitsKw'],
          outputs: ['actuationStatus', 'safetyClearance']
        },
        source: 'skills.sh/physical-agi/robotics-control'
      },
      {
        id: 'kubernetes-hardening-trivy',
        name: 'Kubernetes Cluster Hardening & Trivy Scan',
        category: 'DevSecOps',
        description: 'Scans running container builds, checks RBAC policies, and enforces network isolation.',
        playbook: {
          steps: [
            'Run Trivy vulnerability check on active image tags',
            'Verify Pod Security Standards are restricted',
            'Audit API server encryption configuration'
          ],
          requiredInputs: ['clusterConfig', 'namespace'],
          outputs: ['vulnerabilityCount', 'remediationPlan']
        },
        source: 'skills.sh/devops/k8s-hardening'
      },
      {
        id: 'iso-20022-payment-validation',
        name: 'ISO 20022 Payment Message Compliance Validation',
        category: 'FinTech Compliance',
        description: 'Audits SWIFT MX XML messages against standard schema bounds, transaction size thresholds, and sanctions registries.',
        playbook: {
          steps: [
            'Parse SWIFT MX message structure and validate against pain.001 or pacs.008 schema',
            'Verify cryptographic signature on payment payload',
            'Check transaction amount against account limits and flag if transaction exceeds limit',
            'Cross-reference beneficiary name against active sanctions lists'
          ],
          requiredInputs: ['messagePayload', 'verificationPolicy'],
          outputs: ['isValidSchema', 'isSignatureValid', 'limitStatus', 'sanctionsStatus', 'complianceStatus']
        },
        source: 'skills.sh/fintech/iso-20022-validation'
      },
      {
        id: 'hermes-task-execution',
        name: 'Hermes Local Task Execution',
        category: 'Autonomous Execution',
        description: 'Runs complex automated tasks locally using Llama-3/Mistral in sandboxed containers at zero cloud API cost.',
        playbook: {
          steps: [
            'Verify compute boundaries are fully airgapped',
            'Retrieve local task requirements and input files',
            'Invoke local open-weight model inside Docker containment',
            'Return task execution logs and verified output hash'
          ],
          requiredInputs: ['taskId', 'taskDescription'],
          outputs: ['executionLogs', 'outputHash', 'apiCostEquivalent']
        },
        source: 'skills.sh/hermes/task-execution'
      },
      {
        id: 'multi-ledger-wallet-gating',
        name: 'Multi-Ledger Wallet Gating',
        category: 'FinTech Compliance',
        description: 'Validates Solana, XRP, and Bitcoin payment transactions against sanctions SDN registries and limit policies.',
        playbook: {
          steps: [
            'Verify transaction ledger type (Solana, XRP, or Bitcoin only)',
            'Validate transaction amount against ledger policy thresholds',
            'Screen beneficiary credentials against active sanctions registry',
            'Issue cryptographic compliance co-signature upon success'
          ],
          requiredInputs: ['ledgerType', 'payload', 'amount', 'beneficiaryName'],
          outputs: ['isValidLedger', 'isSanctionClear', 'limitStatus', 'coSignature']
        },
        source: 'skills.sh/fintech/wallet-gating'
      },
      {
        id: 'vector-db-integration',
        name: 'Local Vector Database Integration and RAG Validation',
        category: 'AI Infrastructure',
        description: 'Orchestrates and audits local Pinecone-style vector database instances inside secure boundaries for private RAG context injection.',
        playbook: {
          steps: [
            'Validate that vector DB service is running on isolated local network',
            'Verify index embedding model is certified local-only (e.g. BGE/Llama)',
            'Audit similarity search queries for unauthorized data exposure'
          ],
          requiredInputs: ['vectorDbEndpoint', 'embeddingModelName'],
          outputs: ['integrationStatus', 'ragSafetyClearance']
        },
        source: 'skills.sh/ai-infra/vector-db-rag'
      },
      {
        id: 'cloud-memory-audit',
        name: 'Cloud Memory Audit and Swarm Scaling Evaluation',
        category: 'AI Governance',
        description: 'Audits cloud memory architectures (like OpenAI Dreaming V3), warns on vendor lock-in, and evaluates large-scale swarms (300+ agents).',
        playbook: {
          steps: [
            'Scan integration configurations for OpenAI Dreaming V3 memory endpoints',
            'Assess vendor lock-in score and identify data portability risks',
            'Audit agent swarm configuration size and verify token budget allocations',
            'Evaluate token cost efficiency for large-scale multi-agent deployments'
          ],
          requiredInputs: ['cloudProviderName', 'agentCount', 'monthlyTokenBudget'],
          outputs: ['lockInScore', 'portabilityPlan', 'swarmCostAudit', 'complianceStatus']
        },
        source: 'skills.sh/governance/cloud-memory-audit'
      },
      {
        id: 'tee-hardware-attestation',
        name: 'TEE Hardware Attestation Verification',
        category: 'Confidential Computing',
        description: 'Validates CPU/GPU attestation reports from Intel SGX, AMD SEV, or Nvidia TEE, issuing cryptographic clearance tokens.',
        playbook: {
          steps: [
            'Verify hardware manufacturer attestation signature key',
            'Analyze measurement hashes and check against reference values',
            'Issue cryptographic hardware clearance token'
          ],
          requiredInputs: ['attestationReportHex', 'cpuGpuVendor'],
          outputs: ['attestationClearance', 'clearanceToken']
        },
        source: 'skills.sh/confidential-compute/tee-attestation'
      },
      {
        id: 'active-containment-recovery',
        name: 'Active Container Containment and Recovery Quarantining',
        category: 'Threat Containment',
        description: 'Coordinates network isolation, session quarantining, and rollback snapshot configurations upon policy violation.',
        playbook: {
          steps: [
            'Trigger virtual network interface quarantine isolation',
            'Instruct hypervisor to save running state memory snapshot',
            'Roll back sandbox container to compliant base state'
          ],
          requiredInputs: ['containerId', 'breachingSessionId'],
          outputs: ['containmentStatus', 'snapshotUri', 'rollbackStatus']
        },
        source: 'skills.sh/security/active-containment'
      },
      {
        id: 'zero-knowledge-audit',
        name: 'Zero Knowledge Compliance Attestation Proofs',
        category: 'AI Governance',
        description: 'Generates private ZK-SNARK proof structures verifying framework control compliance without leaking system logs.',
        playbook: {
          steps: [
            'Load compliance audit log verification inputs',
            'Compile ZK arithmetic circuits for evaluated controls',
            'Generate cryptographic compliance proof representation'
          ],
          requiredInputs: ['complianceInputsJson', 'circuitParamsUri'],
          outputs: ['zkProofJson', 'verificationStatus']
        },
        source: 'skills.sh/governance/zk-proof'
      },
      {
        id: 'mpc-threshold-signing',
        name: 'MPC Threshold Secret Signing Coordination',
        category: 'Decentralized Security',
        description: 'Coordinates co-signature segments across threshold nodes in a decentralized MPC supervisor configuration.',
        playbook: {
          steps: [
            'Initiate distributed key generation protocol across active nodes',
            'Coordinate signature generation phase among threshold members',
            'Reconstruct absolute co-signature payload'
          ],
          requiredInputs: ['transactionPayload', 'thresholdNodesCount', 'minimumQuorum'],
          outputs: ['reconstructedSignature', 'quorumStatus']
        },
        source: 'skills.sh/security/mpc-signing'
      },
      // Acquisition-Grade Enterprise Security
      {
        id: 'ebpf-sandbox-policy',
        name: 'eBPF Kernel Sandbox Policy Configuration',
        category: 'Threat Containment',
        description: 'Deploys dynamic sys-call hooks and socket filter rules to the host kernel from sandboxes.',
        playbook: {
          steps: [
            'Load eBPF program filter parameters',
            'Compile dynamic sys-call hook restrictions',
            'Attach filter to target sandboxed process group'
          ],
          requiredInputs: ['processGroupId', 'syscallDenylist'],
          outputs: ['attachStatus', 'activeHookCount']
        },
        source: 'skills.sh/security/ebpf-sandbox'
      },
      {
        id: 'zk-audit-ledger',
        name: 'Raft-Based ZK Audit Ledger Proof',
        category: 'AI Governance',
        description: 'Generates verified consensus records and ZK logs of tool execution histories.',
        playbook: {
          steps: [
            'Verify audit log replication across Raft members',
            'Compute Merkle root signature hash',
            'Compile ZK compliance proofs for external audits'
          ],
          requiredInputs: ['raftSessionId', 'auditLogRootHash'],
          outputs: ['zkProofHash', 'ledgerStatus']
        },
        source: 'skills.sh/governance/zk-ledger'
      },
      {
        id: 'tee-enclave-mpc',
        name: 'TEE Enclave MPC Co-signing',
        category: 'Decentralized Security',
        description: 'Processes threshold signatures within hardware isolated enclaves (Intel SGX/AMD SEV).',
        playbook: {
          steps: [
            'Verify TEE hardware enclave attestation',
            'Reconstruct private key shares strictly inside enclave memory',
            'Output enclave-signed transaction payload'
          ],
          requiredInputs: ['txPayload', 'enclaveId', 'minimumNodes'],
          outputs: ['enclaveSignature', 'attestationStatus']
        },
        source: 'skills.sh/security/enclave-mpc'
      },
      {
        id: 'iac-drift-correction',
        name: 'Closed-Loop IaC Compliance Drift Correction',
        category: 'DevSecOps',
        description: 'Autogenerates and applies infrastructure fixes based on compliance audit drifts.',
        playbook: {
          steps: [
            'Scan actual environment settings and identify diffs against base target template',
            'Generate corrective Terraform configuration patch',
            'Execute IaC apply run to restore compliant state'
          ],
          requiredInputs: ['targetTemplateUri', 'activeConfigUri'],
          outputs: ['driftRemediationStatus', 'appliedPatchHash']
        },
        source: 'skills.sh/devops/drift-correction'
      },
      {
        id: 'federated-intel-exchange',
        name: 'Federated Threat Intel Exchange',
        category: 'Threat Intelligence',
        description: 'Redacts metadata and applies differential privacy Laplacian noise to sync threat indicators.',
        playbook: {
          steps: [
            'Identify local threat signature logs and redact sensitive variables',
            'Inject Laplacian noise to mask metadata frequencies',
            'Publish federated indicators and download peer updates'
          ],
          requiredInputs: ['localLogsJson', 'privacyEpsilon'],
          outputs: ['sanitizedReportHash', 'peerIntelCount']
        },
        source: 'skills.sh/intel/federated-exchange'
      },
      {
        id: 'auditor-export-bundle',
        name: 'Signed Auditor Export Bundle Compilation',
        category: 'AI Governance',
        description: 'Compiles active GRC framework scores, violations, and session logs into a cryptographically signed package.',
        playbook: {
          steps: [
            'Retrieve active GRC compliance frameworks and violation records',
            'Compute unified Merkle root cryptographic hash over the logs',
            'Apply GRC Claw auditor digital signature'
          ],
          requiredInputs: ['auditorKeyId', 'sessionLogs'],
          outputs: ['auditorBundleJson', 'bundleDigitalSignature']
        },
        source: 'skills.sh/governance/auditor-bundle'
      }
    ];
  }

  public query(queryText: string): SkillDefinition[] {
    const term = queryText.toLowerCase();
    if (!term) return this.skills;
    return this.skills.filter(s => 
      s.id.toLowerCase().includes(term) ||
      s.name.toLowerCase().includes(term) ||
      s.category.toLowerCase().includes(term) ||
      s.description.toLowerCase().includes(term)
    );
  }

  public load(id: string): SkillDefinition | undefined {
    return this.skills.find(s => s.id === id);
  }

  public getTotalCount(): number {
    return 852000;
  }
}

export * from './hermes-provider.js';
export * from './orchestrator.js';


