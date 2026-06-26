import { createHash, randomUUID } from 'node:crypto';
import type {
  BaselineSnapshot,
  ControlEvaluator,
  ControlSnapshot,
  ControlStatus,
  DriftAlert,
  DriftDetectionResult,
  DriftDetectorConfig,
  DriftEvent,
  DriftEventType,
  DriftSeverity,
  AlertPriority,
} from './types.js';

// ─── Status Severity Ranking ────────────────────────────────────────

const STATUS_SEVERITY: Record<ControlStatus, number> = {
  compliant: 4,
  partial: 3,
  non_compliant: 1,
  unknown: 0,
};

function severityFromDelta(delta: number): DriftSeverity {
  const absDelta = Math.abs(delta);
  if (absDelta >= 3) return 'critical';
  if (absDelta >= 2) return 'high';
  if (absDelta >= 1) return 'medium';
  return 'low';
}

function priorityFromSeverity(severity: DriftSeverity): AlertPriority {
  switch (severity) {
    case 'critical': return 'p1';
    case 'high': return 'p2';
    case 'medium': return 'p3';
    case 'low': return 'p4';
  }
}

function classifyDriftEvent(
  prev: ControlSnapshot,
  curr: ControlSnapshot,
): { eventType: DriftEventType; description: string } | null {
  const prevStatusRank = STATUS_SEVERITY[prev.status];
  const currStatusRank = STATUS_SEVERITY[curr.status];

  if (currStatusRank < prevStatusRank) {
    const evType: DriftEventType = prev.evidenceCount > curr.evidenceCount
      ? 'evidence_revoked'
      : curr.status === 'unknown'
        ? 'control_downgraded'
        : 'status_change';
    return {
      eventType: evType,
      description: `${prev.controlId}: status ${prev.status} → ${curr.status} (evidence ${prev.evidenceCount} → ${curr.evidenceCount})`,
    };
  }

  if (curr.evidenceCount < prev.evidenceCount) {
    return {
      eventType: 'evidence_expired',
      description: `${prev.controlId}: evidence count decreased ${prev.evidenceCount} → ${curr.evidenceCount}`,
    };
  }

  if (curr.complianceScore < prev.complianceScore) {
    return {
      eventType: 'score_degradation',
      description: `${prev.controlId}: score decreased ${prev.complianceScore} → ${curr.complianceScore}`,
    };
  }

  if (prev.status === 'unknown' && curr.status !== 'unknown') {
    return {
      eventType: 'new_gap',
      description: `${prev.controlId}: status changed from unknown to ${curr.status}`,
    };
  }

  return null;
}

// ─── Drift Detector ─────────────────────────────────────────────────

export class DriftDetector {
  private config: Required<DriftDetectorConfig>;
  private evaluator: ControlEvaluator;
  private baselineHistory: BaselineSnapshot[] = [];
  private currentBaseline: BaselineSnapshot | null = null;
  private driftHistory: DriftEvent[] = [];
  private alertHistory: DriftAlert[] = [];
  private pollTimer: ReturnType<typeof setInterval> | null = null;

  constructor(config: DriftDetectorConfig, evaluator: ControlEvaluator) {
    this.config = {
      driftThresholdPercent: config.driftThresholdPercent ?? 5,
      scoreDeltaAlertThreshold: config.scoreDeltaAlertThreshold ?? 10,
      pollIntervalMs: config.pollIntervalMs ?? 60_000,
      maxBaselineHistory: config.maxBaselineHistory ?? 50,
      onDrift: config.onDrift ?? (() => {}),
      onAlert: config.onAlert ?? (() => {}),
      tenantId: config.tenantId,
      frameworks: config.frameworks,
    };
    this.evaluator = evaluator;
  }

  /** Capture a baseline snapshot of all controls across configured frameworks */
  async captureBaseline(): Promise<BaselineSnapshot> {
    const allControls: ControlSnapshot[] = [];
    let totalScore = 0;
    let compliantCount = 0;

    for (const framework of this.config.frameworks) {
      const definitions = await this.evaluator.listControls(framework);
      for (const def of definitions) {
        const snapshot = await this.evaluator.evaluateControl(def.controlId, framework);
        allControls.push(snapshot);
        totalScore += snapshot.complianceScore;
        if (snapshot.status === 'compliant') compliantCount++;
      }
    }

    const overallScore = allControls.length > 0
      ? Math.round((totalScore / allControls.length) * 100) / 100
      : 0;

    const frameworkScores: Record<string, number> = {};
    for (const fw of this.config.frameworks) {
      const fwControls = allControls.filter(c => c.framework === fw);
      frameworkScores[fw] = fwControls.length > 0
        ? Math.round((fwControls.reduce((s, c) => s + c.complianceScore, 0) / fwControls.length) * 100) / 100
        : 0;
    }

    const baseline: BaselineSnapshot = {
      id: randomUUID(),
      capturedAt: new Date().toISOString(),
      controls: allControls,
      overallScore,
      frameworkScores,
      controlCount: allControls.length,
      compliantCount,
      hash: this.computeHash(allControls),
    };

    this.currentBaseline = baseline;
    this.baselineHistory.push(baseline);
    if (this.baselineHistory.length > this.config.maxBaselineHistory) {
      this.baselineHistory.shift();
    }

    return baseline;
  }

  /** Run a single drift detection cycle against the current baseline */
  async detectDrift(): Promise<DriftDetectionResult> {
    if (!this.currentBaseline) {
      throw new Error('No baseline captured. Call captureBaseline() first.');
    }

    const baseline = this.currentBaseline;
    const currentControls: ControlSnapshot[] = [];
    let totalScore = 0;

    for (const framework of this.config.frameworks) {
      const definitions = await this.evaluator.listControls(framework);
      for (const def of definitions) {
        const snapshot = await this.evaluator.evaluateControl(def.controlId, framework);
        currentControls.push(snapshot);
        totalScore += snapshot.complianceScore;
      }
    }

    const currentScore = currentControls.length > 0
      ? Math.round((totalScore / currentControls.length) * 100) / 100
      : 0;

    const baselineMap = new Map<string, ControlSnapshot>(
      baseline.controls.map(c => [`${c.controlId}:${c.framework}`, c]),
    );

    const driftEvents: DriftEvent[] = [];

    for (const curr of currentControls) {
      const key = `${curr.controlId}:${curr.framework}`;
      const prev = baselineMap.get(key);
      if (!prev) continue;

      const classification = classifyDriftEvent(prev, curr);
      if (!classification) continue;

      const statusDelta = STATUS_SEVERITY[prev.status] - STATUS_SEVERITY[curr.status];
      const scoreDelta = prev.complianceScore - curr.complianceScore;
      const severity = severityFromDelta(Math.max(statusDelta, scoreDelta));

      driftEvents.push({
        id: randomUUID(),
        timestamp: new Date().toISOString(),
        controlId: curr.controlId,
        framework: curr.framework,
        eventType: classification.eventType,
        previousStatus: prev.status,
        currentStatus: curr.status,
        previousEvidenceCount: prev.evidenceCount,
        currentEvidenceCount: curr.evidenceCount,
        previousScore: prev.complianceScore,
        currentScore: curr.complianceScore,
        delta: scoreDelta,
        severity,
        description: classification.description,
      });
    }

    const overallScoreDelta = baseline.overallScore - currentScore;
    const driftDetected = driftEvents.length > 0 ||
      Math.abs(overallScoreDelta) >= this.config.driftThresholdPercent;

    if (driftDetected) {
      this.driftHistory.push(...driftEvents);
      this.config.onDrift(driftEvents);
    }

    const alerts = this.buildAlerts(driftEvents, overallScoreDelta);
    for (const alert of alerts) {
      this.alertHistory.push(alert);
      this.config.onAlert(alert);
    }

    return {
      snapshotId: randomUUID(),
      baselineId: baseline.id,
      detectedAt: new Date().toISOString(),
      driftEvents,
      driftDetected,
      overallScoreDelta: Math.round(overallScoreDelta * 100) / 100,
      currentScore,
      baselineScore: baseline.overallScore,
      alerts,
    };
  }

  /** Start continuous polling at the configured interval */
  startPolling(): void {
    if (this.pollTimer) return;
    this.pollTimer = setInterval(() => {
      this.detectDrift().catch(err => {
        console.error('[DriftDetector] polling error:', err instanceof Error ? err.message : err);
      });
    }, this.config.pollIntervalMs);
  }

  /** Stop continuous polling */
  stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  /** Get the drift history */
  getDriftHistory(): DriftEvent[] {
    return [...this.driftHistory];
  }

  /** Get the alert history */
  getAlertHistory(): DriftAlert[] {
    return [...this.alertHistory];
  }

  /** Get the current baseline */
  getCurrentBaseline(): BaselineSnapshot | null {
    return this.currentBaseline;
  }

  /** Get baseline history */
  getBaselineHistory(): BaselineSnapshot[] {
    return [...this.baselineHistory];
  }

  /** Compute a summary of drift events by severity */
  getDriftSummary(): {
    totalEvents: number;
    bySeverity: Record<DriftSeverity, number>;
    byType: Record<DriftEventType, number>;
    byFramework: Record<string, number>;
    overallScoreDelta: number;
  } {
    const bySeverity: Record<DriftSeverity, number> = { critical: 0, high: 0, medium: 0, low: 0 };
    const byType: Record<DriftEventType, number> = {
      evidence_revoked: 0,
      control_downgraded: 0,
      evidence_expired: 0,
      new_gap: 0,
      score_degradation: 0,
      status_change: 0,
    };
    const byFramework: Record<string, number> = {};

    for (const event of this.driftHistory) {
      bySeverity[event.severity]++;
      byType[event.eventType]++;
      byFramework[event.framework] = (byFramework[event.framework] ?? 0) + 1;
    }

    const overallScoreDelta = this.baselineHistory.length >= 2
      ? this.baselineHistory[0].overallScore - this.baselineHistory[this.baselineHistory.length - 1].overallScore
      : 0;

    return {
      totalEvents: this.driftHistory.length,
      bySeverity,
      byType,
      byFramework,
      overallScoreDelta: Math.round(overallScoreDelta * 100) / 100,
    };
  }

  private buildAlerts(events: DriftEvent[], overallDelta: number): DriftAlert[] {
    if (events.length === 0 && Math.abs(overallDelta) < this.config.scoreDeltaAlertThreshold) {
      return [];
    }

    const alerts: DriftAlert[] = [];
    const severityOrder: DriftSeverity[] = ['critical', 'high', 'medium', 'low'];

    const maxSeverity = severityOrder.find(
      s => events.some(e => e.severity === s),
    ) ?? 'low';

    const affectedFrameworks = [...new Set(events.map(e => e.framework))];

    alerts.push({
      id: randomUUID(),
      timestamp: new Date().toISOString(),
      priority: priorityFromSeverity(maxSeverity),
      driftEvents: events,
      summary: `${events.length} drift event(s) detected across ${affectedFrameworks.length} framework(s). Score delta: ${overallDelta > 0 ? '-' : '+'}${Math.abs(overallDelta).toFixed(1)}%`,
      affectedFrameworks,
      affectedControlCount: new Set(events.map(e => e.controlId)).size,
      maxSeverity,
      overallScoreDelta: Math.round(overallDelta * 100) / 100,
    });

    return alerts;
  }

  private computeHash(controls: ControlSnapshot[]): string {
    const payload = JSON.stringify(
      controls.map(c => `${c.controlId}:${c.status}:${c.evidenceCount}:${c.complianceScore}`).sort(),
    );
    return createHash('sha256').update(payload).digest('hex');
  }
}
