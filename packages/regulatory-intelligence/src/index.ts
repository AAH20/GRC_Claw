import type { FrameworkCode } from "./types.js";
import type {
  RegulatorySource,
  RegulatoryChange,
  RegulatoryDigest,
  MonitoringConfig,
  ChangeType,
  ImpactLevel,
} from "./types.js";
import { RegulatoryChangeDetector } from "./detectors/RegulatoryChangeDetector.js";
import { RegulatoryImpactAnalyzer } from "./analysis/RegulatoryImpactAnalyzer.js";

export interface RegulatoryIntelligenceConfig extends Partial<MonitoringConfig> {
  autoAnalyze: boolean;
  autoDigest: boolean;
}

const DEFAULT_CONFIG: RegulatoryIntelligenceConfig = {
  defaultPollingIntervalMs: 3600000,
  maxConcurrentFetches: 5,
  changeDetectionThreshold: 0.85,
  alertOnCritical: true,
  digestSchedule: "weekly",
  autoAnalyze: true,
  autoDigest: true,
};

export class RegulatoryIntelligenceEngine {
  private sources: Map<string, RegulatorySource> = new Map();
  private changes: RegulatoryChange[] = [];
  private digests: RegulatoryDigest[] = [];
  private changeDetector: RegulatoryChangeDetector;
  private impactAnalyzer: RegulatoryImpactAnalyzer;
  private config: MonitoringConfig;

  constructor(config: Partial<RegulatoryIntelligenceConfig> = {}) {
    const fullConfig = { ...DEFAULT_CONFIG, ...config };
    this.config = {
      defaultPollingIntervalMs: fullConfig.defaultPollingIntervalMs!,
      maxConcurrentFetches: fullConfig.maxConcurrentFetches!,
      changeDetectionThreshold: fullConfig.changeDetectionThreshold!,
      alertOnCritical: fullConfig.alertOnCritical!,
      digestSchedule: fullConfig.digestSchedule!,
    };
    this.changeDetector = new RegulatoryChangeDetector({ similarityThreshold: fullConfig.changeDetectionThreshold });
    this.impactAnalyzer = new RegulatoryImpactAnalyzer();
  }

  registerSource(source: RegulatorySource): void {
    this.sources.set(source.id, source);
  }

  deregisterSource(sourceId: string): boolean {
    return this.sources.delete(sourceId);
  }

  async checkForChanges(
    sourceId: string,
    contentFetcher: (url: string) => Promise<string>
  ): Promise<RegulatoryChange | null> {
    const source = this.sources.get(sourceId);
    if (!source) return null;

    const content = await contentFetcher(source.url);
    const detectionResult = await this.changeDetector.detectChange(source, content);

    if (!detectionResult.hasChange) return null;

    const change: RegulatoryChange = {
      id: `change-${Date.now()}`,
      sourceId: source.id,
      title: `Regulatory Update: ${source.name}`,
      summary: detectionResult.diffSummary || "Content changed",
      fullText: content,
      detectedAt: new Date().toISOString(),
      changeType: detectionResult.changeType || "amendment",
      jurisdiction: source.jurisdiction,
      framework: source.framework,
      affectedControls: [],
      impactLevel: "moderate",
      impactAnalysis: {
        affectedControls: [],
        overallImpact: "moderate",
        estimatedRemediationDays: 0,
        complianceGapScore: 0,
        recommendedActions: [],
        crossFrameworkImpact: [],
      },
      status: "detected",
    };

    this.changes.push(change);
    source.lastCheckedAt = new Date().toISOString();

    return change;
  }

  async analyzeChange(
    changeId: string,
    currentControls: Map<string, { controlId: string; controlCode: string; framework: FrameworkCode; status: string }>
  ): Promise<RegulatoryChange | null> {
    const change = this.changes.find((c) => c.id === changeId);
    if (!change) return null;

    const analysis = this.impactAnalyzer.analyzeImpact(change, currentControls);
    change.impactAnalysis = analysis;
    change.affectedControls = analysis.affectedControls.map((c) => c.controlCode);
    change.impactLevel = analysis.overallImpact;
    change.status = "analyzed";

    return change;
  }

  generateDigest(
    jurisdiction: string,
    periodFrom: string,
    periodTo: string
  ): RegulatoryDigest {
    const periodChanges = this.changes.filter(
      (c) =>
        c.jurisdiction === jurisdiction &&
        c.detectedAt >= periodFrom &&
        c.detectedAt <= periodTo
    );

    const totalImpactScore = periodChanges.reduce((sum, c) => {
      const impactScores = { critical: 4, significant: 3, moderate: 2, minimal: 1, none: 0 };
      return sum + (impactScores[c.impactLevel] || 0);
    }, 0);

    const priorityActions = periodChanges
      .filter((c) => c.impactLevel === "critical" || c.impactLevel === "significant")
      .flatMap((c) => c.impactAnalysis.recommendedActions.slice(0, 2));

    const digest: RegulatoryDigest = {
      id: `digest-${Date.now()}`,
      generatedAt: new Date().toISOString(),
      period: { from: periodFrom, to: periodTo },
      jurisdiction,
      changes: periodChanges,
      summary: `Detected ${periodChanges.length} regulatory changes with total impact score ${totalImpactScore}`,
      priorityActions: [...new Set(priorityActions)],
      totalImpactScore,
    };

    this.digests.push(digest);
    return digest;
  }

  getChangesByFramework(framework: FrameworkCode): RegulatoryChange[] {
    return this.changes.filter((c) => c.framework === framework);
  }

  getChangesByImpact(impact: ImpactLevel): RegulatoryChange[] {
    return this.changes.filter((c) => c.impactLevel === impact);
  }

  getChangesByType(type: ChangeType): RegulatoryChange[] {
    return this.changes.filter((c) => c.changeType === type);
  }

  getCriticalChanges(): RegulatoryChange[] {
    return this.getChangesByImpact("critical");
  }

  getSources(): RegulatorySource[] {
    return Array.from(this.sources.values());
  }

  getDigests(jurisdiction?: string): RegulatoryDigest[] {
    if (jurisdiction) return this.digests.filter((d) => d.jurisdiction === jurisdiction);
    return this.digests;
  }

  getChangeDetector(): RegulatoryChangeDetector {
    return this.changeDetector;
  }

  getImpactAnalyzer(): RegulatoryImpactAnalyzer {
    return this.impactAnalyzer;
  }

  getStats(): {
    totalSources: number;
    activeSources: number;
    totalChanges: number;
    criticalChanges: number;
    totalDigests: number;
  } {
    const sources = Array.from(this.sources.values());
    return {
      totalSources: sources.length,
      activeSources: sources.filter((s) => s.status === "active").length,
      totalChanges: this.changes.length,
      criticalChanges: this.getCriticalChanges().length,
      totalDigests: this.digests.length,
    };
  }
}

export { RegulatoryChangeDetector } from "./detectors/RegulatoryChangeDetector.js";
export { RegulatoryImpactAnalyzer } from "./analysis/RegulatoryImpactAnalyzer.js";
export type * from "./types.js";
