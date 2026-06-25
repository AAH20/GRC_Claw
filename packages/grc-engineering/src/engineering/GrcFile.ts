import { createHash } from 'node:crypto';
import type {
  GrcConfig,
  GrcPlan,
  GrcPlanChange,
  GrcDiff,
  DiffSummary,
  ValidationError,
  ChangeImpact,
  AuditEntry,
  AuditTrail,
  ControlDefinition,
  EvidenceSource,
  ComplianceRule,
  GrcFrameworkBinding,
} from '../types.js';
import type { ComplianceControl } from '@grc-claw/core';
import { listFrameworkPacks } from '@grc-claw/frameworks';

// ── Schema definition ─────────────────────────────────────────────────────

interface SchemaField {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required?: boolean;
  minItems?: number;
  enum?: readonly string[];
  fields?: Record<string, SchemaField>;
  itemSchema?: SchemaField;
}

const GRC_CONFIG_SCHEMA: Record<string, SchemaField> = {
  version: { type: 'string', required: true, enum: ['1.0'] },
  org: {
    type: 'object',
    required: true,
    fields: {
      name: { type: 'string', required: true },
      tenantId: { type: 'number', required: true },
      slug: { type: 'string', required: true },
      complianceEmail: { type: 'string' },
    },
  },
  frameworks: { type: 'array', required: true, minItems: 1 },
  controls: { type: 'array', required: true, minItems: 0 },
  evidenceSources: { type: 'array', required: true, minItems: 0 },
  complianceRules: { type: 'array', required: true, minItems: 0 },
  pipelines: { type: 'array' },
  branchProtection: { type: 'object' },
};

// ── GrcFile class ─────────────────────────────────────────────────────────

export class GrcFile {
  private config: GrcConfig | null = null;
  private validationErrors: ValidationError[] = [];
  private auditTrail: AuditEntry[] = [];
  private configHash = '';

  /**
   * Parse a GRC config from a JSON string (representing grcfile.json/yaml/toml).
   */
  parse(raw: string, format: 'json' | 'yaml' | 'toml' = 'json'): GrcConfig {
    let parsed: unknown;
    if (format === 'json') {
      parsed = JSON.parse(raw);
    } else {
      throw new Error(`Format '${format}' is not yet supported. Use 'json' for now.`);
    }

    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      throw new Error('GRC config must be a JSON object');
    }

    this.config = parsed as GrcConfig;
    this.configHash = this.hashConfig(this.config);

    this.addAuditEntry('config.create', 'system', 'config', 'grcfile', undefined, this.config);

    return this.config;
  }

  /**
   * Validate the parsed config against the GRC schema.
   */
  validate(config?: GrcConfig): ValidationError[] {
    const cfg = config ?? this.config;
    if (!cfg) {
      return [{ path: '$', message: 'No config loaded. Call parse() first.', severity: 'error' }];
    }

    const errors: ValidationError[] = [];
    this.validateObject(cfg, GRC_CONFIG_SCHEMA, '$', errors);

    // Cross-field validations
    this.validateFrameworkBindings(cfg, errors);
    this.validateControlReferences(cfg, errors);
    this.validateEvidenceSourceRefs(cfg, errors);

    this.validationErrors = errors;
    this.addAuditEntry('config.validate', 'system', 'config', 'grcfile', undefined, {
      errorCount: errors.filter((e) => e.severity === 'error').length,
      warningCount: errors.filter((e) => e.severity === 'warning').length,
    });

    return errors;
  }

  /**
   * Generate a plan: diff between the current desired config and a snapshot of live controls.
   */
  plan(liveControls: ComplianceControl[] = []): GrcPlan {
    if (!this.config) {
      throw new Error('No config loaded. Call parse() first.');
    }

    const changes: GrcPlanChange[] = [];

    // Map live controls by ID for lookup
    const liveMap = new Map(liveControls.map((c) => [c.id, c]));
    const desiredMap = new Map(this.config.controls.map((c) => [c.id, c]));

    // Additions: controls in desired but not in live
    for (const ctrl of this.config.controls) {
      if (!liveMap.has(ctrl.id)) {
        changes.push({
          type: 'control',
          id: ctrl.id,
          after: this.toControlSnapshot(ctrl),
          impact: this.classifyImpact(ctrl),
        });
      }
    }

    // Deletions: controls in live but not in desired
    for (const [id, liveCtrl] of liveMap) {
      if (!desiredMap.has(id)) {
        changes.push({
          type: 'control',
          id,
          before: liveCtrl,
          impact: 'medium',
        });
      }
    }

    // Modifications: controls in both, check for drift
    for (const [id, desiredCtrl] of desiredMap) {
      const liveCtrl = liveMap.get(id);
      if (liveCtrl) {
        const diffs = this.detectControlDrift(desiredCtrl, liveCtrl);
        if (diffs.length > 0) {
          changes.push({
            type: 'control',
            id,
            before: liveCtrl,
            after: this.toControlSnapshot(desiredCtrl),
            impact: this.classifyImpact(desiredCtrl),
          });
        }
      }
    }

    const additions = changes.filter((c) => !c.before);
    const deletions = changes.filter((c) => !c.after);
    const modifications = changes.filter((c) => c.before && c.after);

    const plan: GrcPlan = {
      id: `plan-${Date.now().toString(36)}`,
      createdAt: new Date().toISOString(),
      configHash: this.configHash,
      additions,
      modifications,
      deletions,
      validationErrors: this.validationErrors,
      isValid: this.validationErrors.filter((e) => e.severity === 'error').length === 0,
    };

    this.addAuditEntry('config.update', 'system', 'config', 'grcfile', undefined, {
      planId: plan.id,
      changeCount: changes.length,
    });

    return plan;
  }

  /**
   * Apply a plan: produce the target state that the plan would create.
   */
  apply(plan: GrcPlan): GrcConfig {
    if (!this.config) {
      throw new Error('No config loaded.');
    }
    if (!plan.isValid) {
      throw new Error(`Cannot apply plan with ${plan.validationErrors.filter((e) => e.severity === 'error').length} validation errors.`);
    }

    // Clone config
    const result: GrcConfig = JSON.parse(JSON.stringify(this.config));

    // Apply additions (no before means it's new)
    for (const change of plan.additions) {
      if (change.type === 'control' && change.after) {
        const ctrl = change.after as ControlDefinition;
        if (!result.controls.find((c) => c.id === ctrl.id)) {
          result.controls.push(ctrl);
        }
      }
    }

    // Apply modifications
    for (const change of plan.modifications) {
      if (change.type === 'control' && change.after) {
        const idx = result.controls.findIndex((c) => c.id === change.id);
        if (idx >= 0) {
          result.controls[idx] = change.after as ControlDefinition;
        }
      }
    }

    // Apply deletions
    for (const change of plan.deletions) {
      if (change.type === 'control') {
        result.controls = result.controls.filter((c) => c.id !== change.id);
      }
    }

    this.config = result;
    this.configHash = this.hashConfig(result);

    this.addAuditEntry('config.update', 'system', 'config', 'grcfile', undefined, {
      appliedPlanId: plan.id,
    });

    return result;
  }

  /**
   * Generate a diff summary between this config and a set of live controls.
   */
  diff(liveControls: ComplianceControl[]): GrcDiff {
    const plan = this.plan(liveControls);
    const summary: DiffSummary = {
      controlsAdded: plan.additions.length,
      controlsModified: plan.modifications.length,
      controlsRemoved: plan.deletions.length,
      evidenceSourcesChanged: 0,
      rulesChanged: 0,
      pipelinesChanged: 0,
      overallRisk: this.computeOverallRisk([...plan.additions, ...plan.modifications, ...plan.deletions]),
    };

    return {
      summary,
      changes: [...plan.additions, ...plan.modifications, ...plan.deletions],
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Export the full audit trail.
   */
  getAuditTrail(): AuditTrail {
    return { entries: [...this.auditTrail] };
  }

  /**
   * Get the current config hash.
   */
  getConfigHash(): string {
    return this.configHash;
  }

  getConfig(): GrcConfig | null {
    return this.config ? JSON.parse(JSON.stringify(this.config)) : null;
  }

  // ── Private helpers ───────────────────────────────────────────────────────

  private validateObject(
    obj: unknown,
    schema: Record<string, SchemaField>,
    basePath: string,
    errors: ValidationError[],
  ): void {
    const record = obj as Record<string, unknown>;
    for (const [key, field] of Object.entries(schema)) {
      const path = `${basePath}.${key}`;
      const value = record[key];

      if (field.required && (value === undefined || value === null)) {
        errors.push({ path, message: `Required field '${key}' is missing`, severity: 'error' });
        continue;
      }

      if (value === undefined || value === null) continue;

      switch (field.type) {
        case 'string':
          if (typeof value !== 'string') {
            errors.push({ path, message: `Expected string, got ${typeof value}`, severity: 'error' });
          } else if (field.enum && !field.enum.includes(value)) {
            errors.push({ path, message: `Value '${value}' not in allowed values: ${field.enum.join(', ')}`, severity: 'error' });
          }
          break;
        case 'number':
          if (typeof value !== 'number') {
            errors.push({ path, message: `Expected number, got ${typeof value}`, severity: 'error' });
          }
          break;
        case 'boolean':
          if (typeof value !== 'boolean') {
            errors.push({ path, message: `Expected boolean, got ${typeof value}`, severity: 'error' });
          }
          break;
        case 'array':
          if (!Array.isArray(value)) {
            errors.push({ path, message: `Expected array, got ${typeof value}`, severity: 'error' });
          } else if (field.minItems !== undefined && value.length < field.minItems) {
            errors.push({ path, message: `Array must have at least ${field.minItems} items, got ${value.length}`, severity: 'error' });
          }
          break;
        case 'object':
          if (typeof value !== 'object' || Array.isArray(value)) {
            errors.push({ path, message: `Expected object, got ${typeof value}`, severity: 'error' });
          } else if (field.fields) {
            this.validateObject(value as Record<string, unknown>, field.fields, path, errors);
          }
          break;
      }
    }
  }

  private validateFrameworkBindings(cfg: GrcConfig, errors: ValidationError[]): void {
    const knownFrameworks = listFrameworkPacks().map((f) => f.code);
    for (const binding of cfg.frameworks) {
      const path = `$.frameworks[${binding.code}]`;
      if (!knownFrameworks.includes(binding.code)) {
        errors.push({
          path,
          message: `Unknown framework '${binding.code}'. Known: ${knownFrameworks.join(', ')}`,
          severity: 'warning',
        });
      }
    }
  }

  private validateControlReferences(cfg: GrcConfig, errors: ValidationError[]): void {
    const frameworkCodes = new Set(cfg.frameworks.map((f) => f.code));
    for (const ctrl of cfg.controls) {
      const path = `$.controls[${ctrl.id}]`;
      if (!frameworkCodes.has(ctrl.frameworkCode)) {
        errors.push({
          path,
          message: `Control '${ctrl.id}' references unbound framework '${ctrl.frameworkCode}'`,
          severity: 'error',
        });
      }
    }
  }

  private validateEvidenceSourceRefs(cfg: GrcConfig, errors: ValidationError[]): void {
    const sourceIds = new Set(cfg.evidenceSources.map((s) => s.id));
    for (const ctrl of cfg.controls) {
      if (ctrl.autoCollect?.endpoint) {
        // Validate endpoint is a URL-like string
        try {
          new URL(ctrl.autoCollect.endpoint);
        } catch {
          errors.push({
            path: `$.controls[${ctrl.id}].autoCollect.endpoint`,
            message: `Invalid endpoint URL: ${ctrl.autoCollect.endpoint}`,
            severity: 'warning',
          });
        }
      }
      for (const req of ctrl.evidenceRequired) {
        // No cross-ref to source IDs currently, but validate structure
        if (req.minimumCount < 0) {
          errors.push({
            path: `$.controls[${ctrl.id}].evidenceRequired`,
            message: `minimumCount cannot be negative`,
            severity: 'error',
          });
        }
      }
    }
  }

  private detectControlDrift(desired: ControlDefinition, live: ComplianceControl): string[] {
    const diffs: string[] = [];
    if (desired.controlCode !== live.controlCode) diffs.push('controlCode');
    if (desired.title !== live.title) diffs.push('title');
    if (desired.frameworkCode !== live.frameworkCode) diffs.push('frameworkCode');
    if (desired.domain && desired.domain !== live.domain) diffs.push('domain');
    if (desired.implementationStatus !== live.orgStatus) diffs.push('status');
    return diffs;
  }

  private toControlSnapshot(ctrl: ControlDefinition): ComplianceControl {
    return {
      id: ctrl.id,
      controlCode: ctrl.controlCode,
      title: ctrl.title,
      frameworkCode: ctrl.frameworkCode,
      domain: ctrl.domain,
      orgStatus: ctrl.implementationStatus,
    };
  }

  private classifyImpact(ctrl: ControlDefinition): ChangeImpact {
    if (ctrl.evidenceRequired.length === 0) return 'low';
    if (ctrl.implementationStatus === 'failed') return 'critical';
    if (ctrl.implementationStatus === 'not_started') return 'high';
    return 'medium';
  }

  private computeOverallRisk(changes: GrcPlanChange[]): ChangeImpact {
    const impactOrder: ChangeImpact[] = ['none', 'low', 'medium', 'high', 'critical'];
    let maxImpact: ChangeImpact = 'none';
    for (const change of changes) {
      if (impactOrder.indexOf(change.impact) > impactOrder.indexOf(maxImpact)) {
        maxImpact = change.impact;
      }
    }
    return maxImpact;
  }

  private hashConfig(config: GrcConfig): string {
    const serialized = JSON.stringify(config, Object.keys(config).sort());
    return createHash('sha256').update(serialized).digest('hex');
  }

  private addAuditEntry(
    action: AuditEntry['action'],
    actor: string,
    targetType: AuditEntry['targetType'],
    targetId: string,
    before: unknown,
    after: unknown,
  ): void {
    this.auditTrail.push({
      id: `audit-${Date.now().toString(36)}-${this.auditTrail.length}`,
      timestamp: new Date().toISOString(),
      action,
      actor,
      targetType,
      targetId,
      before,
      after,
    });
  }
}
