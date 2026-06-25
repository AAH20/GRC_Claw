import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { GrcFile } from './engineering/GrcFile.js';
import { CompliancePipeline } from './engineering/CompliancePipeline.js';
import { GitOpsWorkflow } from './engineering/GitOpsWorkflow.js';
import type { GrcConfig } from './types.js';
import type { ComplianceControl } from '@grc-claw/core';
import type { GrcDiff } from './types.js';

// ── Test fixtures ──────────────────────────────────────────────────────────

function makeConfig(overrides?: Partial<GrcConfig>): GrcConfig {
  return {
    version: '1.0',
    org: { name: 'Acme Corp', tenantId: 1, slug: 'acme' },
    frameworks: [{ code: 'iso27001', enabledControls: ['iso-a.5.1'] }],
    controls: [
      {
        id: 'ctrl-1',
        controlCode: 'A.5.1',
        title: 'Policies for information security',
        frameworkCode: 'iso27001',
        domain: 'Organizational',
        implementationStatus: 'in_progress',
        evidenceRequired: [{ type: 'document', description: 'Policy doc', minimumCount: 1 }],
      },
    ],
    evidenceSources: [
      {
        id: 'src-1',
        name: 'GitHub',
        type: 'git_repo',
        config: { repo: 'acme/policies' },
      },
    ],
    complianceRules: [
      {
        id: 'rule-1',
        name: 'Policy document exists',
        description: 'Ensure policy document is attached',
        severity: 'high',
        frameworkCode: 'iso27001',
        controlIds: ['ctrl-1'],
        ruleType: 'evidence_freshness',
        condition: { field: 'version', operator: 'equals', value: '1.0' },
      },
    ],
    ...overrides,
  };
}

function makeLiveControls(): ComplianceControl[] {
  return [
    {
      id: 'ctrl-1',
      controlCode: 'A.5.1',
      title: 'Policies for information security',
      frameworkCode: 'iso27001',
      domain: 'Organizational',
      orgStatus: 'in_progress',
    },
  ];
}

// ── GrcFile tests ──────────────────────────────────────────────────────────

describe('GrcFile', () => {
  let grcFile: GrcFile;

  beforeEach(() => {
    grcFile = new GrcFile();
  });

  describe('parse', () => {
    it('should parse a valid JSON config', () => {
      const config = makeConfig();
      const result = grcFile.parse(JSON.stringify(config));
      assert.equal(result.version, '1.0');
      assert.equal(result.org.name, 'Acme Corp');
      assert.equal(result.controls.length, 1);
    });

    it('should reject non-object JSON', () => {
      assert.throws(() => grcFile.parse('"hello"'), /GRC config must be a JSON object/);
    });

    it('should reject array JSON', () => {
      assert.throws(() => grcFile.parse('[1,2,3]'), /GRC config must be a JSON object/);
    });

    it('should set a config hash', () => {
      grcFile.parse(JSON.stringify(makeConfig()));
      const hash = grcFile.getConfigHash();
      assert.ok(hash.length > 0);
      assert.ok(hash.match(/^[a-f0-9]+$/));
    });

    it('should produce consistent hashes for identical configs', () => {
      const config = makeConfig();
      const g1 = new GrcFile();
      const g2 = new GrcFile();
      g1.parse(JSON.stringify(config));
      g2.parse(JSON.stringify(config));
      assert.equal(g1.getConfigHash(), g2.getConfigHash());
    });
  });

  describe('validate', () => {
    it('should pass a valid config', () => {
      grcFile.parse(JSON.stringify(makeConfig()));
      const errors = grcFile.validate();
      const critical = errors.filter((e) => e.severity === 'error');
      assert.equal(critical.length, 0);
    });

    it('should fail when version is missing', () => {
      const config = makeConfig();
      delete (config as unknown as Record<string, unknown>).version;
      grcFile.parse(JSON.stringify(config));
      const errors = grcFile.validate();
      assert.ok(errors.some((e) => e.message.includes('Required field')));
    });

    it('should fail when org is missing', () => {
      const config = makeConfig();
      delete (config as unknown as Record<string, unknown>).org;
      grcFile.parse(JSON.stringify(config));
      const errors = grcFile.validate();
      assert.ok(errors.some((e) => e.path.includes('org')));
    });

    it('should warn about unknown frameworks', () => {
      const config = makeConfig({
        frameworks: [{ code: 'unknown_framework', enabledControls: [] }],
      });
      grcFile.parse(JSON.stringify(config));
      const errors = grcFile.validate();
      assert.ok(errors.some((e) => e.message.includes('Unknown framework')));
    });

    it('should fail when control references unbound framework', () => {
      const config = makeConfig({
        frameworks: [{ code: 'iso27001', enabledControls: [] }],
        controls: [
          {
            id: 'ctrl-bad',
            controlCode: 'X.1',
            title: 'Bad',
            frameworkCode: 'soc2',
            implementationStatus: 'not_started',
            evidenceRequired: [],
          },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const errors = grcFile.validate();
      assert.ok(errors.some((e) => e.message.includes('unbound framework')));
    });

    it('should warn about invalid endpoint URL', () => {
      const config = makeConfig({
        controls: [
          {
            id: 'ctrl-auto',
            controlCode: 'A.1',
            title: 'Auto',
            frameworkCode: 'iso27001',
            implementationStatus: 'in_progress',
            evidenceRequired: [],
            autoCollect: { method: 'api_poll', endpoint: 'not-a-url' },
          },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const errors = grcFile.validate();
      assert.ok(errors.some((e) => e.message.includes('Invalid endpoint URL')));
    });
  });

  describe('plan', () => {
    it('should generate additions for new controls', () => {
      const config = makeConfig({
        controls: [
          {
            id: 'ctrl-new',
            controlCode: 'A.8.1',
            title: 'New Control',
            frameworkCode: 'iso27001',
            implementationStatus: 'not_started',
            evidenceRequired: [],
          },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const plan = grcFile.plan([]);
      assert.equal(plan.additions.length, 1);
      assert.equal(plan.additions[0].id, 'ctrl-new');
      assert.equal(plan.modifications.length, 0);
      assert.equal(plan.deletions.length, 0);
    });

    it('should generate deletions for removed controls', () => {
      const config = makeConfig({ controls: [] });
      grcFile.parse(JSON.stringify(config));
      const plan = grcFile.plan(makeLiveControls());
      assert.equal(plan.deletions.length, 1);
      assert.equal(plan.deletions[0].id, 'ctrl-1');
    });

    it('should generate modifications for status drift', () => {
      const config = makeConfig({
        controls: [
          {
            id: 'ctrl-1',
            controlCode: 'A.5.1',
            title: 'Policies for information security',
            frameworkCode: 'iso27001',
            implementationStatus: 'implemented',
            evidenceRequired: [],
          },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const plan = grcFile.plan(makeLiveControls());
      assert.equal(plan.modifications.length, 1);
      assert.equal(plan.modifications[0].id, 'ctrl-1');
    });

    it('should produce valid plan when no changes', () => {
      const config = makeConfig();
      grcFile.parse(JSON.stringify(config));
      const plan = grcFile.plan(makeLiveControls());
      assert.equal(plan.additions.length, 0);
      assert.equal(plan.modifications.length, 0);
      assert.equal(plan.deletions.length, 0);
      assert.equal(plan.isValid, true);
    });

    it('should compute config hash', () => {
      grcFile.parse(JSON.stringify(makeConfig()));
      const plan = grcFile.plan([]);
      assert.equal(plan.configHash, grcFile.getConfigHash());
    });
  });

  describe('apply', () => {
    it('should apply a valid plan', () => {
      const config = makeConfig({
        controls: [
          { id: 'ctrl-new', controlCode: 'A.1', title: 'New', frameworkCode: 'iso27001', implementationStatus: 'not_started', evidenceRequired: [] },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const plan = grcFile.plan([]);
      assert.equal(plan.additions.length, 1);
      const result = grcFile.apply(plan);
      assert.ok(result.controls.find((c) => c.id === 'ctrl-new'));
    });

    it('should reject invalid plan', () => {
      grcFile.parse(JSON.stringify(makeConfig()));
      const plan = grcFile.plan([]);
      plan.validationErrors.push({ path: '$', message: 'forced error', severity: 'error' });
      plan.isValid = false;
      assert.throws(() => grcFile.apply(plan), /validation errors/);
    });
  });

  describe('diff', () => {
    it('should produce a diff summary', () => {
      const config = makeConfig({
        controls: [
          { id: 'ctrl-a', controlCode: 'A.1', title: 'A', frameworkCode: 'iso27001', implementationStatus: 'not_started', evidenceRequired: [] },
        ],
      });
      grcFile.parse(JSON.stringify(config));
      const diff = grcFile.diff([
        { id: 'ctrl-b', controlCode: 'B.1', title: 'B', frameworkCode: 'iso27001', orgStatus: 'implemented' },
      ]);
      assert.equal(diff.summary.controlsAdded, 1);
      assert.equal(diff.summary.controlsRemoved, 1);
      assert.ok(diff.timestamp);
    });
  });

  describe('audit trail', () => {
    it('should track parse, validate, and plan actions', () => {
      grcFile.parse(JSON.stringify(makeConfig()));
      grcFile.validate();
      grcFile.plan([]);
      const trail = grcFile.getAuditTrail();
      assert.ok(trail.entries.length >= 3);
      assert.ok(trail.entries.some((e) => e.action === 'config.create'));
      assert.ok(trail.entries.some((e) => e.action === 'config.validate'));
    });
  });
});

// ── CompliancePipeline tests ───────────────────────────────────────────────

describe('CompliancePipeline', () => {
  let pipeline: CompliancePipeline;

  beforeEach(() => {
    pipeline = new CompliancePipeline();
  });

  describe('configure', () => {
    it('should allow disabling stages', () => {
      pipeline.configure([
        { name: 'lint', enabled: true },
        { name: 'validate', enabled: true },
        { name: 'test', enabled: false },
        { name: 'deploy', enabled: false },
        { name: 'monitor', enabled: false },
      ]);
      const stages = pipeline.getEnabledStages();
      assert.deepEqual(stages, ['lint', 'validate']);
    });

    it('should include all stages by default', () => {
      const stages = pipeline.getEnabledStages();
      assert.deepEqual(stages, ['lint', 'validate', 'test', 'deploy', 'monitor']);
    });
  });

  describe('run', () => {
    it('should run full pipeline successfully on valid config', async () => {
      const config = makeConfig();
      const result = await pipeline.run(config, 'test-user');
      assert.equal(result.status, 'passed');
      assert.equal(result.stages.length, 5);
      assert.equal(result.stages.every((s) => s.status === 'passed'), true);
    });

    it('should fail on lint when control IDs are duplicated', async () => {
      const config = makeConfig({
        controls: [
          { id: 'dup', controlCode: 'A.1', title: 'A', frameworkCode: 'iso27001', implementationStatus: 'in_progress', evidenceRequired: [] },
          { id: 'dup', controlCode: 'A.2', title: 'B', frameworkCode: 'iso27001', implementationStatus: 'in_progress', evidenceRequired: [] },
        ],
      });
      const result = await pipeline.run(config);
      assert.equal(result.status, 'failed');
      assert.equal(result.stages[0].status, 'failed');
      assert.ok(result.stages[0].findings.some((f) => f.ruleId === 'lint-003'));
    });

    it('should fail validate when control references unbound framework', async () => {
      const config = makeConfig({
        controls: [
          { id: 'ctrl-x', controlCode: 'X.1', title: 'X', frameworkCode: 'nonexistent', implementationStatus: 'in_progress', evidenceRequired: [] },
        ],
      });
      const result = await pipeline.run(config);
      // Lint passes (no duplicates), validate fails
      assert.equal(result.stages[0].status, 'passed');
      assert.equal(result.stages[1].status, 'failed');
    });

    it('should record evidence from deploy stage', async () => {
      const config = makeConfig({
        controls: [
          {
            id: 'ctrl-auto',
            controlCode: 'A.1',
            title: 'Auto',
            frameworkCode: 'iso27001',
            implementationStatus: 'in_progress',
            evidenceRequired: [],
            autoCollect: { method: 'api_poll', endpoint: 'https://example.com' },
          },
        ],
      });
      const result = await pipeline.run(config);
      assert.ok(result.evidence.length > 0);
      assert.equal(result.evidence[0].controlId, 'ctrl-auto');
    });

    it('should track pipeline run history', async () => {
      await pipeline.run(makeConfig());
      await pipeline.run(makeConfig());
      assert.equal(pipeline.getRuns().length, 2);
    });

    it('should generate audit entries', async () => {
      await pipeline.run(makeConfig(), 'auditor');
      const entries = pipeline.getAuditEntries();
      assert.ok(entries.some((e) => e.action === 'pipeline.run_started'));
      assert.ok(entries.some((e) => e.action === 'pipeline.run_completed'));
    });
  });

  describe('registerStage', () => {
    it('should allow registering a custom stage handler', async () => {
      pipeline.registerStage({
        name: 'lint',
        async run() {
          return {
            status: 'passed' as const,
            findings: [{ ruleId: 'custom', severity: 'low' as const, message: 'Custom lint' }],
            logs: ['[custom-lint] Ran custom lint'],
          };
        },
      });
      const result = await pipeline.run(makeConfig());
      const lintStage = result.stages.find((s) => s.stage === 'lint');
      assert.ok(lintStage, 'lint stage should exist in results');
      assert.equal(lintStage.status, 'passed');
      assert.ok(lintStage.logs.length > 0, 'lint stage should have logs');
      assert.ok(lintStage.logs.some((l) => l.includes('custom-lint')), `Expected custom-lint in logs: ${JSON.stringify(lintStage.logs)}`);
    });
  });
});

// ── GitOpsWorkflow tests ───────────────────────────────────────────────────

describe('GitOpsWorkflow', () => {
  let workflow: GitOpsWorkflow;

  beforeEach(() => {
    workflow = new GitOpsWorkflow();
  });

  describe('initRepo', () => {
    it('should create initial repo state', () => {
      const state = workflow.initRepo('main');
      assert.equal(state.branch, 'main');
      assert.ok(state.commitSha);
      assert.ok(state.configHash);
    });

    it('should record initial commit', () => {
      workflow.initRepo();
      assert.equal(workflow.getCommitHistory().length, 1);
    });
  });

  describe('commit', () => {
    it('should record a commit', () => {
      workflow.initRepo();
      const commit = workflow.commit(makeConfig(), 'dev', 'Add controls');
      assert.ok(commit.sha);
      assert.equal(commit.author, 'dev');
      assert.equal(commit.message, 'Add controls');
      assert.equal(workflow.getCommitHistory().length, 2);
    });

    it('should produce unique SHAs', () => {
      workflow.initRepo();
      const c1 = workflow.commit(makeConfig(), 'dev', 'First');
      const c2 = workflow.commit(makeConfig(), 'dev', 'Second');
      assert.notEqual(c1.sha, c2.sha);
    });
  });

  describe('detectDrift', () => {
    it('should detect no drift when states match', () => {
      workflow.initRepo();
      const config = makeConfig();
      const commit = workflow.commit(config, 'dev', 'Init');
      const liveControls = makeLiveControls();
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: liveControls,
        rules: [],
      };
      const report = workflow.detectDrift(repoState, liveControls);
      assert.equal(report.totalDrift, 0);
    });

    it('should detect control missing from live', () => {
      workflow.initRepo();
      const config = makeConfig();
      const commit = workflow.commit(config, 'dev', 'Init');
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: makeLiveControls(),
        rules: [],
      };
      const report = workflow.detectDrift(repoState, []);
      assert.equal(report.totalDrift, 1);
      assert.equal(report.driftItems[0].type, 'control_status');
      assert.equal(report.driftItems[0].severity, 'medium');
    });

    it('should detect control missing from repo', () => {
      workflow.initRepo();
      const config = makeConfig({ controls: [] });
      const commit = workflow.commit(config, 'dev', 'Init');
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: [],
        rules: [],
      };
      const liveControls = makeLiveControls();
      const report = workflow.detectDrift(repoState, liveControls);
      assert.equal(report.totalDrift, 1);
      assert.equal(report.driftItems[0].severity, 'high');
    });

    it('should detect status drift', () => {
      workflow.initRepo();
      const config = makeConfig({
        controls: [
          { id: 'ctrl-1', controlCode: 'A.5.1', title: 'Policies', frameworkCode: 'iso27001', implementationStatus: 'implemented', evidenceRequired: [] },
        ],
      });
      const commit = workflow.commit(config, 'dev', 'Init');
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: [{ id: 'ctrl-1', controlCode: 'A.5.1', title: 'Policies', frameworkCode: 'iso27001', orgStatus: 'implemented' as const }],
        rules: [],
      };
      const report = workflow.detectDrift(repoState, [{ id: 'ctrl-1', controlCode: 'A.5.1', title: 'Policies', frameworkCode: 'iso27001', orgStatus: 'failed' as const }]);
      assert.ok(report.totalDrift > 0);
    });
  });

  describe('resolveDrift', () => {
    it('should create a new commit resolving drift', () => {
      workflow.initRepo();
      const config = makeConfig({ controls: [] });
      const commit = workflow.commit(config, 'dev', 'Init');
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: [],
        rules: [],
      };
      const liveControls = makeLiveControls();
      const driftReport = workflow.detectDrift(repoState, liveControls);
      const resolved = workflow.resolveDrift(driftReport, liveControls, 'resolver');
      assert.ok(resolved.sha);
      assert.equal(resolved.author, 'resolver');
      assert.equal(workflow.getCommitHistory().length, 3);
    });
  });

  describe('generatePRDescription', () => {
    it('should generate a PR description from diff', () => {
      const diff: GrcDiff = {
        summary: {
          controlsAdded: 1,
          controlsModified: 0,
          controlsRemoved: 0,
          evidenceSourcesChanged: 0,
          rulesChanged: 0,
          pipelinesChanged: 0,
          overallRisk: 'high',
        },
        changes: [],
        timestamp: new Date().toISOString(),
      };
      const pr = workflow.generatePRDescription(diff);
      assert.ok(pr.title.includes('+1 controls'));
      assert.ok(pr.body.includes('Compliance Change Summary'));
      assert.ok(pr.labels.includes('compliance: new-controls'));
      assert.ok(pr.labels.includes('priority: high'));
    });

    it('should include drift items in PR body', () => {
      const diff: GrcDiff = {
        summary: {
          controlsAdded: 0,
          controlsModified: 1,
          controlsRemoved: 0,
          evidenceSourcesChanged: 0,
          rulesChanged: 0,
          pipelinesChanged: 0,
          overallRisk: 'medium',
        },
        changes: [],
        timestamp: new Date().toISOString(),
      };
      const driftItems = [
        { type: 'control_status' as const, id: 'ctrl-1', description: 'Status drift', repoValue: 'implemented', liveValue: 'failed', severity: 'critical' as const },
      ];
      const pr = workflow.generatePRDescription(diff, driftItems);
      assert.ok(pr.body.includes('Drift Resolution'));
      assert.ok(pr.body.includes('Status drift'));
      assert.ok(pr.labels.includes('drift-resolution'));
    });
  });

  describe('configureBranchProtection', () => {
    it('should set branch protection rules', () => {
      workflow.configureBranchProtection('main', {
        pattern: 'main',
        requireReview: true,
        requiredReviewers: 2,
        requireStatusChecks: ['lint', 'validate'],
        requireSignedCommits: true,
        restrictPushes: true,
        allowForcePushes: false,
        requireLinearHistory: true,
      });
      const protections = workflow.getBranchProtections();
      assert.ok(protections.has('main'));
      assert.equal(protections.get('main')?.requiredReviewers, 2);
    });
  });

  describe('checkPushAllowed', () => {
    it('should allow push when no protection configured', () => {
      const result = workflow.checkPushAllowed('feature');
      assert.equal(result.allowed, true);
      assert.equal(result.reasons.length, 0);
    });

    it('should block push when review required but not approved', () => {
      workflow.configureBranchProtection('main', {
        pattern: 'main',
        requireReview: true,
        requiredReviewers: 1,
        requireStatusChecks: [],
        requireSignedCommits: false,
        restrictPushes: false,
        allowForcePushes: true,
        requireLinearHistory: false,
      });
      const result = workflow.checkPushAllowed('main');
      assert.equal(result.allowed, false);
      assert.ok(result.reasons.some((r) => r.includes('review')));
    });

    it('should block when status checks missing', () => {
      workflow.configureBranchProtection('main', {
        pattern: 'main',
        requireReview: false,
        requiredReviewers: 0,
        requireStatusChecks: ['lint', 'validate'],
        requireSignedCommits: false,
        restrictPushes: false,
        allowForcePushes: true,
        requireLinearHistory: false,
      });
      const result = workflow.checkPushAllowed('main', { statusChecks: ['lint'] });
      assert.equal(result.allowed, false);
      assert.ok(result.reasons.some((r) => r.includes('validate')));
    });

    it('should block unsigned commits when required', () => {
      workflow.configureBranchProtection('main', {
        pattern: 'main',
        requireReview: false,
        requiredReviewers: 0,
        requireStatusChecks: [],
        requireSignedCommits: true,
        restrictPushes: false,
        allowForcePushes: true,
        requireLinearHistory: false,
      });
      const result = workflow.checkPushAllowed('main', { isSigned: false });
      assert.equal(result.allowed, false);
      assert.ok(result.reasons.some((r) => r.includes('signed')));
    });

    it('should block force pushes when not allowed', () => {
      workflow.configureBranchProtection('main', {
        pattern: 'main',
        requireReview: false,
        requiredReviewers: 0,
        requireStatusChecks: [],
        requireSignedCommits: false,
        restrictPushes: false,
        allowForcePushes: false,
        requireLinearHistory: false,
      });
      const result = workflow.checkPushAllowed('main', { isForcePush: true });
      assert.equal(result.allowed, false);
      assert.ok(result.reasons.some((r) => r.includes('Force push')));
    });
  });

  describe('snapshot', () => {
    it('should export full state', () => {
      workflow.initRepo();
      workflow.commit(makeConfig(), 'dev', 'Test');
      const snap = workflow.snapshot();
      assert.equal(snap.commits.length, 2);
      assert.ok(typeof snap.branchProtections === 'object');
      assert.ok(Array.isArray(snap.driftReports));
      assert.ok(Array.isArray(snap.auditEntries));
    });
  });

  describe('audit trail', () => {
    it('should track all workflow actions', () => {
      workflow.initRepo();
      const config = makeConfig();
      const commit = workflow.commit(config, 'dev', 'Init');
      const repoState = {
        commitSha: commit.sha,
        branch: 'main',
        configHash: commit.configHash,
        controls: makeLiveControls(),
        rules: [],
      };
      workflow.detectDrift(repoState, []);
      workflow.configureBranchProtection('main', {
        pattern: 'main', requireReview: true, requiredReviewers: 1,
        requireStatusChecks: [], requireSignedCommits: false,
        restrictPushes: false, allowForcePushes: true, requireLinearHistory: false,
      });
      const entries = workflow.getAuditEntries();
      assert.ok(entries.length >= 3);
    });
  });
});
