import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { ComplianceAutopilot } from './ComplianceAutopilot.js';
import type { EvidenceDatabase, AutopilotConfig } from './types.js';

function createMockDb(evidence: Record<string, Array<{ id: string; sha256: string }>> = {}): EvidenceDatabase {
  const store = new Map<string, Array<{ id: string; sha256: string }>>(Object.entries(evidence));
  return {
    async query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }> {
      if (sql.includes('WHERE control_id')) {
        const controlId = params?.[0] as string;
        const items = store.get(controlId) ?? [];
        return { rows: items as T[], rowCount: items.length };
      }
      return { rows: [] as T[], rowCount: 0 };
    },
    async execute(_sql: string, _params?: unknown[]) {
      // no-op for tests
    },
  };
}

function createTestConfig(overrides?: Partial<AutopilotConfig>): AutopilotConfig {
  return {
    frameworks: ['iso27001'],
    tenantId: 1,
    autoRemediate: true,
    ...overrides,
  };
}

describe('ComplianceAutopilot', () => {
  let autopilot: ComplianceAutopilot;

  beforeEach(() => {
    autopilot = new ComplianceAutopilot(createTestConfig());
  });

  it('initializes controls for configured frameworks', () => {
    const controls = autopilot.getControls();
    assert.ok(controls.length > 0, 'Should have controls');
    assert.ok(controls.every((c) => c.framework === 'iso27001'));
    assert.ok(controls.some((c) => c.controlId === 'A.5.1'));
    assert.ok(controls.some((c) => c.controlId === 'A.8.16'));
  });

  it('supports multiple frameworks', () => {
    const multi = new ComplianceAutopilot(
      createTestConfig({ frameworks: ['iso27001', 'soc2', 'nist_csf'] }),
    );
    const controls = multi.getControls();
    const frameworks = new Set(controls.map((c) => c.framework));
    assert.ok(frameworks.has('iso27001'));
    assert.ok(frameworks.has('soc2'));
    assert.ok(frameworks.has('nist_csf'));
  });

  it('monitor detects gaps when no evidence exists', async () => {
    const result = await autopilot.monitor();
    assert.ok(result.controlsChecked > 0);
    assert.ok(result.gapsFound > 0);
    assert.ok(result.gaps.length > 0);
    assert.ok(result.frameworksChecked.includes('iso27001'));
  });

  it('monitor marks controls compliant when evidence exists', async () => {
    const db = createMockDb({
      'A.5.1': [{ id: 'ev-1', sha256: 'abc' }, { id: 'ev-2', sha256: 'def' }],
      'A.8.16': [{ id: 'ev-3', sha256: 'ghi' }, { id: 'ev-4', sha256: 'jkl' }],
    });
    const auto = new ComplianceAutopilot(
      createTestConfig({ evidenceDb: db }),
    );
    const result = await auto.monitor();
    const compliantControls = auto.getControls().filter((c) => c.status === 'compliant');
    assert.ok(compliantControls.length >= 2, 'At least 2 controls should be compliant');
    const a51 = auto.getControls().find((c) => c.controlId === 'A.5.1');
    assert.equal(a51?.status, 'compliant');
  });

  it('monitor marks controls partial when only 1 evidence item', async () => {
    const db = createMockDb({
      'A.5.1': [{ id: 'ev-1', sha256: 'abc' }],
    });
    const auto = new ComplianceAutopilot(
      createTestConfig({ evidenceDb: db }),
    );
    await auto.monitor();
    const a51 = auto.getControls().find((c) => c.controlId === 'A.5.1');
    assert.equal(a51?.status, 'partial');
  });

  it('detect returns current gaps', async () => {
    await autopilot.monitor();
    const gaps = autopilot.detect();
    assert.ok(Array.isArray(gaps));
    assert.ok(gaps.length > 0);
    assert.ok(gaps[0]!.id);
    assert.ok(gaps[0]!.controlId);
    assert.ok(gaps[0]!.severity);
  });

  it('remediate creates remediation plans', async () => {
    await autopilot.monitor();
    const plans = await autopilot.remediate();
    assert.ok(plans.length > 0);
    assert.ok(plans[0]!.actions.length > 0);
    assert.ok(['completed', 'in_progress', 'pending'].includes(plans[0]!.status));
  });

  it('remediate does not duplicate plans for same gap', async () => {
    await autopilot.monitor();
    const plans1 = await autopilot.remediate();
    const plans2 = await autopilot.remediate();
    assert.equal(plans2.length, 0, 'Should not create duplicate plans');
  });

  it('verify checks remediation results', async () => {
    await autopilot.monitor();
    const plans = await autopilot.remediate();
    if (plans.length > 0) {
      const results = await autopilot.verify([plans[0]!.id]);
      assert.ok(results.length > 0);
      assert.ok(typeof results[0]!.verified === 'boolean');
      assert.ok(results[0]!.verifiedAt);
    }
  });

  it('generateReport produces a valid report', async () => {
    await autopilot.monitor();
    const report = await autopilot.generateReport('iso27001');
    assert.equal(report.framework, 'iso27001');
    assert.ok(report.totalControls > 0);
    assert.ok(typeof report.complianceScore === 'number');
    assert.ok(report.complianceScore >= 0 && report.complianceScore <= 100);
    assert.ok(report.generatedAt);
    assert.ok(report.id);
  });

  it('runCycle executes the full compliance cycle', async () => {
    const result = await autopilot.runCycle();
    assert.ok(result.cycleId);
    assert.ok(result.startedAt);
    assert.ok(result.completedAt);
    assert.ok(result.monitor);
    assert.ok(Array.isArray(result.remediations));
    assert.ok(Array.isArray(result.verificationResults));
    assert.ok(result.report);
    assert.ok(Array.isArray(result.auditTrail));
    assert.ok(result.auditTrail.length > 0);
  });

  it('audit trail is cryptographically chained', async () => {
    await autopilot.runCycle();
    assert.ok(autopilot.verifyAuditTrail(), 'Audit trail should be valid');
  });

  it('audit trail breaks on tampering', async () => {
    await autopilot.runCycle();
    const trail = autopilot.getAuditTrail();
    if (trail.length > 1) {
      (trail[1]! as any).action = 'tampered';
      assert.ok(!autopilot.verifyAuditTrail(), 'Tampered trail should be invalid');
    }
  });

  it('signAuditEntry creates a signature', async () => {
    await autopilot.runCycle();
    const trail = autopilot.getAuditTrail();
    if (trail.length > 0) {
      const sig = autopilot.signAuditEntry(trail[0]!.id, 'test-key-123');
      assert.ok(sig);
      assert.ok(sig.length === 64, 'Signature should be 64 hex chars');
    }
  });

  it('signAll signs all unsigned entries', async () => {
    await autopilot.runCycle();
    const signed = autopilot.signAll('signing-key');
    const allSigned = signed.every((e) => e.signature !== undefined);
    assert.ok(allSigned, 'All entries should be signed');
  });

  it('report gets signed when signingKey is provided', async () => {
    const auto = new ComplianceAutopilot(
      createTestConfig({ signingKey: 'my-secret-key' }),
    );
    await auto.monitor();
    const report = await auto.generateReport('iso27001');
    assert.ok(report.signature, 'Report should be signed');
  });

  it('returns correct config via getConfig', () => {
    const config = autopilot.getConfig();
    assert.deepEqual(config.frameworks, ['iso27001']);
    assert.equal(config.tenantId, 1);
  });

  it('cisco_controls framework has controls', () => {
    const auto = new ComplianceAutopilot(
      createTestConfig({ frameworks: ['cis_controls'] }),
    );
    const controls = auto.getControls();
    assert.ok(controls.length >= 15);
    assert.ok(controls.some((c) => c.controlId === 'CIS.1'));
  });
});
