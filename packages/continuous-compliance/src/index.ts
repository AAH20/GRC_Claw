import type { FrameworkCode } from "./types.js";
import type {
  ComplianceBaseline,
  DriftEvent,
  CompliancePosture,
  RemediationPlan,
  MonitorConfig,
  ComplianceSnapshot,
} from "./types.js";
import { RealTimeDriftDetector, type EvidenceIntegrityChecker } from "./monitors/RealTimeDriftDetector.js";
import { CompliancePostureMonitor } from "./monitors/CompliancePostureMonitor.js";
import { AutoRemediationEngine, type RemediationExecutor } from "./remediation/AutoRemediationEngine.js";

export interface ContinuousComplianceConfig {
  monitorIntervalMs: number;
  autoRemediate: boolean;
  maxAutoRemediationSeverity: "low" | "medium" | "high" | "critical";
  alertChannels: string[];
}

const DEFAULT_CONFIG: ContinuousComplianceConfig = {
  monitorIntervalMs: 60_000,
  autoRemediate: true,
  maxAutoRemediationSeverity: "medium",
  alertChannels: ["console"],
};

export class ContinuousComplianceEngine {
  private driftDetector: RealTimeDriftDetector;
  private postureMonitor: CompliancePostureMonitor;
  private remediationEngine: AutoRemediationEngine;
  private monitors: Map<string, MonitorConfig> = new Map();
  private config: ContinuousComplianceConfig;
  private intervals: Map<string, ReturnType<typeof setInterval>> = new Map();

  constructor(
    evidenceChecker: EvidenceIntegrityChecker,
    remediationExecutor: RemediationExecutor,
    config: Partial<ContinuousComplianceConfig> = {}
  ) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.driftDetector = new RealTimeDriftDetector(evidenceChecker);
    this.postureMonitor = new CompliancePostureMonitor();
    this.remediationEngine = new AutoRemediationEngine(remediationExecutor, {
      maxAutoRemediationSeverity: this.config.maxAutoRemediationSeverity,
    });
  }

  async loadBaseline(baseline: ComplianceBaseline): Promise<void> {
    await this.driftDetector.loadBaseline(baseline);
  }

  registerMonitor(config: MonitorConfig): void {
    this.monitors.set(config.id, config);
  }

  async startMonitoring(): Promise<void> {
    for (const [id, config] of this.monitors) {
      if (!config.enabled) continue;

      const interval = setInterval(async () => {
        await this.runMonitoringCycle(config);
      }, config.intervalMs || this.config.monitorIntervalMs);

      this.intervals.set(id, interval);
    }
  }

  stopMonitoring(): void {
    for (const [id, interval] of this.intervals) {
      clearInterval(interval);
    }
    this.intervals.clear();
  }

  async runMonitoringCycle(config: MonitorConfig): Promise<{
    drifts: DriftEvent[];
    posture: CompliancePosture;
    remediations: RemediationPlan[];
  }> {
    const allDrifts: DriftEvent[] = [];
    const remediations: RemediationPlan[] = [];

    for (const frameworkCode of config.frameworkCodes) {
      const drifts = await this.driftDetector.detectDrift(config.tenantId, frameworkCode);
      allDrifts.push(...drifts);

      if (this.config.autoRemediate && config.autoRemediate) {
        for (const drift of drifts) {
          if (this.remediationEngine.canAutoRemediate(drift)) {
            const plan = this.remediationEngine.createRemediationPlan(drift);
            remediations.push(plan);
          }
        }
      }
    }

    const posture = this.calculateCurrentPosture(config.tenantId, config.frameworkCodes[0]);

    return { drifts: allDrifts, posture, remediations };
  }

  private calculateCurrentPosture(tenantId: string, frameworkCode: FrameworkCode): CompliancePosture {
    const drifts = this.driftDetector.getDriftEvents(tenantId, frameworkCode);
    return this.postureMonitor.calculatePosture({
      tenantId,
      frameworkCode,
      controlStatuses: new Map(),
      driftEvents: drifts,
    });
  }

  async takeSnapshot(tenantId: string, frameworkCode: FrameworkCode): Promise<ComplianceSnapshot> {
    const drifts = this.driftDetector.getDriftEvents(tenantId, frameworkCode);
    const posture = this.calculateCurrentPosture(tenantId, frameworkCode);

    return {
      id: `snapshot-${Date.now()}`,
      tenantId,
      frameworkCode,
      timestamp: new Date().toISOString(),
      overallScore: posture.overallScore,
      controlCount: posture.controlScores.size,
      passingControls: Array.from(posture.controlScores.values()).filter((c) => c.status === "healthy").length,
      failingControls: Array.from(posture.controlScores.values()).filter((c) => c.status === "critical").length,
      driftEvents: drifts,
    };
  }

  getDriftDetector(): RealTimeDriftDetector {
    return this.driftDetector;
  }

  getPostureMonitor(): CompliancePostureMonitor {
    return this.postureMonitor;
  }

  getRemediationEngine(): AutoRemediationEngine {
    return this.remediationEngine;
  }
}

export { RealTimeDriftDetector } from "./monitors/RealTimeDriftDetector.js";
export { CompliancePostureMonitor } from "./monitors/CompliancePostureMonitor.js";
export { AutoRemediationEngine } from "./remediation/AutoRemediationEngine.js";
export type * from "./types.js";
