import type { DriftEvent, RemediationPlan, RemediationStep, RemediationAction, RemediationResult } from "../types.js";

export interface RemediationEngineConfig {
  maxAutoRemediationSeverity: "low" | "medium" | "high" | "critical";
  requireApprovalAbove: "low" | "medium" | "high" | "critical";
  timeoutMs: number;
  retryAttempts: number;
}

const SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"];

const DEFAULT_ENGINE_CONFIG: RemediationEngineConfig = {
  maxAutoRemediationSeverity: "medium",
  requireApprovalAbove: "low",
  timeoutMs: 30_000,
  retryAttempts: 3,
};

export interface RemediationExecutor {
  execute(script: string, context: Record<string, unknown>): Promise<RemediationResult>;
}

export class AutoRemediationEngine {
  private plans: Map<string, RemediationPlan> = new Map();
  private executor: RemediationExecutor;
  private config: RemediationEngineConfig;

  constructor(executor: RemediationExecutor, config: Partial<RemediationEngineConfig> = {}) {
    this.executor = executor;
    this.config = { ...DEFAULT_ENGINE_CONFIG, ...config };
  }

  canAutoRemediate(drift: DriftEvent): boolean {
    if (!drift.remediable) return false;
    const driftLevel = SEVERITY_ORDER.indexOf(drift.severity);
    const maxLevel = SEVERITY_ORDER.indexOf(this.config.maxAutoRemediationSeverity);
    return driftLevel <= maxLevel;
  }

  requiresApproval(drift: DriftEvent): boolean {
    const driftLevel = SEVERITY_ORDER.indexOf(drift.severity);
    const approvalLevel = SEVERITY_ORDER.indexOf(this.config.requireApprovalAbove);
    return driftLevel > approvalLevel;
  }

  createRemediationPlan(drift: DriftEvent): RemediationPlan {
    const actions = this.determineActions(drift);
    const plan: RemediationPlan = {
      id: `remedy-${drift.id}`,
      tenantId: drift.tenantId,
      driftEventId: drift.id,
      controlId: drift.controlId,
      actions,
      createdAt: new Date().toISOString(),
      status: "pending",
    };
    this.plans.set(plan.id, plan);
    return plan;
  }

  private determineActions(drift: DriftEvent): RemediationStep[] {
    const steps: RemediationStep[] = [];

    switch (drift.driftType) {
      case "evidence_missing":
        steps.push(
          { order: 1, action: "alert", description: "Notify evidence owner of missing evidence", automated: true, requiresApproval: false, executed: false },
          { order: 2, action: "escalate", description: "Escalate to compliance officer if not resolved in 24h", automated: false, requiresApproval: true, executed: false }
        );
        break;
      case "evidence_tampered":
        steps.push(
          { order: 1, action: "quarantine", description: "Quarantine affected evidence and lock control", automated: true, requiresApproval: false, executed: false },
          { order: 2, action: "block", description: "Block all write access to evidence store", automated: true, requiresApproval: false, executed: false },
          { order: 3, action: "escalate", description: "Immediate escalation to CISO", automated: true, requiresApproval: false, executed: false }
        );
        break;
      case "config_changed":
        steps.push(
          { order: 1, action: "rollback", description: "Rollback configuration to last known good state", automated: true, requiresApproval: true, executed: false },
          { order: 2, action: "log_evidence", description: "Log remediation evidence with timestamp", automated: true, requiresApproval: false, executed: false }
        );
        break;
      case "control_disabled":
        steps.push(
          { order: 1, action: "alert", description: "Alert control owner to re-enable control", automated: true, requiresApproval: false, executed: false },
          { order: 2, action: "auto_fix", description: "Attempt automatic re-enablement", automated: true, requiresApproval: true, executed: false }
        );
        break;
      case "policy_violation":
        steps.push(
          { order: 1, action: "block", description: "Block violating operation", automated: true, requiresApproval: false, executed: false },
          { order: 2, action: "alert", description: "Notify security team", automated: true, requiresApproval: false, executed: false },
          { order: 3, action: "escalate", description: "Escalate to management if severe", automated: false, requiresApproval: true, executed: false }
        );
        break;
      default:
        steps.push(
          { order: 1, action: "alert", description: `Alert on ${drift.driftType} drift`, automated: true, requiresApproval: false, executed: false }
        );
    }

    return steps;
  }

  async executeRemediation(planId: string): Promise<RemediationResult> {
    const plan = this.plans.get(planId);
    if (!plan) return { success: false, message: "Plan not found", actionsTaken: [] };

    plan.status = "in_progress";
    plan.executedAt = new Date().toISOString();
    const actionsTaken: string[] = [];

    for (const step of plan.actions) {
      if (step.requiresApproval) {
        step.executed = false;
        continue;
      }

      try {
        const result = await this.executor.execute(step.action, { plan, step });
        step.executed = true;
        step.executedAt = new Date().toISOString();
        step.output = result.message;
        actionsTaken.push(step.action);

        if (!result.success) {
          plan.status = "failed";
          plan.result = { success: false, message: `Failed at step ${step.order}: ${result.message}`, actionsTaken };
          return plan.result;
        }
      } catch (error) {
        step.output = error instanceof Error ? error.message : "Unknown error";
        plan.status = "failed";
        plan.result = { success: false, message: `Error at step ${step.order}: ${step.output}`, actionsTaken };
        return plan.result;
      }
    }

    plan.status = "completed";
    plan.completedAt = new Date().toISOString();
    plan.result = { success: true, message: "Remediation completed successfully", actionsTaken };
    return plan.result;
  }

  getPlan(planId: string): RemediationPlan | undefined {
    return this.plans.get(planId);
  }

  getPlansForDrift(driftId: string): RemediationPlan[] {
    return Array.from(this.plans.values()).filter((p) => p.driftEventId === driftId);
  }
}
