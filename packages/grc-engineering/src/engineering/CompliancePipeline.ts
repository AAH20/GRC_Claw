import { createHash } from 'node:crypto';
import type {
  GrcConfig,
  PipelineStageConfig,
  PipelineStageName,
  PipelineRun,
  PipelineStageResult,
  PipelineEvidence,
  PipelineRunStatus,
  StageFinding,
  AuditEntry,
} from '../types.js';
import { EvidenceStore } from '@grc-claw/evidence';

// ── Stage handler interface ────────────────────────────────────────────────

export interface StageHandler {
  name: PipelineStageName;
  run(ctx: StageContext): Promise<StageResult>;
}

export interface StageContext {
  config: GrcConfig;
  runId: string;
  stageName: PipelineStageName;
  previousResults: PipelineStageResult[];
  evidenceStore: EvidenceStore;
}

export interface StageResult {
  status: PipelineRunStatus;
  findings: StageFinding[];
  logs: string[];
  evidence?: PipelineEvidence[];
}

// ── Default stage handlers ─────────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS = 30_000;

class LintStage implements StageHandler {
  name: PipelineStageName = 'lint';

  async run(ctx: StageContext): Promise<StageResult> {
    const findings: StageFinding[] = [];
    const logs: string[] = ['[lint] Scanning grcfile for structural issues'];

    // Validate control IDs are non-empty
    for (const ctrl of ctx.config.controls) {
      if (!ctrl.id || ctrl.id.trim().length === 0) {
        findings.push({
          ruleId: 'lint-001',
          severity: 'high',
          message: 'Control has empty ID',
        });
      }
      if (!ctrl.controlCode || ctrl.controlCode.trim().length === 0) {
        findings.push({
          ruleId: 'lint-002',
          severity: 'medium',
          message: `Control '${ctrl.id}' has empty controlCode`,
        });
      }
      // Check for duplicate IDs
      const dups = ctx.config.controls.filter((c) => c.id === ctrl.id);
      if (dups.length > 1) {
        findings.push({
          ruleId: 'lint-003',
          severity: 'critical',
          message: `Duplicate control ID: '${ctrl.id}'`,
        });
      }
    }

    // Validate evidence source IDs are unique
    const sourceIds = ctx.config.evidenceSources.map((s) => s.id);
    const uniqueSources = new Set(sourceIds);
    if (uniqueSources.size !== sourceIds.length) {
      findings.push({
        ruleId: 'lint-004',
        severity: 'high',
        message: 'Duplicate evidence source IDs detected',
      });
    }

    // Validate rule IDs are unique
    const ruleIds = ctx.config.complianceRules.map((r) => r.id);
    const uniqueRules = new Set(ruleIds);
    if (uniqueRules.size !== ruleIds.length) {
      findings.push({
        ruleId: 'lint-005',
        severity: 'high',
        message: 'Duplicate compliance rule IDs detected',
      });
    }

    logs.push(`[lint] Checked ${ctx.config.controls.length} controls, ${ctx.config.evidenceSources.length} evidence sources, ${ctx.config.complianceRules.length} rules`);

    const hasBlocking = findings.some((f) => f.severity === 'critical');
    return {
      status: hasBlocking ? 'failed' : 'passed',
      findings,
      logs,
    };
  }
}

class ValidateStage implements StageHandler {
  name: PipelineStageName = 'validate';

  async run(ctx: StageContext): Promise<StageResult> {
    const findings: StageFinding[] = [];
    const logs: string[] = ['[validate] Cross-referencing controls against frameworks'];

    // Check that every control references a bound framework
    const boundFrameworks = new Set(ctx.config.frameworks.map((f) => f.code));
    for (const ctrl of ctx.config.controls) {
      if (!boundFrameworks.has(ctrl.frameworkCode)) {
        findings.push({
          ruleId: 'val-001',
          severity: 'critical',
          message: `Control '${ctrl.id}' references unbound framework '${ctrl.frameworkCode}'`,
        });
      }
    }

    // Check evidence requirements reference valid types
    const validEvidenceTypes = new Set([
      'screenshot', 'document', 'log_excerpt', 'config_dump',
      'policy_hash', 'scan_result', 'api_response', 'manual attestation',
    ]);
    for (const ctrl of ctx.config.controls) {
      for (const req of ctrl.evidenceRequired) {
        if (!validEvidenceTypes.has(req.type)) {
          findings.push({
            ruleId: 'val-002',
            severity: 'medium',
            message: `Control '${ctrl.id}' has invalid evidence type: '${req.type}'`,
          });
        }
      }
    }

    // Validate compliance rules reference existing controls
    const controlIds = new Set(ctx.config.controls.map((c) => c.id));
    for (const rule of ctx.config.complianceRules) {
      for (const cid of rule.controlIds) {
        if (!controlIds.has(cid)) {
          findings.push({
            ruleId: 'val-003',
            severity: 'high',
            message: `Rule '${rule.id}' references non-existent control '${cid}'`,
          });
        }
      }
    }

    // Validate schedule syntax (basic: must be cron-like or empty)
    for (const ctrl of ctx.config.controls) {
      if (ctrl.schedule) {
        const parts = ctrl.schedule.trim().split(/\s+/);
        if (parts.length < 5 || parts.length > 6) {
          findings.push({
            ruleId: 'val-004',
            severity: 'low',
            message: `Control '${ctrl.id}' has suspicious schedule format: '${ctrl.schedule}'`,
          });
        }
      }
    }

    logs.push(`[validate] Cross-referenced ${ctx.config.controls.length} controls against ${ctx.config.frameworks.length} frameworks`);

    const hasBlocking = findings.some((f) => f.severity === 'critical');
    return {
      status: hasBlocking ? 'failed' : 'passed',
      findings,
      logs,
    };
  }
}

class TestStage implements StageHandler {
  name: PipelineStageName = 'test';

  async run(ctx: StageContext): Promise<StageResult> {
    const findings: StageFinding[] = [];
    const logs: string[] = ['[test] Running compliance rule tests'];

    // Simulate running each compliance rule against the config
    for (const rule of ctx.config.complianceRules) {
      const violation = this.evaluateRule(rule, ctx.config);
      if (violation) {
        findings.push({
          ruleId: rule.id,
          severity: rule.severity,
          message: violation,
        });
        logs.push(`[test] Rule '${rule.id}' VIOLATION: ${violation}`);
      } else {
        logs.push(`[test] Rule '${rule.id}' passed`);
      }
    }

    // Check evidence freshness
    for (const ctrl of ctx.config.controls) {
      for (const req of ctrl.evidenceRequired) {
        if (req.maxAgeDays && req.maxAgeDays > 365) {
          findings.push({
            ruleId: `test-evidence-${ctrl.id}`,
            severity: 'low',
            message: `Control '${ctrl.id}' requires evidence older than ${req.maxAgeDays} days (unusual)`,
          });
        }
      }
    }

    logs.push(`[test] Evaluated ${ctx.config.complianceRules.length} rules`);

    const hasBlocking = findings.some((f) => f.severity === 'critical');
    return {
      status: hasBlocking ? 'failed' : 'passed',
      findings,
      logs,
    };
  }

  private evaluateRule(rule: import('../types.js').ComplianceRule, config: GrcConfig): string | null {
    const { condition } = rule;
    switch (rule.ruleType) {
      case 'control_status': {
        const targetControls = config.controls.filter((c) => rule.controlIds.includes(c.id));
        const failedControls = targetControls.filter((c) => c.implementationStatus === 'failed');
        if (failedControls.length > 0) {
          return `${failedControls.length} control(s) in failed status: ${failedControls.map((c) => c.id).join(', ')}`;
        }
        return null;
      }
      case 'evidence_freshness': {
        const targetControls = config.controls.filter((c) => rule.controlIds.includes(c.id));
        const noEvidence = targetControls.filter((c) => c.evidenceRequired.length === 0);
        if (noEvidence.length > 0) {
          return `Controls missing evidence requirements: ${noEvidence.map((c) => c.id).join(', ')}`;
        }
        return null;
      }
      case 'config_check': {
        if (condition.field && condition.operator) {
          const val = this.resolveField(condition.field, config);
          if (!this.evaluateCondition(val, condition.operator, condition.value)) {
            return `Config check failed: ${condition.field} ${condition.operator} ${JSON.stringify(condition.value)}`;
          }
        }
        return null;
      }
      default:
        return null;
    }
  }

  private resolveField(field: string, config: GrcConfig): unknown {
    const parts = field.split('.');
    let current: unknown = config;
    for (const part of parts) {
      if (typeof current !== 'object' || current === null) return undefined;
      current = (current as Record<string, unknown>)[part];
    }
    return current;
  }

  private evaluateCondition(value: unknown, operator: string, expected: unknown): boolean {
    switch (operator) {
      case 'equals': return value === expected;
      case 'not_equals': return value !== expected;
      case 'greater_than': return typeof value === 'number' && typeof expected === 'number' && value > expected;
      case 'less_than': return typeof value === 'number' && typeof expected === 'number' && value < expected;
      case 'contains': return typeof value === 'string' && typeof expected === 'string' && value.includes(expected);
      case 'is_empty': return value === undefined || value === null || value === '';
      case 'is_not_empty': return value !== undefined && value !== null && value !== '';
      default: return true;
    }
  }
}

class DeployStage implements StageHandler {
  name: PipelineStageName = 'deploy';

  async run(ctx: StageContext): Promise<StageResult> {
    const logs: string[] = ['[deploy] Applying config to live environment'];
    const findings: StageFinding[] = [];

    // In a real implementation, this would push config to the live GRC store
    // Here we generate evidence from the deployment
    const evidence: PipelineEvidence[] = [];

    for (const ctrl of ctx.config.controls) {
      if (ctrl.autoCollect) {
        const hash = createHash('sha256')
          .update(JSON.stringify({ control: ctrl.id, timestamp: Date.now() }))
          .digest('hex');

        const ev: PipelineEvidence = {
          id: `pev-${hash.slice(0, 16)}`,
          stage: 'deploy',
          controlId: ctrl.id,
          contentHash: hash,
          collectedAt: new Date().toISOString(),
          uri: `pipeline://${ctx.runId}/deploy/${ctrl.id}`,
        };
        evidence.push(ev);
        ctx.evidenceStore.attach({
          controlId: ctrl.id,
          tenantId: ctx.config.org.tenantId,
          uri: ev.uri,
          collectedAt: ev.collectedAt,
          lineage: { source: 'compliance_pipeline' },
        });
      }
    }

    logs.push(`[deploy] Deployed ${ctx.config.controls.length} controls, collected ${evidence.length} evidence items`);

    return {
      status: 'passed',
      findings,
      logs,
      evidence,
    };
  }
}

class MonitorStage implements StageHandler {
  name: PipelineStageName = 'monitor';

  async run(ctx: StageContext): Promise<StageResult> {
    const logs: string[] = ['[monitor] Post-deploy monitoring check'];
    const findings: StageFinding[] = [];

    // Check that all required evidence sources are configured
    const configuredSourceTypes = new Set(ctx.config.evidenceSources.map((s) => s.type));
    for (const ctrl of ctx.config.controls) {
      if (ctrl.autoCollect && !configuredSourceTypes.has('custom_webhook') && !configuredSourceTypes.has('cloud_api')) {
        findings.push({
          ruleId: `mon-${ctrl.id}`,
          severity: 'medium',
          message: `Control '${ctrl.id}' has autoCollect but no matching evidence source type`,
        });
      }
    }

    // Verify branch protection is set if rules are strict
    const criticalRules = ctx.config.complianceRules.filter((r) => r.severity === 'critical');
    if (criticalRules.length > 0 && !ctx.config.branchProtection) {
      findings.push({
        ruleId: 'mon-bp',
        severity: 'high',
        message: `${criticalRules.length} critical rules defined but no branch protection configured`,
      });
    }

    logs.push(`[monitor] Monitoring check complete: ${findings.length} findings`);

    return {
      status: findings.some((f) => f.severity === 'critical') ? 'failed' : 'passed',
      findings,
      logs,
    };
  }
}

// ── CompliancePipeline class ───────────────────────────────────────────────

export class CompliancePipeline {
  private stages: Map<PipelineStageName, StageHandler> = new Map();
  private runs: PipelineRun[] = [];
  private evidenceStore: EvidenceStore;
  private auditEntries: AuditEntry[] = [];
  private stageConfigs: PipelineStageConfig[];

  constructor(evidenceStore?: EvidenceStore) {
    this.evidenceStore = evidenceStore ?? new EvidenceStore();
    this.stageConfigs = [
      { name: 'lint', enabled: true },
      { name: 'validate', enabled: true },
      { name: 'test', enabled: true },
      { name: 'deploy', enabled: true },
      { name: 'monitor', enabled: true },
    ];

    // Register default handlers
    this.stages.set('lint', new LintStage());
    this.stages.set('validate', new ValidateStage());
    this.stages.set('test', new TestStage());
    this.stages.set('deploy', new DeployStage());
    this.stages.set('monitor', new MonitorStage());
  }

  /**
   * Register a custom stage handler.
   */
  registerStage(handler: StageHandler): void {
    this.stages.set(handler.name, handler);
  }

  /**
   * Configure pipeline stages.
   */
  configure(configs: PipelineStageConfig[]): void {
    this.stageConfigs = configs;
  }

  /**
   * Get the ordered list of enabled stages.
   */
  getEnabledStages(): PipelineStageName[] {
    const stageOrder: PipelineStageName[] = ['lint', 'validate', 'test', 'deploy', 'monitor'];
    return stageOrder.filter((name) => {
      const cfg = this.stageConfigs.find((s) => s.name === name);
      return cfg?.enabled ?? true;
    });
  }

  /**
   * Run the full pipeline for a GRC config.
   */
  async run(config: GrcConfig, triggeredBy: string = 'system'): Promise<PipelineRun> {
    const runId = `run-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    const enabledStages = this.getEnabledStages();

    const pipelineRun: PipelineRun = {
      id: runId,
      pipelineName: 'grc-compliance-pipeline',
      triggeredBy,
      startedAt: new Date().toISOString(),
      status: 'running',
      stages: [],
      evidence: [],
    };

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'pipeline.run_started',
      actor: triggeredBy,
      targetType: 'pipeline',
      targetId: runId,
      after: { pipelineName: pipelineRun.pipelineName },
    });

    for (const stageName of enabledStages) {
      const handler = this.stages.get(stageName);
      if (!handler) {
        pipelineRun.stages.push({
          stage: stageName,
          status: 'failed',
          startedAt: new Date().toISOString(),
          completedAt: new Date().toISOString(),
          durationMs: 0,
          findings: [{ ruleId: 'internal', severity: 'critical', message: `No handler for stage '${stageName}'` }],
          logs: [`[error] No handler registered for stage '${stageName}'`],
        });
        pipelineRun.status = 'failed';
        break;
      }

      const stageConfig = this.stageConfigs.find((s) => s.name === stageName);
      const timeoutMs = stageConfig?.timeoutMs ?? DEFAULT_TIMEOUT_MS;

      const stageStart = Date.now();
      const stageResult: PipelineStageResult = {
        stage: stageName,
        status: 'running',
        startedAt: new Date().toISOString(),
        findings: [],
        logs: [],
      };

      try {
        const result = await Promise.race([
          handler.run({
            config,
            runId,
            stageName,
            previousResults: pipelineRun.stages,
            evidenceStore: this.evidenceStore,
          }),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error(`Stage '${stageName}' timed out after ${timeoutMs}ms`)), timeoutMs),
          ),
        ]);

        stageResult.status = result.status;
        stageResult.findings = result.findings;
        stageResult.logs = result.logs;
        stageResult.completedAt = new Date().toISOString();
        stageResult.durationMs = Date.now() - stageStart;

        if (result.evidence) {
          pipelineRun.evidence.push(...result.evidence);
        }

        this.auditEntries.push({
          id: `audit-${Date.now().toString(36)}`,
          timestamp: new Date().toISOString(),
          action: result.status === 'passed' ? 'pipeline.stage_passed' : 'pipeline.stage_failed',
          actor: triggeredBy,
          targetType: 'pipeline',
          targetId: runId,
          after: { stage: stageName, status: result.status },
        });
      } catch (err) {
        stageResult.status = 'failed';
        stageResult.completedAt = new Date().toISOString();
        stageResult.durationMs = Date.now() - stageStart;
        stageResult.logs.push(`[error] ${err instanceof Error ? err.message : String(err)}`);
        stageResult.findings.push({
          ruleId: 'internal',
          severity: 'critical',
          message: `Stage '${stageName}' crashed: ${err instanceof Error ? err.message : String(err)}`,
        });
        pipelineRun.status = 'failed';

        this.auditEntries.push({
          id: `audit-${Date.now().toString(36)}`,
          timestamp: new Date().toISOString(),
          action: 'pipeline.stage_failed',
          actor: triggeredBy,
          targetType: 'pipeline',
          targetId: runId,
          after: { stage: stageName, status: 'failed', error: err instanceof Error ? err.message : String(err) },
        });
        break;
      }

      pipelineRun.stages.push(stageResult);

      if (stageResult.status === 'failed' && !stageConfig?.continueOnFailure) {
        pipelineRun.status = 'failed';
        break;
      }
    }

    if (pipelineRun.status === 'running') {
      pipelineRun.status = 'passed';
    }

    pipelineRun.completedAt = new Date().toISOString();

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'pipeline.run_completed',
      actor: triggeredBy,
      targetType: 'pipeline',
      targetId: runId,
      after: { status: pipelineRun.status, stagesCompleted: pipelineRun.stages.length },
    });

    this.runs.push(pipelineRun);
    return pipelineRun;
  }

  /**
   * Get all pipeline runs.
   */
  getRuns(): PipelineRun[] {
    return [...this.runs];
  }

  /**
   * Get a specific pipeline run by ID.
   */
  getRun(id: string): PipelineRun | undefined {
    return this.runs.find((r) => r.id === id);
  }

  /**
   * Get the audit trail for pipeline operations.
   */
  getAuditEntries(): AuditEntry[] {
    return [...this.auditEntries];
  }

  /**
   * Get the evidence store used by this pipeline.
   */
  getEvidenceStore(): EvidenceStore {
    return this.evidenceStore;
  }
}
