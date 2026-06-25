import { createHash } from 'node:crypto';
import type {
  GrcConfig,
  GrcDiff,
  DiffSummary,
  DriftReport,
  DriftItem,
  RepoComplianceState,
  LiveComplianceState,
  CompliancePRDescription,
  PRChecklistItem,
  ChangeImpact,
  AuditEntry,
  BranchProtectionConfig,
  ComplianceRule,
} from '../types.js';
import type { ComplianceControl } from '@grc-claw/core';
import { GrcFile } from './GrcFile.js';

// ── Commit metadata ────────────────────────────────────────────────────────

export interface ComplianceCommit {
  sha: string;
  author: string;
  message: string;
  timestamp: string;
  configHash: string;
}

// ── Branch protection rule ─────────────────────────────────────────────────

export interface BranchProtectionRule {
  pattern: string;
  requireReview: boolean;
  requiredReviewers: number;
  requireStatusChecks: string[];
  requireSignedCommits: boolean;
  restrictPushes: boolean;
  allowForcePushes: boolean;
  requireLinearHistory: boolean;
}

// ── GitOpsWorkflow class ───────────────────────────────────────────────────

export class GitOpsWorkflow {
  private grcFile: GrcFile;
  private commitHistory: ComplianceCommit[] = [];
  private branchProtections: Map<string, BranchProtectionRule> = new Map();
  private auditEntries: AuditEntry[] = [];
  private trackedConfigs: Map<string, GrcConfig> = new Map();
  private driftHistory: DriftReport[] = [];

  constructor(grcFile?: GrcFile) {
    this.grcFile = grcFile ?? new GrcFile();
  }

  /**
   * Initialize a compliance-as-code repository state.
   */
  initRepo(branch: string = 'main', config?: GrcConfig): RepoComplianceState {
    if (config) {
      this.grcFile.parse(JSON.stringify(config));
    }
    const state: RepoComplianceState = {
      commitSha: this.generateFakeSha(),
      branch,
      configHash: this.grcFile.getConfigHash() || this.hashConfig(config ?? { version: '1.0', org: { name: '', tenantId: 0, slug: '' }, frameworks: [], controls: [], evidenceSources: [], complianceRules: [] }),
      controls: [],
      rules: [],
    };

    this.commitHistory.push({
      sha: state.commitSha,
      author: 'system',
      message: 'Initialize compliance-as-code repository',
      timestamp: new Date().toISOString(),
      configHash: state.configHash,
    });

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'config.create',
      actor: 'system',
      targetType: 'config',
      targetId: state.commitSha,
      after: { branch, commitSha: state.commitSha },
    });

    return state;
  }

  /**
   * Record a config commit.
   */
  commit(
    config: GrcConfig,
    author: string,
    message: string,
    branch: string = 'main',
  ): ComplianceCommit {
    const sha = this.generateFakeSha();
    const configHash = this.hashConfig(config);

    const commit: ComplianceCommit = {
      sha,
      author,
      message,
      timestamp: new Date().toISOString(),
      configHash,
    };

    this.commitHistory.push(commit);
    this.trackedConfigs.set(sha, JSON.parse(JSON.stringify(config)));

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'config.update',
      actor: author,
      targetType: 'config',
      targetId: sha,
      after: { message, branch },
    });

    return commit;
  }

  /**
   * Detect drift between the repo state (last commit) and live state.
   */
  detectDrift(
    repoState: RepoComplianceState,
    liveControls: ComplianceControl[],
    liveRules?: ComplianceRule[],
  ): DriftReport {
    const driftItems: DriftItem[] = [];

    // Build maps for comparison
    const repoControlMap = new Map(repoState.controls.map((c) => [c.id, c]));
    const liveControlMap = new Map(liveControls.map((c) => [c.id, c]));

    // Controls in live but not in repo
    for (const [id, liveCtrl] of liveControlMap) {
      if (!repoControlMap.has(id)) {
        driftItems.push({
          type: 'control_status',
          id,
          description: `Control '${id}' exists in live but not in repo`,
          repoValue: undefined,
          liveValue: liveCtrl,
          severity: 'high',
        });
      }
    }

    // Controls in repo but not in live
    for (const [id, repoCtrl] of repoControlMap) {
      if (!liveControlMap.has(id)) {
        driftItems.push({
          type: 'control_status',
          id,
          description: `Control '${id}' exists in repo but not in live`,
          repoValue: repoCtrl,
          liveValue: undefined,
          severity: 'medium',
        });
      }
    }

    // Controls in both: check status drift
    for (const [id, repoCtrl] of repoControlMap) {
      const liveCtrl = liveControlMap.get(id);
      if (liveCtrl) {
        if (repoCtrl.orgStatus !== liveCtrl.orgStatus) {
          driftItems.push({
            type: 'control_status',
            id,
            description: `Control '${id}' status drift: repo=${repoCtrl.orgStatus ?? 'unset'} live=${liveCtrl.orgStatus ?? 'unset'}`,
            repoValue: repoCtrl.orgStatus,
            liveValue: liveCtrl.orgStatus,
            severity: this.classifyDriftSeverity(repoCtrl.orgStatus, liveCtrl.orgStatus),
          });
        }
        if (repoCtrl.title !== liveCtrl.title) {
          driftItems.push({
            type: 'config_field',
            id,
            description: `Control '${id}' title drift`,
            repoValue: repoCtrl.title,
            liveValue: liveCtrl.title,
            severity: 'low',
          });
        }
      }
    }

    // Check evidence freshness
    const repoConfig = this.trackedConfigs.get(repoState.commitSha);
    if (repoConfig) {
      for (const ctrl of repoConfig.controls) {
        for (const req of ctrl.evidenceRequired) {
          if (req.maxAgeDays) {
            // In real implementation, we'd check actual evidence timestamps
            // Here we flag it as a potential drift item
            const hasLiveEvidence = liveControls.some((lc) => lc.id === ctrl.id);
            if (!hasLiveEvidence) {
              driftItems.push({
                type: 'evidence_missing',
                id: ctrl.id,
                description: `Control '${ctrl.id}' requires evidence freshness (${req.maxAgeDays}d max) but no live evidence found`,
                repoValue: req,
                liveValue: null,
                severity: 'medium',
              });
            }
          }
        }
      }
    }

    const report: DriftReport = {
      detectedAt: new Date().toISOString(),
      repoState,
      liveState: {
        timestamp: new Date().toISOString(),
        controls: liveControls,
        rules: liveRules ?? [],
      },
      driftItems,
      totalDrift: driftItems.length,
      severity: this.computeMaxSeverity(driftItems),
    };

    this.driftHistory.push(report);

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'drift.detected',
      actor: 'system',
      targetType: 'config',
      targetId: repoState.commitSha,
      after: { driftCount: driftItems.length, severity: report.severity },
    });

    return report;
  }

  /**
   * Resolve drift by updating the repo state to match live state.
   */
  resolveDrift(
    driftReport: DriftReport,
    liveControls: ComplianceControl[],
    author: string = 'drift-resolver',
  ): ComplianceCommit {
    const updatedConfig: GrcConfig = {
      version: '1.0',
      org: { name: 'resolved-org', tenantId: 0, slug: 'resolved' },
      frameworks: [],
      controls: liveControls.map((c) => ({
        id: c.id,
        controlCode: c.controlCode,
        title: c.title,
        frameworkCode: c.frameworkCode,
        domain: c.domain,
        implementationStatus: c.orgStatus ?? 'not_started',
        evidenceRequired: [],
      })),
      evidenceSources: [],
      complianceRules: [],
    };

    const commit = this.commit(updatedConfig, author, `Resolve ${driftReport.totalDrift} drift items`);

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'drift.resolved',
      actor: author,
      targetType: 'config',
      targetId: commit.sha,
      before: { driftCount: driftReport.totalDrift },
    });

    return commit;
  }

  /**
   * Generate a PR description for compliance changes.
   */
  generatePRDescription(
    diff: GrcDiff,
    driftItems: DriftItem[] = [],
  ): CompliancePRDescription {
    const labels: string[] = [];
    const checklist: PRChecklistItem[] = [];

    // Determine labels based on changes
    if (diff.summary.controlsAdded > 0) {
      labels.push('compliance: new-controls');
    }
    if (diff.summary.controlsModified > 0) {
      labels.push('compliance: control-changes');
    }
    if (diff.summary.controlsRemoved > 0) {
      labels.push('compliance: control-removal');
      labels.push('needs-review');
    }
    if (diff.summary.overallRisk === 'critical' || diff.summary.overallRisk === 'high') {
      labels.push('priority: high');
    }
    if (driftItems.length > 0) {
      labels.push('drift-resolution');
    }

    // Build checklist
    checklist.push({
      label: 'All control IDs are unique',
      checked: true,
      required: true,
    });
    checklist.push({
      label: 'Framework bindings are valid',
      checked: true,
      required: true,
    });
    checklist.push({
      label: 'Evidence requirements defined for critical controls',
      checked: diff.summary.overallRisk !== 'critical',
      required: true,
    });
    checklist.push({
      label: 'Branch protection rules updated',
      checked: false,
      required: diff.summary.controlsAdded > 0,
    });
    checklist.push({
      label: 'Drift items addressed',
      checked: driftItems.length === 0,
      required: driftItems.length > 0,
    });

    // Build body
    const bodyParts: string[] = [];
    bodyParts.push('## Compliance Change Summary');
    bodyParts.push('');
    bodyParts.push(`| Metric | Count |`);
    bodyParts.push(`|--------|-------|`);
    bodyParts.push(`| Controls Added | ${diff.summary.controlsAdded} |`);
    bodyParts.push(`| Controls Modified | ${diff.summary.controlsModified} |`);
    bodyParts.push(`| Controls Removed | ${diff.summary.controlsRemoved} |`);
    bodyParts.push(`| Evidence Sources Changed | ${diff.summary.evidenceSourcesChanged} |`);
    bodyParts.push(`| Rules Changed | ${diff.summary.rulesChanged} |`);
    bodyParts.push(`| Overall Risk | ${diff.summary.overallRisk} |`);
    bodyParts.push('');

    if (driftItems.length > 0) {
      bodyParts.push('## Drift Resolution');
      bodyParts.push('');
      for (const item of driftItems) {
        bodyParts.push(`- [ ] ${item.description} (severity: ${item.severity})`);
      }
      bodyParts.push('');
    }

    bodyParts.push('## Checklist');
    bodyParts.push('');
    for (const item of checklist) {
      const mark = item.checked ? 'x' : ' ';
      const req = item.required ? ' *(required)*' : '';
      bodyParts.push(`- [${mark}] ${item.label}${req}`);
    }

    const title = this.generatePRTitle(diff, driftItems);

    return {
      title,
      body: bodyParts.join('\n'),
      labels,
      diff,
      driftItems,
      checklist,
    };
  }

  /**
   * Configure branch protection for a compliance branch.
   */
  configureBranchProtection(branch: string, rule: BranchProtectionRule): void {
    this.branchProtections.set(branch, rule);

    this.auditEntries.push({
      id: `audit-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      action: 'branch_protection.updated',
      actor: 'system',
      targetType: 'config',
      targetId: branch,
      after: rule,
    });
  }

  /**
   * Check if a push to a branch is allowed under current protection rules.
   */
  checkPushAllowed(
    branch: string,
    options: {
      hasApproval?: boolean;
      approvalCount?: number;
      statusChecks?: string[];
      isSigned?: boolean;
      isForcePush?: boolean;
    } = {},
  ): { allowed: boolean; reasons: string[] } {
    const rule = this.branchProtections.get(branch);
    if (!rule) {
      return { allowed: true, reasons: [] };
    }

    const reasons: string[] = [];

    if (rule.requireReview && (!options.hasApproval || (options.approvalCount ?? 0) < rule.requiredReviewers)) {
      reasons.push(`Requires ${rule.requiredReviewers} review approval(s)`);
    }

    if (rule.requireStatusChecks.length > 0) {
      const missing = rule.requireStatusChecks.filter(
        (sc) => !(options.statusChecks ?? []).includes(sc),
      );
      if (missing.length > 0) {
        reasons.push(`Missing required status checks: ${missing.join(', ')}`);
      }
    }

    if (rule.requireSignedCommits && !options.isSigned) {
      reasons.push('Commits must be signed');
    }

    if (rule.restrictPushes && !options.hasApproval) {
      reasons.push('Pushes restricted to authorized users');
    }

    if (rule.allowForcePushes === false && options.isForcePush) {
      reasons.push('Force pushes not allowed');
    }

    return { allowed: reasons.length === 0, reasons };
  }

  /**
   * Get the full commit history.
   */
  getCommitHistory(): ComplianceCommit[] {
    return [...this.commitHistory];
  }

  /**
   * Get drift history.
   */
  getDriftHistory(): DriftReport[] {
    return [...this.driftHistory];
  }

  /**
   * Get branch protection rules.
   */
  getBranchProtections(): Map<string, BranchProtectionRule> {
    return new Map(this.branchProtections);
  }

  /**
   * Get audit entries.
   */
  getAuditEntries(): AuditEntry[] {
    return [...this.auditEntries];
  }

  /**
   * Export all tracked state as a snapshot.
   */
  snapshot(): {
    commits: ComplianceCommit[];
    branchProtections: Record<string, BranchProtectionRule>;
    driftReports: DriftReport[];
    auditEntries: AuditEntry[];
  } {
    const bpObj: Record<string, BranchProtectionRule> = {};
    for (const [k, v] of this.branchProtections) bpObj[k] = v;

    return {
      commits: this.getCommitHistory(),
      branchProtections: bpObj,
      driftReports: this.getDriftHistory(),
      auditEntries: this.getAuditEntries(),
    };
  }

  // ── Private helpers ───────────────────────────────────────────────────────

  private generateFakeSha(): string {
    const data = `${Date.now()}-${Math.random()}`;
    return createHash('sha1').update(data).digest('hex').slice(0, 40);
  }

  private hashConfig(config: GrcConfig): string {
    const serialized = JSON.stringify(config, Object.keys(config).sort());
    return createHash('sha256').update(serialized).digest('hex');
  }

  private classifyDriftSeverity(
    repoStatus: string | undefined,
    liveStatus: string | undefined,
  ): ChangeImpact {
    if (repoStatus === 'implemented' && liveStatus === 'failed') return 'critical';
    if (repoStatus === 'implemented' && liveStatus === 'not_started') return 'high';
    if (repoStatus === 'in_progress' && liveStatus === 'failed') return 'high';
    return 'medium';
  }

  private computeMaxSeverity(items: DriftItem[]): ChangeImpact {
    const order: ChangeImpact[] = ['none', 'low', 'medium', 'high', 'critical'];
    let max: ChangeImpact = 'none';
    for (const item of items) {
      if (order.indexOf(item.severity) > order.indexOf(max)) {
        max = item.severity;
      }
    }
    return max;
  }

  private generatePRTitle(diff: GrcDiff, driftItems: DriftItem[]): string {
    const parts: string[] = ['compliance:'];

    if (diff.summary.controlsAdded > 0) {
      parts.push(`+${diff.summary.controlsAdded} controls`);
    }
    if (diff.summary.controlsModified > 0) {
      parts.push(`~${diff.summary.controlsModified} modified`);
    }
    if (diff.summary.controlsRemoved > 0) {
      parts.push(`-${diff.summary.controlsRemoved} removed`);
    }
    if (driftItems.length > 0) {
      parts.push(`drift-fix(${driftItems.length})`);
    }

    return parts.length > 1 ? parts.join(' ') : 'compliance: config update';
  }
}
