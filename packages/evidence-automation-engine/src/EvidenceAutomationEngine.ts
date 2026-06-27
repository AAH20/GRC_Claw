import {
  type EvidenceArtifact,
  type CollectionSchedule,
  type CollectionJob,
  type ScheduleConfig,
  type EvidenceGap,
  type EvidenceSummaryReport,
  type EvidenceStore,
  type ComplianceFramework,
  type EvidenceFreshness,
  hashData,
  generateId,
  computeNextRun,
  assessFreshness,
  getControlFrameworkMap,
} from "./types.js";

export interface ConnectorAdapter {
  collectEvidence(): Promise<EvidenceArtifact[]>;
  testConnection(): Promise<boolean>;
}

export interface EvidenceAutomationConfig {
  defaultFreshnessHours?: number;
  staleThresholdHours?: number;
}

class InMemoryEvidenceStore implements EvidenceStore {
  artifacts = new Map<string, EvidenceArtifact>();

  add(artifact: EvidenceArtifact): void {
    this.artifacts.set(artifact.id, artifact);
  }

  get(id: string): EvidenceArtifact | undefined {
    return this.artifacts.get(id);
  }

  getAll(): EvidenceArtifact[] {
    return Array.from(this.artifacts.values());
  }

  getByConnector(connectorId: string): EvidenceArtifact[] {
    return this.getAll().filter((a) => a.connectorId === connectorId);
  }

  getByControl(controlId: string): EvidenceArtifact[] {
    return this.getAll().filter((a) => a.controlId === controlId);
  }

  getByFramework(framework: ComplianceFramework): EvidenceArtifact[] {
    return this.getAll().filter((a) => a.framework === framework);
  }

  remove(id: string): boolean {
    return this.artifacts.delete(id);
  }

  get size(): number {
    return this.artifacts.size;
  }
}

export class EvidenceAutomationEngine {
  private store: EvidenceStore;
  private schedules: Map<string, CollectionSchedule> = new Map();
  private jobsArray: CollectionJob[] = [];
  private connectors: Map<string, ConnectorAdapter> = new Map();
  private timers: Map<string, ReturnType<typeof setTimeout>> = new Map();
  private config: EvidenceAutomationConfig;
  private runLoopActive = false;

  constructor(config: EvidenceAutomationConfig = {}) {
    this.store = new InMemoryEvidenceStore();
    this.config = {
      defaultFreshnessHours: config.defaultFreshnessHours ?? 24 * 30,
      staleThresholdHours: config.staleThresholdHours ?? 24 * 14,
    };
  }

  registerConnector(id: string, adapter: ConnectorAdapter): void {
    this.connectors.set(id, adapter);
  }

  unregisterConnector(id: string): void {
    this.connectors.delete(id);
    for (const [scheduleId, s] of this.schedules) {
      if (s.connectorId === id) this.schedules.delete(scheduleId);
    }
  }

  createSchedule(connectorId: string, config: ScheduleConfig): CollectionSchedule {
    if (!this.connectors.has(connectorId)) {
      throw new Error(`Connector not registered: ${connectorId}`);
    }
    const schedule: CollectionSchedule = {
      id: generateId("sched"),
      connectorId,
      config,
      enabled: true,
      nextRunAt: computeNextRun(config),
    };
    this.schedules.set(schedule.id, schedule);
    return schedule;
  }

  updateSchedule(scheduleId: string, updates: Partial<CollectionSchedule>): CollectionSchedule | null {
    const schedule = this.schedules.get(scheduleId);
    if (!schedule) return null;
    if (updates.config) {
      schedule.config = updates.config;
      schedule.nextRunAt = computeNextRun(updates.config, schedule.lastRunAt);
    }
    if (updates.enabled !== undefined) schedule.enabled = updates.enabled;
    return schedule;
  }

  deleteSchedule(scheduleId: string): boolean {
    const timer = this.timers.get(scheduleId);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(scheduleId);
    }
    return this.schedules.delete(scheduleId);
  }

  getSchedules(): CollectionSchedule[] {
    return Array.from(this.schedules.values());
  }

  getSchedule(scheduleId: string): CollectionSchedule | undefined {
    return this.schedules.get(scheduleId);
  }

  async collectFromConnector(connectorId: string): Promise<CollectionJob> {
    const adapter = this.connectors.get(connectorId);
    if (!adapter) throw new Error(`Connector not found: ${connectorId}`);

    const job: CollectionJob = {
      id: generateId("job"),
      connectorId,
      startedAt: new Date().toISOString(),
      status: "running",
      artifacts: [],
    };
    this.jobsArray.push(job);

    try {
      const artifacts = await adapter.collectEvidence();
      for (const artifact of artifacts) {
        this.store.add(artifact);
      }
      job.artifacts = artifacts;
      job.status = "completed";
      job.completedAt = new Date().toISOString();
      job.duration =
        new Date(job.completedAt).getTime() - new Date(job.startedAt).getTime();
    } catch (err) {
      job.status = "failed";
      job.completedAt = new Date().toISOString();
      job.error = err instanceof Error ? err.message : String(err);
      job.duration =
        new Date(job.completedAt).getTime() - new Date(job.startedAt).getTime();
    }

    const schedule = Array.from(this.schedules.values()).find(
      (s) => s.connectorId === connectorId
    );
    if (schedule) {
      schedule.lastRunAt = job.completedAt;
      schedule.lastJobId = job.id;
      schedule.nextRunAt = computeNextRun(schedule.config, schedule.lastRunAt);
    }

    return job;
  }

  async collectAll(): Promise<CollectionJob[]> {
    const jobs: CollectionJob[] = [];
    for (const connectorId of this.connectors.keys()) {
      jobs.push(await this.collectFromConnector(connectorId));
    }
    return jobs;
  }

  startScheduler(): void {
    if (this.runLoopActive) return;
    this.runLoopActive = true;
    this.runLoop();
  }

  stopScheduler(): void {
    this.runLoopActive = false;
    for (const timer of this.timers.values()) {
      clearTimeout(timer);
    }
    this.timers.clear();
  }

  private runLoop(): void {
    if (!this.runLoopActive) return;

    const now = new Date();
    for (const schedule of this.schedules.values()) {
      if (!schedule.enabled || !schedule.nextRunAt) continue;
      const nextRun = new Date(schedule.nextRunAt);
      if (nextRun <= now) {
        this.collectFromConnector(schedule.connectorId).catch(() => {});
      }
    }

    setTimeout(() => this.runLoop(), 60_000);
  }

  detectGaps(): EvidenceGap[] {
    const controlMap = getControlFrameworkMap();
    const gaps: EvidenceGap[] = [];

    for (const [controlId, frameworks] of Object.entries(controlMap)) {
      for (const framework of frameworks) {
        const evidence = this.store.getByFramework(framework).filter(
          (a) => a.controlId === controlId
        );

        if (evidence.length === 0) {
          gaps.push({
            controlId,
            framework,
            requiredBy: this.getConnectorIdsForControl(controlId),
            freshness: "missing",
            connectors: [],
            recommendation: `No evidence collected for control ${controlId}. Configure a connector to collect this evidence.`,
          });
          continue;
        }

        const latest = evidence.sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )[0];

        const freshness = assessFreshness(latest, this.config.defaultFreshnessHours);
        if (freshness === "expired") {
          gaps.push({
            controlId,
            framework,
            requiredBy: this.getConnectorIdsForControl(controlId),
            lastCollectedAt: latest.timestamp,
            freshness,
            connectors: [...new Set(evidence.map((e) => e.connectorId))],
            recommendation: `Evidence for control ${controlId} is expired. Re-collect immediately.`,
          });
        } else if (freshness === "stale") {
          gaps.push({
            controlId,
            framework,
            requiredBy: this.getConnectorIdsForControl(controlId),
            lastCollectedAt: latest.timestamp,
            freshness,
            connectors: [...new Set(evidence.map((e) => e.connectorId))],
            recommendation: `Evidence for control ${controlId} is stale. Schedule more frequent collection.`,
          });
        }
      }
    }

    return gaps;
  }

  private getConnectorIdsForControl(controlId: string): string[] {
    return Array.from(this.connectors.keys()).filter((id) => {
      const evidence = this.store.getByConnector(id);
      return evidence.some((e) => e.controlId === controlId);
    });
  }

  generateSummaryReport(): EvidenceSummaryReport {
    const artifacts = this.store.getAll();
    const byFramework: Record<string, number> = {};
    const byStatus: Record<string, number> = {};
    const freshness: Record<string, number> = { fresh: 0, stale: 0, expired: 0, missing: 0 };

    for (const artifact of artifacts) {
      byFramework[artifact.framework] = (byFramework[artifact.framework] || 0) + 1;
      byStatus[artifact.status] = (byStatus[artifact.status] || 0) + 1;
      const f = assessFreshness(artifact, this.config.defaultFreshnessHours);
      freshness[f] = (freshness[f] || 0) + 1;
    }

    const gaps = this.detectGaps();
    const controlMap = getControlFrameworkMap();
    const totalControls = Object.keys(controlMap).length;
    const coveredControls = new Set(
      artifacts.map((a) => a.controlId)
    ).size;

    return {
      generatedAt: new Date().toISOString(),
      totalArtifacts: artifacts.length,
      artifactsByFramework: byFramework as Record<ComplianceFramework, number>,
      artifactsByStatus: byStatus,
      gaps,
      totalGaps: gaps.length,
      freshness: freshness as { fresh: number; stale: number; expired: number; missing: number },
      coveragePercentage: totalControls > 0 ? Math.round((coveredControls / totalControls) * 100) : 0,
    };
  }

  getStore(): EvidenceStore {
    return this.store;
  }

  getJobs(): CollectionJob[] {
    return [...this.jobsArray];
  }

  getRecentJobs(limit = 10): CollectionJob[] {
    return this.jobsArray.slice(-limit);
  }

  clearStore(): void {
    const inMem = this.store as InMemoryEvidenceStore;
    inMem.artifacts.clear();
  }
}
