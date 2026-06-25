import { randomUUID } from "node:crypto";
import type {
  ComplianceBaseline,
  ControlBaseline,
  DriftEvent,
  DriftType,
  DriftSeverity,
  FrameworkCode,
  CompliancePosture,
  ControlPosture,
  RiskArea,
  MonitorConfig,
  ComplianceSnapshot,
} from "../types.js";

export interface BaselineStore {
  getBaseline(tenantId: string, frameworkCode: string): Promise<ComplianceBaseline | undefined>;
  saveBaseline(baseline: ComplianceBaseline): Promise<void>;
  listBaselines(tenantId: string): Promise<ComplianceBaseline[]>;
}

export interface EvidenceIntegrityChecker {
  verifyEvidence(evidenceHash: string, uri: string): Promise<boolean>;
  getCurrentEvidence(controlId: string, tenantId: string): Promise<{ hash: string; uri: string }[]>;
}

export interface DriftDetectorConfig {
  checkIntervalMs: number;
  evidenceVerificationEnabled: boolean;
  configChangeDetection: boolean;
  accessLogAnalysis: boolean;
  maxDriftAge: number;
}

const DEFAULT_CONFIG: DriftDetectorConfig = {
  checkIntervalMs: 60_000,
  evidenceVerificationEnabled: true,
  configChangeDetection: true,
  accessLogAnalysis: true,
  maxDriftAge: 30 * 24 * 60 * 60 * 1000,
};

export class RealTimeDriftDetector {
  private baselines: Map<string, ComplianceBaseline> = new Map();
  private driftEvents: DriftEvent[] = [];
  private evidenceChecker: EvidenceIntegrityChecker;
  private config: DriftDetectorConfig;

  constructor(evidenceChecker: EvidenceIntegrityChecker, config: Partial<DriftDetectorConfig> = {}) {
    this.evidenceChecker = evidenceChecker;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async loadBaseline(baseline: ComplianceBaseline): Promise<void> {
    const key = `${baseline.tenantId}:${baseline.frameworkCode}`;
    this.baselines.set(key, baseline);
  }

  async detectDrift(tenantId: string, frameworkCode: FrameworkCode): Promise<DriftEvent[]> {
    const key = `${tenantId}:${frameworkCode}`;
    const baseline = this.baselines.get(key);
    if (!baseline) return [];

    const newDrifts: DriftEvent[] = [];

    for (const control of baseline.controls) {
      const currentEvidence = await this.evidenceChecker.getCurrentEvidence(control.controlId, tenantId);

      if (this.config.evidenceVerificationEnabled) {
        const evidenceDrift = await this.checkEvidenceIntegrity(tenantId, frameworkCode, control, currentEvidence);
        if (evidenceDrift) newDrifts.push(evidenceDrift);
      }

      const statusDrift = await this.checkControlStatus(tenantId, frameworkCode, control);
      if (statusDrift) newDrifts.push(statusDrift);
    }

    this.driftEvents.push(...newDrifts);
    return newDrifts;
  }

  private async checkEvidenceIntegrity(
    tenantId: string,
    frameworkCode: FrameworkCode,
    control: ControlBaseline,
    currentEvidence: { hash: string; uri: string }[]
  ): Promise<DriftEvent | null> {
    for (const expectedHash of control.evidenceHashes) {
      const found = currentEvidence.some((e) => e.hash === expectedHash);
      if (!found) {
        return this.createDriftEvent(tenantId, frameworkCode, control, "evidence_missing", "high",
          `Expected evidence hash ${expectedHash.slice(0, 12)}... not found for control ${control.controlCode}`);
      }
    }

    for (const evidence of currentEvidence) {
      const isValid = await this.evidenceChecker.verifyEvidence(evidence.hash, evidence.uri);
      if (!isValid) {
        return this.createDriftEvent(tenantId, frameworkCode, control, "evidence_tampered", "critical",
          `Evidence integrity check failed for control ${control.controlCode}: hash mismatch`);
      }
    }

    return null;
  }

  private async checkControlStatus(
    tenantId: string,
    frameworkCode: FrameworkCode,
    control: ControlBaseline
  ): Promise<DriftEvent | null> {
    if (control.expectedStatus === "implemented") {
      const lastVerified = new Date(control.lastVerifiedAt).getTime();
      const age = Date.now() - lastVerified;
      if (age > this.config.maxDriftAge) {
        return this.createDriftEvent(tenantId, frameworkCode, control, "control_disabled", "medium",
          `Control ${control.controlCode} has not been verified in ${Math.floor(age / 86400000)} days`);
      }
    }
    return null;
  }

  private createDriftEvent(
    tenantId: string,
    frameworkCode: FrameworkCode,
    control: ControlBaseline,
    driftType: DriftType,
    severity: DriftSeverity,
    description: string
  ): DriftEvent {
    return {
      id: randomUUID(),
      tenantId,
      frameworkCode,
      controlId: control.controlId,
      controlCode: control.controlCode,
      detectedAt: new Date().toISOString(),
      severity,
      driftType,
      description,
      remediable: severity !== "critical",
      autoRemediation: severity === "low" ? "alert" : undefined,
      resolved: false,
    };
  }

  getDriftEvents(tenantId: string, frameworkCode?: string): DriftEvent[] {
    return this.driftEvents.filter(
      (e) => e.tenantId === tenantId && (!frameworkCode || e.frameworkCode === frameworkCode)
    );
  }

  getUnresolvedDrifts(tenantId: string): DriftEvent[] {
    return this.driftEvents.filter((e) => e.tenantId === tenantId && !e.resolved);
  }

  resolveDrift(driftId: string, resolvedBy: string): boolean {
    const drift = this.driftEvents.find((e) => e.id === driftId);
    if (!drift) return false;
    drift.resolved = true;
    drift.resolvedAt = new Date().toISOString();
    drift.resolvedBy = resolvedBy;
    return true;
  }
}
