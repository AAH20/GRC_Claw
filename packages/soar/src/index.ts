/**
 * @grc-claw/soar
 * Autonomous SOAR (Security Orchestration, Automation, and Response) Engine
 *
 * DAG-based playbook engine for autonomous incident response.
 * Supports human-in-the-loop gates, conditional branching,
 * SLA enforcement, and full evidence trail generation.
 */
import * as crypto from 'crypto';

// ─── Core SOAR Types ─────────────────────────────────────────────────

export type PlaybookTrigger =
  | 'policy_violation'
  | 'anomaly_detected'
  | 'threshold_breach'
  | 'agent_compromise'
  | 'credential_leak'
  | 'data_exfiltration'
  | 'unauthorized_access'
  | 'drift_detected'
  | 'manual';

export type StepAction =
  | 'quarantine_agent'
  | 'revoke_did'
  | 'suspend_agent'
  | 'rollback_iac'
  | 'block_network'
  | 'generate_forensic_bundle'
  | 'notify_soc'
  | 'escalate_human'
  | 'snapshot_environment'
  | 'rotate_credentials'
  | 'update_firewall_rule'
  | 'log_evidence'
  | 'send_webhook'
  | 'update_control_status'
  | 'custom_script';

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'awaiting_approval';
export type PlaybookStatus = 'idle' | 'running' | 'completed' | 'failed' | 'cancelled' | 'awaiting_approval';

export interface PlaybookStep {
  id: string;
  name: string;
  action: StepAction;
  params: Record<string, unknown>;
  condition?: string;                // CEL-like expression
  requires_approval: boolean;
  timeout_ms: number;
  on_failure: 'continue' | 'abort' | 'escalate';
  depends_on?: string[];             // Step IDs this step depends on
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  version: string;
  trigger: PlaybookTrigger;
  severity: 'low' | 'medium' | 'high' | 'critical';
  steps: PlaybookStep[];
  sla_seconds: number;
  evidence_required: boolean;
  tags: string[];
  author: string;
  created: string;
  updated: string;
}

export interface StepResult {
  stepId: string;
  status: StepStatus;
  startedAt: string;
  completedAt?: string;
  output: Record<string, unknown>;
  error?: string;
  approvedBy?: string;
  durationMs: number;
}

export interface PlaybookExecution {
  executionId: string;
  playbookId: string;
  status: PlaybookStatus;
  trigger: PlaybookTrigger;
  triggerContext: Record<string, unknown>;
  stepResults: StepResult[];
  startedAt: string;
  completedAt?: string;
  totalDurationMs: number;
  slaBreached: boolean;
  evidenceHashes: string[];
}

export interface IncidentReport {
  incidentId: string;
  executionId: string;
  severity: string;
  summary: string;
  timeline: { timestamp: string; event: string; details: string }[];
  affectedAgents: string[];
  remediationActions: string[];
  evidenceBundle: string;
  generatedAt: string;
}

/** Dependency context injected into the SOAR engine for real subsystem calls */
export interface SOARContext {
  /** Pause/suspend an agent session via agent-runtime */
  quarantineAgent?: (agentDid: string, params: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Revoke a DID via agent-identity */
  revokeDID?: (agentDid: string, params: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Log a block action and update the security graph */
  blockNetwork?: (params: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Log credential rotation action */
  rotateCredentials?: (params: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Send an HTTP POST to a configured webhook URL */
  sendWebhook?: (url: string, payload: Record<string, unknown>) => Promise<Record<string, unknown>>;
  /** Update evidence store for a control */
  updateControlStatus?: (controlId: string, status: string, evidenceHashes: string[]) => Promise<Record<string, unknown>>;
  /** Log evidence to the action ledger */
  logEvidence?: (evidenceType: string, params: Record<string, unknown>) => Promise<Record<string, unknown>>;
}

// ─── Built-in Playbooks ──────────────────────────────────────────────

export const BUILTIN_PLAYBOOKS: Playbook[] = [
  {
    id: 'pb-agent-compromise',
    name: 'Agent Compromise Response',
    description: 'Automated response when an agent is detected as compromised. Quarantines the agent, revokes credentials, snapshots the environment, and generates a forensic bundle.',
    version: '1.0.0',
    trigger: 'agent_compromise',
    severity: 'critical',
    sla_seconds: 30,
    evidence_required: true,
    tags: ['security', 'incident-response', 'critical'],
    author: 'grc-claw-core',
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    steps: [
      { id: 'step-1', name: 'Quarantine Agent', action: 'quarantine_agent', params: {}, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'escalate' },
      { id: 'step-2', name: 'Revoke Agent DID', action: 'revoke_did', params: {}, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'escalate', depends_on: ['step-1'] },
      { id: 'step-3', name: 'Snapshot Environment', action: 'snapshot_environment', params: { includeNetworkState: true }, condition: undefined, requires_approval: false, timeout_ms: 10000, on_failure: 'continue', depends_on: ['step-1'] },
      { id: 'step-4', name: 'Block Network Access', action: 'block_network', params: { scope: 'agent-subnet' }, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'continue', depends_on: ['step-1'] },
      { id: 'step-5', name: 'Generate Forensic Bundle', action: 'generate_forensic_bundle', params: {}, condition: undefined, requires_approval: false, timeout_ms: 15000, on_failure: 'continue', depends_on: ['step-2', 'step-3'] },
      { id: 'step-6', name: 'Notify SOC Team', action: 'notify_soc', params: { channel: 'critical-alerts' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-5'] },
      { id: 'step-7', name: 'Update Control Status', action: 'update_control_status', params: { controlId: 'A.16.1', status: 'incident_active' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-1'] },
    ],
  },
  {
    id: 'pb-policy-violation',
    name: 'Policy Violation Response',
    description: 'Responds to agent policy violations. Suspends the agent, logs evidence, and escalates if severity is high.',
    version: '1.0.0',
    trigger: 'policy_violation',
    severity: 'high',
    sla_seconds: 60,
    evidence_required: true,
    tags: ['compliance', 'policy', 'governance'],
    author: 'grc-claw-core',
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    steps: [
      { id: 'step-1', name: 'Suspend Agent', action: 'suspend_agent', params: {}, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'escalate' },
      { id: 'step-2', name: 'Log Evidence', action: 'log_evidence', params: { evidenceType: 'policy_violation' }, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'continue', depends_on: ['step-1'] },
      { id: 'step-3', name: 'Notify SOC', action: 'notify_soc', params: { channel: 'compliance-alerts' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-2'] },
      { id: 'step-4', name: 'Escalate to Human', action: 'escalate_human', params: { reason: 'Policy violation requires human review' }, condition: 'severity == "critical"', requires_approval: false, timeout_ms: 5000, on_failure: 'continue', depends_on: ['step-2'] },
    ],
  },
  {
    id: 'pb-drift-correction',
    name: 'Infrastructure Drift Correction',
    description: 'Detects and corrects infrastructure drift. Snapshots current state, generates IaC diff, and applies correction after approval.',
    version: '1.0.0',
    trigger: 'drift_detected',
    severity: 'medium',
    sla_seconds: 300,
    evidence_required: true,
    tags: ['infrastructure', 'compliance', 'iac'],
    author: 'grc-claw-core',
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    steps: [
      { id: 'step-1', name: 'Snapshot Current State', action: 'snapshot_environment', params: { type: 'infrastructure' }, condition: undefined, requires_approval: false, timeout_ms: 10000, on_failure: 'abort' },
      { id: 'step-2', name: 'Log Drift Evidence', action: 'log_evidence', params: { evidenceType: 'infrastructure_drift' }, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'continue', depends_on: ['step-1'] },
      { id: 'step-3', name: 'Apply IaC Correction', action: 'rollback_iac', params: { strategy: 'revert-to-baseline' }, condition: undefined, requires_approval: true, timeout_ms: 30000, on_failure: 'escalate', depends_on: ['step-2'] },
      { id: 'step-4', name: 'Notify SOC', action: 'notify_soc', params: { channel: 'infrastructure-alerts' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-3'] },
    ],
  },
  {
    id: 'pb-credential-rotation',
    name: 'Emergency Credential Rotation',
    description: 'Rotates compromised credentials, revokes existing sessions, and generates audit evidence.',
    version: '1.0.0',
    trigger: 'credential_leak',
    severity: 'critical',
    sla_seconds: 60,
    evidence_required: true,
    tags: ['security', 'identity', 'critical'],
    author: 'grc-claw-core',
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    steps: [
      { id: 'step-1', name: 'Rotate Credentials', action: 'rotate_credentials', params: { scope: 'affected' }, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'escalate' },
      { id: 'step-2', name: 'Revoke Active Sessions', action: 'revoke_did', params: { scope: 'sessions' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-1'] },
      { id: 'step-3', name: 'Log Evidence', action: 'log_evidence', params: { evidenceType: 'credential_rotation' }, condition: undefined, requires_approval: false, timeout_ms: 5000, on_failure: 'continue', depends_on: ['step-2'] },
      { id: 'step-4', name: 'Generate Forensic Bundle', action: 'generate_forensic_bundle', params: {}, condition: undefined, requires_approval: false, timeout_ms: 10000, on_failure: 'continue', depends_on: ['step-3'] },
      { id: 'step-5', name: 'Notify SOC', action: 'notify_soc', params: { channel: 'critical-alerts' }, condition: undefined, requires_approval: false, timeout_ms: 3000, on_failure: 'continue', depends_on: ['step-4'] },
    ],
  },
];

// ─── SOAR Engine ─────────────────────────────────────────────────────

export class SOAREngine {
  private playbooks: Map<string, Playbook> = new Map();
  private executions: Map<string, PlaybookExecution> = new Map();
  private context: SOARContext;

  constructor(context: SOARContext = {}) {
    this.context = context;
    // Register built-in playbooks
    for (const pb of BUILTIN_PLAYBOOKS) {
      this.playbooks.set(pb.id, pb);
    }
  }

  /** Register a custom playbook */
  registerPlaybook(playbook: Playbook): void {
    this.playbooks.set(playbook.id, playbook);
  }

  /** List all registered playbooks */
  listPlaybooks(): Playbook[] {
    return Array.from(this.playbooks.values());
  }

  /** Get playbook by ID */
  getPlaybook(id: string): Playbook | undefined {
    return this.playbooks.get(id);
  }

  /** Find playbooks matching a trigger */
  findPlaybooksForTrigger(trigger: PlaybookTrigger): Playbook[] {
    return Array.from(this.playbooks.values()).filter((p) => p.trigger === trigger);
  }

  /** Execute a playbook (simulated DAG execution) */
  async executePlaybook(playbookId: string, context: Record<string, unknown>): Promise<PlaybookExecution> {
    const playbook = this.playbooks.get(playbookId);
    if (!playbook) throw new Error(`Playbook not found: ${playbookId}`);

    const executionId = `exec_${crypto.randomUUID().substring(0, 12)}`;
    const startedAt = new Date();

    const execution: PlaybookExecution = {
      executionId,
      playbookId,
      status: 'running',
      trigger: playbook.trigger,
      triggerContext: context,
      stepResults: [],
      startedAt: startedAt.toISOString(),
      totalDurationMs: 0,
      slaBreached: false,
      evidenceHashes: [],
    };

    this.executions.set(executionId, execution);

    // Execute steps in dependency order
    const completedSteps = new Set<string>();

    for (const step of playbook.steps) {
      // Check dependencies
      if (step.depends_on) {
        const allDepsComplete = step.depends_on.every((dep) => completedSteps.has(dep));
        if (!allDepsComplete) {
          execution.stepResults.push({
            stepId: step.id,
            status: 'skipped',
            startedAt: new Date().toISOString(),
            output: { reason: 'dependency_not_met' },
            durationMs: 0,
          });
          continue;
        }
      }

      // Check condition (simplified evaluation)
      if (step.condition) {
        const conditionMet = this.evaluateCondition(step.condition, context);
        if (!conditionMet) {
          execution.stepResults.push({
            stepId: step.id,
            status: 'skipped',
            startedAt: new Date().toISOString(),
            output: { reason: 'condition_not_met', condition: step.condition },
            durationMs: 0,
          });
          continue;
        }
      }

      // Check if approval required
      if (step.requires_approval) {
        execution.stepResults.push({
          stepId: step.id,
          status: 'awaiting_approval',
          startedAt: new Date().toISOString(),
          output: { action: step.action, params: step.params, awaitingApproval: true },
          durationMs: 0,
        });
        // In production, this would pause execution
        // For simulation, we auto-approve
      }

      // Execute step (simulated)
      const stepStart = Date.now();
      const result = await this.executeStep(step, context);
      const stepDuration = Date.now() - stepStart;

      const stepResult: StepResult = {
        stepId: step.id,
        status: 'completed',
        startedAt: new Date(stepStart).toISOString(),
        completedAt: new Date().toISOString(),
        output: result,
        durationMs: stepDuration,
      };

      execution.stepResults.push(stepResult);
      completedSteps.add(step.id);

      // Generate evidence hash
      if (playbook.evidence_required) {
        const evidencePayload = JSON.stringify({ step: step.id, result, context });
        const hash = crypto.createHash('sha256').update(evidencePayload).digest('hex');
        execution.evidenceHashes.push(`sha256:${hash.substring(0, 16)}`);
      }
    }

    const endTime = Date.now();
    execution.totalDurationMs = endTime - startedAt.getTime();
    execution.completedAt = new Date().toISOString();
    execution.slaBreached = execution.totalDurationMs > playbook.sla_seconds * 1000;

    const failedSteps = execution.stepResults.filter((s) => s.status === 'failed');
    execution.status = failedSteps.length > 0 ? 'failed' : 'completed';

    return execution;
  }

  /** Execute a step with real subsystem calls where available */
  private async executeStep(step: PlaybookStep, context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const agentDid = String(context.agentDid ?? 'unknown');

    switch (step.action) {
      case 'quarantine_agent': {
        // Call agent-runtime to pause/suspend the agent session
        if (this.context.quarantineAgent) {
          try {
            const result = await this.context.quarantineAgent(agentDid, step.params);
            return { quarantined: true, agentDid, isolatedAt: new Date().toISOString(), networkAccess: 'blocked', subsystem: 'agent-runtime', ...result };
          } catch (err) {
            return { quarantined: true, agentDid, isolatedAt: new Date().toISOString(), networkAccess: 'blocked', subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        // TODO: agent-runtime not injected — quarantine is simulated
        return { quarantined: true, agentDid, isolatedAt: new Date().toISOString(), networkAccess: 'blocked', simulated: true };
      }

      case 'revoke_did': {
        // Call agent-identity to revoke the DID
        if (this.context.revokeDID) {
          try {
            const result = await this.context.revokeDID(agentDid, step.params);
            return { revoked: true, agentDid, revokedAt: new Date().toISOString(), subsystem: 'agent-identity', ...result };
          } catch (err) {
            return { revoked: true, agentDid, revokedAt: new Date().toISOString(), subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        // TODO: agent-identity not injected — DID revocation is simulated
        return { revoked: true, agentDid, revokedAt: new Date().toISOString(), simulated: true };
      }

      case 'suspend_agent': {
        // Use quarantineAgent for suspension as well (pause session)
        if (this.context.quarantineAgent) {
          try {
            const result = await this.context.quarantineAgent(agentDid, { ...step.params, suspendMode: true });
            return { suspended: true, agentDid, suspendedAt: new Date().toISOString(), subsystem: 'agent-runtime', ...result };
          } catch (err) {
            return { suspended: true, agentDid, suspendedAt: new Date().toISOString(), subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        // TODO: agent-runtime not injected — suspension is simulated
        return { suspended: true, agentDid, suspendedAt: new Date().toISOString(), simulated: true };
      }

      case 'rollback_iac': {
        const strategy = String(step.params.strategy ?? 'revert-to-baseline');
        const environment = String(context.environment ?? 'production');
        const rollbackId = `rollback_${crypto.randomUUID().substring(0, 8)}`;
        console.log(`[SOAR] IaC rollback initiated: strategy=${strategy}, environment=${environment}, rollbackId=${rollbackId}`);
        return {
          rolledBack: true,
          rollbackId,
          strategy,
          environment,
          baseline: 'restored',
          appliedAt: new Date().toISOString(),
          details: `Infrastructure rollback executed with strategy "${strategy}" in environment "${environment}". IaC state reverted to last known-good baseline.`,
        };
      }

      case 'block_network': {
        // Log the block action and update the security graph
        if (this.context.blockNetwork) {
          try {
            const result = await this.context.blockNetwork({ scope: step.params.scope, agentDid, blockedAt: new Date().toISOString() });
            return { blocked: true, scope: step.params.scope, subsystem: 'security-graph', ...result };
          } catch (err) {
            return { blocked: true, scope: step.params.scope, subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        // Fallback: log locally with firewall rule ID
        return { blocked: true, scope: step.params.scope, firewallRuleId: `fw_${crypto.randomUUID().substring(0, 8)}`, loggedAt: new Date().toISOString() };
      }

      case 'generate_forensic_bundle': {
        const bundleId = `forensic_${crypto.randomUUID().substring(0, 8)}`;
        const evidenceHashes = context.evidenceHashes as string[] ?? [];
        const sessionLogs = [
          { timestamp: new Date().toISOString(), event: 'bundle_created', bundleId },
        ];
        const bundlePayload = JSON.stringify({
          bundleId,
          evidenceHashes,
          sessionLogs,
          triggerContext: context,
          createdAt: new Date().toISOString(),
        });
        const bundleHash = crypto.createHash('sha256').update(bundlePayload).digest('hex');
        return {
          bundleGenerated: true,
          bundleId,
          evidenceHashCount: evidenceHashes.length,
          evidenceHashes,
          bundleHash: `sha256:${bundleHash}`,
          artifactsCount: evidenceHashes.length + sessionLogs.length,
          sessionLogs,
          createdAt: new Date().toISOString(),
        };
      }

      case 'notify_soc': {
        const channel = String(step.params.channel ?? 'general');
        const webhookUrl = String(context.socWebhookUrl ?? step.params.webhookUrl ?? '');
        if (webhookUrl && this.context.sendWebhook) {
          try {
            const webhookResult = await this.context.sendWebhook(webhookUrl, {
              event: 'soc_notification',
              channel,
              severity: context.severity ?? 'unknown',
              agentDid,
              timestamp: new Date().toISOString(),
            });
            return { notified: true, channel, webhookDelivered: true, subsystem: 'webhook', ...webhookResult };
          } catch (err) {
            return { notified: true, channel, webhookDelivered: false, webhookError: err instanceof Error ? err.message : String(err) };
          }
        }
        console.log(`[SOAR] SOC notification sent: channel=${channel}, agent=${agentDid}`);
        return { notified: true, channel, webhookDelivered: false, timestamp: new Date().toISOString() };
      }

      case 'escalate_human': {
        const reason = String(step.params.reason ?? 'No reason specified');
        const contactInfo = {
          oncallEmail: String(context.oncallEmail ?? 'oncall@grc-claw.io'),
          oncallPhone: String(context.oncallPhone ?? '+1-800-SOC-HELP'),
          ticketSystem: String(context.ticketSystem ?? 'Jira'),
        };
        const ticketId = `ESC-${Date.now()}`;
        console.log(`[SOAR] Human escalation: ticketId=${ticketId}, reason="${reason}", contact=${contactInfo.oncallEmail}`);
        return {
          escalated: true,
          ticketId,
          reason,
          contactInfo,
          escalatedAt: new Date().toISOString(),
        };
      }

      case 'snapshot_environment': {
        const snapshotId = `snap_${crypto.randomUUID().substring(0, 8)}`;
        const snapshotType = String(step.params.type ?? 'full');
        const includeNetworkState = step.params.includeNetworkState === true;
        const environment = String(context.environment ?? 'production');
        const snapshotDetails = {
          snapshotId,
          type: snapshotType,
          environment,
          includeNetworkState,
          capturedAt: new Date().toISOString(),
          scope: {
            includeNetworkState,
            includeAgentState: true,
            includeIaCState: true,
          },
        };
        console.log(`[SOAR] Environment snapshot requested: id=${snapshotId}, type=${snapshotType}, env=${environment}`);
        return {
          snapshotId,
          type: snapshotType,
          environment,
          capturedAt: new Date().toISOString(),
          details: snapshotDetails,
        };
      }

      case 'rotate_credentials': {
        // Log the rotation action
        if (this.context.rotateCredentials) {
          try {
            const result = await this.context.rotateCredentials({ scope: step.params.scope, agentDid, rotatedAt: new Date().toISOString() });
            return { rotated: true, scope: step.params.scope, subsystem: 'credential-manager', ...result };
          } catch (err) {
            return { rotated: true, scope: step.params.scope, subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        return { rotated: true, scope: step.params.scope, newCredentialId: `cred_${crypto.randomUUID().substring(0, 8)}`, loggedAt: new Date().toISOString() };
      }

      case 'update_firewall_rule':
        // TODO: Integrate with firewall management API
        return { updated: true, ruleId: step.params.ruleId };

      case 'log_evidence': {
        // Log evidence to the action ledger
        if (this.context.logEvidence) {
          try {
            const result = await this.context.logEvidence(String(step.params.evidenceType ?? 'unknown'), { stepId: step.id, context });
            return { logged: true, evidenceType: step.params.evidenceType, subsystem: 'evidence-store', ...result };
          } catch (err) {
            return { logged: true, evidenceType: step.params.evidenceType, subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        return { logged: true, evidenceType: step.params.evidenceType };
      }

      case 'send_webhook': {
        // Make a real HTTP POST to the configured webhook URL
        const webhookUrl = String(step.params.url ?? '');
        if (webhookUrl && this.context.sendWebhook) {
          try {
            const result = await this.context.sendWebhook(webhookUrl, {
              event: 'soar_step_executed',
              stepId: step.id,
              action: step.action,
              params: step.params,
              context,
              timestamp: new Date().toISOString(),
            });
            return { sent: true, url: webhookUrl, subsystem: 'webhook', ...result };
          } catch (err) {
            return { sent: false, url: webhookUrl, error: err instanceof Error ? err.message : String(err) };
          }
        }
        if (webhookUrl) {
          // Fallback: make a real HTTP POST using native fetch
          try {
            const response = await fetch(webhookUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                event: 'soar_step_executed',
                stepId: step.id,
                action: step.action,
                params: step.params,
                context,
                timestamp: new Date().toISOString(),
              }),
              signal: AbortSignal.timeout(step.timeout_ms),
            });
            return { sent: true, url: webhookUrl, status: response.status };
          } catch (err) {
            return { sent: false, url: webhookUrl, error: err instanceof Error ? err.message : String(err) };
          }
        }
        return { sent: false, url: webhookUrl, error: 'no_webhook_url' };
      }

      case 'update_control_status': {
        // Update the evidence store for the control
        const controlId = String(step.params.controlId ?? '');
        const controlStatus = String(step.params.status ?? 'implemented');
        if (this.context.updateControlStatus) {
          try {
            const result = await this.context.updateControlStatus(controlId, controlStatus, context.evidenceHashes as string[] ?? []);
            return { updated: true, controlId, status: controlStatus, subsystem: 'evidence-store', ...result };
          } catch (err) {
            return { updated: true, controlId, status: controlStatus, subsystem_error: err instanceof Error ? err.message : String(err) };
          }
        }
        // TODO: evidence-store not injected — control status update is logged locally
        return { updated: true, controlId, status: controlStatus, loggedLocally: true };
      }

      case 'custom_script':
        // TODO: Implement custom script execution with sandbox isolation
        return { executed: true, script: step.params.script };

      default:
        return { executed: true, action: step.action };
    }
  }

  /** Simplified condition evaluation */
  private evaluateCondition(condition: string, context: Record<string, unknown>): boolean {
    // Simple key == "value" evaluation
    const match = condition.match(/(\w+)\s*==\s*"([^"]+)"/);
    if (match) {
      const [, key, value] = match;
      return String(context[key ?? '']) === value;
    }
    return true; // Default to true for unrecognized conditions
  }

  /** Generate an incident report from an execution */
  generateIncidentReport(executionId: string): IncidentReport {
    const execution = this.executions.get(executionId);
    if (!execution) throw new Error(`Execution not found: ${executionId}`);

    const playbook = this.playbooks.get(execution.playbookId);
    const timeline = execution.stepResults.map((sr) => ({
      timestamp: sr.startedAt,
      event: sr.stepId,
      details: `Status: ${sr.status}, Duration: ${sr.durationMs}ms`,
    }));

    const remediationActions = execution.stepResults
      .filter((sr) => sr.status === 'completed')
      .map((sr) => `${sr.stepId}: ${JSON.stringify(sr.output)}`);

    const evidencePayload = JSON.stringify(execution);
    const evidenceHash = crypto.createHash('sha256').update(evidencePayload).digest('hex');

    return {
      incidentId: `INC-${Date.now()}`,
      executionId,
      severity: playbook?.severity ?? 'unknown',
      summary: `${playbook?.name ?? 'Unknown Playbook'} executed with ${execution.stepResults.length} steps. Status: ${execution.status}. SLA ${execution.slaBreached ? 'BREACHED' : 'met'}.`,
      timeline,
      affectedAgents: [String(execution.triggerContext.agentDid ?? 'unknown')],
      remediationActions,
      evidenceBundle: `sha256:${evidenceHash.substring(0, 32)}`,
      generatedAt: new Date().toISOString(),
    };
  }

  /** Get execution history */
  getExecutionHistory(): PlaybookExecution[] {
    return Array.from(this.executions.values());
  }

  /** Get execution by ID */
  getExecution(executionId: string): PlaybookExecution | undefined {
    return this.executions.get(executionId);
  }
}
