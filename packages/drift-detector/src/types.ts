import { createHash } from 'node:crypto';

// ─── Core Types ─────────────────────────────────────────────────────

export type ControlStatus = 'compliant' | 'non_compliant' | 'partial' | 'unknown';
export type DriftSeverity = 'critical' | 'high' | 'medium' | 'low';
export type DriftEventType = 'evidence_revoked' | 'control_downgraded' | 'evidence_expired' | 'new_gap' | 'score_degradation' | 'status_change';
export type AlertPriority = 'p1' | 'p2' | 'p3' | 'p4';

export interface ControlSnapshot {
  controlId: string;
  framework: string;
  status: ControlStatus;
  evidenceHashes: string[];
  evidenceCount: number;
  complianceScore: number;
  lastCheckedAt: string;
  metadata?: Record<string, unknown>;
}

export interface DriftEvent {
  id: string;
  timestamp: string;
  controlId: string;
  framework: string;
  eventType: DriftEventType;
  previousStatus: ControlStatus;
  currentStatus: ControlStatus;
  previousEvidenceCount: number;
  currentEvidenceCount: number;
  previousScore: number;
  currentScore: number;
  delta: number;
  severity: DriftSeverity;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface DriftAlert {
  id: string;
  timestamp: string;
  priority: AlertPriority;
  driftEvents: DriftEvent[];
  summary: string;
  affectedFrameworks: string[];
  affectedControlCount: number;
  maxSeverity: DriftSeverity;
  overallScoreDelta: number;
}

export interface BaselineSnapshot {
  id: string;
  capturedAt: string;
  controls: ControlSnapshot[];
  overallScore: number;
  frameworkScores: Record<string, number>;
  controlCount: number;
  compliantCount: number;
  hash: string;
}

export interface DriftDetectionResult {
  snapshotId: string;
  baselineId: string;
  detectedAt: string;
  driftEvents: DriftEvent[];
  driftDetected: boolean;
  overallScoreDelta: number;
  currentScore: number;
  baselineScore: number;
  alerts: DriftAlert[];
}

export interface DriftDetectorConfig {
  tenantId: number;
  frameworks: string[];
  driftThresholdPercent?: number;
  scoreDeltaAlertThreshold?: number;
  pollIntervalMs?: number;
  maxBaselineHistory?: number;
  onDrift?: (events: DriftEvent[]) => void;
  onAlert?: (alert: DriftAlert) => void;
}

export interface ControlEvaluator {
  evaluateControl(controlId: string, framework: string): Promise<ControlSnapshot>;
  listControls(framework: string): Promise<Array<{ controlId: string; title: string }>>;
}
