import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { DriftDetector } from './DriftDetector.js';
import type { ControlEvaluator, ControlSnapshot, DriftDetectorConfig } from './types.js';

// ─── Mock Evaluator ─────────────────────────────────────────────────

function makeMockEvaluator(controls: Map<string, ControlSnapshot>): ControlEvaluator {
  return {
    async evaluateControl(controlId: string, framework: string): Promise<ControlSnapshot> {
      const key = `${controlId}:${framework}`;
      const snap = controls.get(key);
      if (!snap) {
        return {
          controlId,
          framework,
          status: 'unknown',
          evidenceHashes: [],
          evidenceCount: 0,
          complianceScore: 0,
          lastCheckedAt: new Date().toISOString(),
        };
      }
      return { ...snap, lastCheckedAt: new Date().toISOString() };
    },
    async listControls(framework: string): Promise<Array<{ controlId: string; title: string }>> {
      const defs: Array<{ controlId: string; title: string }> = [];
      for (const [key, snap] of controls) {
        if (snap.framework === framework) {
          defs.push({ controlId: snap.controlId, title: snap.controlId });
        }
      }
      return defs;
    },
  };
}

function makeControl(
  controlId: string,
  framework: string,
  status: ControlSnapshot['status'],
  evidenceCount: number,
  score: number,
): ControlSnapshot {
  return {
    controlId,
    framework,
    status,
    evidenceHashes: Array.from({ length: evidenceCount }, (_, i) => `hash-${i}`),
    evidenceCount,
    complianceScore: score,
    lastCheckedAt: new Date().toISOString(),
  };
}

// ─── Tests ──────────────────────────────────────────────────────────

describe('DriftDetector', () => {
  let controls: Map<string, ControlSnapshot>;
  let evaluator: ControlEvaluator;
  let config: DriftDetectorConfig;

  beforeEach(() => {
    controls = new Map();
    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'compliant', 3, 100));
    controls.set('A.5.2:iso27001', makeControl('A.5.2', 'iso27001', 'compliant', 2, 100));
    controls.set('A.8.1:iso27001', makeControl('A.8.1', 'iso27001', 'partial', 1, 50));
    evaluator = makeMockEvaluator(controls);
    config = {
      tenantId: 1,
      frameworks: ['iso27001'],
      driftThresholdPercent: 5,
      scoreDeltaAlertThreshold: 10,
    };
  });

  it('should capture a baseline snapshot', async () => {
    const detector = new DriftDetector(config, evaluator);
    const baseline = await detector.captureBaseline();

    assert.equal(baseline.controlCount, 3);
    assert.equal(baseline.compliantCount, 2);
    assert.ok(baseline.hash.length > 0);
    assert.ok(baseline.id.length > 0);
  });

  it('should detect no drift when controls are unchanged', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();
    const result = await detector.detectDrift();

    assert.equal(result.driftDetected, false);
    assert.equal(result.driftEvents.length, 0);
    assert.equal(result.overallScoreDelta, 0);
  });

  it('should detect status downgrade drift', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'non_compliant', 0, 0));
    const result = await detector.detectDrift();

    assert.equal(result.driftDetected, true);
    assert.ok(result.driftEvents.length > 0);
    const event = result.driftEvents.find(e => e.controlId === 'A.5.1');
    assert.ok(event);
    assert.equal(event.previousStatus, 'compliant');
    assert.equal(event.currentStatus, 'non_compliant');
    assert.equal(event.eventType, 'evidence_revoked');
  });

  it('should detect evidence revocation', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'compliant', 0, 100));
    const result = await detector.detectDrift();

    const event = result.driftEvents.find(e => e.controlId === 'A.5.1');
    assert.ok(event);
    assert.equal(event.eventType, 'evidence_expired');
    assert.equal(event.previousEvidenceCount, 3);
    assert.equal(event.currentEvidenceCount, 0);
  });

  it('should detect score degradation', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.8.1:iso27001', makeControl('A.8.1', 'iso27001', 'partial', 1, 25));
    const result = await detector.detectDrift();

    const event = result.driftEvents.find(e => e.controlId === 'A.8.1');
    assert.ok(event);
    assert.equal(event.eventType, 'score_degradation');
    assert.equal(event.delta, 25);
  });

  it('should generate alerts when drift exceeds threshold', async () => {
    let alertReceived = false;
    config.onAlert = () => { alertReceived = true; };

    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'non_compliant', 0, 0));
    await detector.detectDrift();

    assert.equal(alertReceived, true);
    const alerts = detector.getAlertHistory();
    assert.ok(alerts.length > 0);
    assert.equal(alerts[0].priority, 'p1');
  });

  it('should track drift history across multiple cycles', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'non_compliant', 0, 0));
    await detector.detectDrift();

    controls.set('A.5.2:iso27001', makeControl('A.5.2', 'iso27001', 'non_compliant', 0, 0));
    await detector.detectDrift();

    const history = detector.getDriftHistory();
    assert.ok(history.length >= 2);
  });

  it('should compute drift summary correctly', async () => {
    const detector = new DriftDetector(config, evaluator);
    await detector.captureBaseline();

    controls.set('A.5.1:iso27001', makeControl('A.5.1', 'iso27001', 'non_compliant', 0, 0));
    controls.set('A.5.2:iso27001', makeControl('A.5.2', 'iso27001', 'partial', 1, 50));
    await detector.detectDrift();

    const summary = detector.getDriftSummary();
    assert.ok(summary.totalEvents >= 2);
    assert.ok(summary.bySeverity.critical > 0 || summary.bySeverity.high > 0);
    assert.ok(summary.byFramework.iso27001 >= 2);
  });

  it('should maintain baseline history within limits', async () => {
    const limitedConfig = { ...config, maxBaselineHistory: 3 };
    const detector = new DriftDetector(limitedConfig, evaluator);

    for (let i = 0; i < 5; i++) {
      await detector.captureBaseline();
    }

    const history = detector.getBaselineHistory();
    assert.equal(history.length, 3);
  });
});
