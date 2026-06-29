/**
 * @grc-claw/compliance-intelligence-api
 *
 * Real-time compliance intelligence API that aggregates data from across the
 * GRC_Claw network to deliver trend analysis, competitive benchmarking,
 * risk scoring, anomaly detection, and actionable recommendations.
 */

// ---------------------------------------------------------------------------
// Types & Enums
// ---------------------------------------------------------------------------

export type OrganizationId = string;
export type FrameworkId = string;
export type ControlId = string;
export type Timestamp = string;

export enum ComplianceStatus {
  Compliant = "compliant",
  NonCompliant = "non_compliant",
  Partial = "partial",
  NotAssessed = "not_assessed",
}

export enum RiskSeverity {
  Critical = "critical",
  High = "high",
  Medium = "medium",
  Low = "low",
  Informational = "informational",
}

export enum TrendDirection {
  Improving = "improving",
  Declining = "declining",
  Stable = "stable",
}

export interface ComplianceRecord {
  organizationId: OrganizationId;
  frameworkId: FrameworkId;
  controlId: ControlId;
  status: ComplianceStatus;
  score: number;
  assessedAt: Timestamp;
  assessor?: string;
  evidence?: string;
  metadata?: Record<string, unknown>;
}

export interface TrendPoint {
  period: Timestamp;
  score: number;
  records: number;
}

export interface TrendResult {
  frameworkId: FrameworkId;
  direction: TrendDirection;
  points: TrendPoint[];
  slope: number;
  projectedNext: number;
  confidence: number;
}

export interface BenchmarkEntry {
  organizationId: OrganizationId;
  organizationName: string;
  overallScore: number;
  frameworkScores: Record<FrameworkId, number>;
  rank: number;
  percentile: number;
}

export interface BenchmarkResult {
  frameworkId: FrameworkId;
  networkAverage: number;
  networkMedian: number;
  entries: BenchmarkEntry[];
  generatedAt: Timestamp;
}

export interface RiskScore {
  organizationId: OrganizationId;
  overallRisk: number;
  frameworkRisks: Record<FrameworkId, number>;
  topRisks: RiskItem[];
  generatedAt: Timestamp;
}

export interface RiskItem {
  controlId: ControlId;
  frameworkId: FrameworkId;
  severity: RiskSeverity;
  score: number;
  description: string;
  mitigation?: string;
}

export interface Anomaly {
  id: string;
  organizationId: OrganizationId;
  frameworkId: FrameworkId;
  controlId: ControlId;
  type: anomalyType;
  severity: RiskSeverity;
  description: string;
  detectedAt: Timestamp;
  expectedValue: number;
  actualValue: number;
}

export enum anomalyType {
  SuddenDrop = "sudden_drop",
  SuddenSpike = "sudden_spike",
  Stagnation = "stagnation",
  Inconsistency = "inconsistency",
  OutOfPattern = "out_of_pattern",
}

export interface Recommendation {
  id: string;
  organizationId: OrganizationId;
  priority: RiskSeverity;
  category: string;
  title: string;
  description: string;
  controls: ControlId[];
  frameworkIds: FrameworkId[];
  estimatedImpact: number;
  generatedAt: Timestamp;
}

export interface NetworkSnapshot {
  totalOrganizations: number;
  totalFrameworks: number;
  totalControls: number;
  averageScore: number;
  complianceDistribution: Record<ComplianceStatus, number>;
  timestamp: Timestamp;
}

// ---------------------------------------------------------------------------
// IntelligenceAggregator – collects and normalises data from the network
// ---------------------------------------------------------------------------

export class IntelligenceAggregator {
  private records: ComplianceRecord[] = [];
  private orgIndex: Map<OrganizationId, ComplianceRecord[]> = new Map();
  private frameworkIndex: Map<FrameworkId, ComplianceRecord[]> = new Map();

  /** Ingest a batch of compliance records. */
  ingest(batch: ComplianceRecord[]): void {
    for (const record of batch) {
      this.records.push(record);

      const orgBucket = this.orgIndex.get(record.organizationId) ?? [];
      orgBucket.push(record);
      this.orgIndex.set(record.organizationId, orgBucket);

      const fwBucket = this.frameworkIndex.get(record.frameworkId) ?? [];
      fwBucket.push(record);
      this.frameworkIndex.set(record.frameworkId, fwBucket);
    }
  }

  /** Return all records for a given organization. */
  getRecordsForOrg(orgId: OrganizationId): ComplianceRecord[] {
    return this.orgIndex.get(orgId) ?? [];
  }

  /** Return all records for a given framework. */
  getRecordsForFramework(fwId: FrameworkId): ComplianceRecord[] {
    return this.frameworkIndex.get(fwId) ?? [];
  }

  /** Return the full dataset. */
  getAllRecords(): ComplianceRecord[] {
    return this.records;
  }

  /** Build a snapshot of the entire network. */
  snapshot(): NetworkSnapshot {
    const totalOrganizations = this.orgIndex.size;
    const totalFrameworks = this.frameworkIndex.size;
    const totalControls = this.records.length;

    const distribution: Record<ComplianceStatus, number> = {
      [ComplianceStatus.Compliant]: 0,
      [ComplianceStatus.NonCompliant]: 0,
      [ComplianceStatus.Partial]: 0,
      [ComplianceStatus.NotAssessed]: 0,
    };

    let scoreSum = 0;
    for (const r of this.records) {
      distribution[r.status] += 1;
      scoreSum += r.score;
    }

    return {
      totalOrganizations,
      totalFrameworks,
      totalControls,
      averageScore: totalControls > 0 ? scoreSum / totalControls : 0,
      complianceDistribution: distribution,
      timestamp: new Date().toISOString(),
    };
  }

  /** Compute the mean score for a framework across the network. */
  frameworkAverage(fwId: FrameworkId): number {
    const recs = this.frameworkIndex.get(fwId) ?? [];
    if (recs.length === 0) return 0;
    return recs.reduce((sum, r) => sum + r.score, 0) / recs.length;
  }

  /** Compute the mean score for an organization across all frameworks. */
  orgAverage(orgId: OrganizationId): number {
    const recs = this.orgIndex.get(orgId) ?? [];
    if (recs.length === 0) return 0;
    return recs.reduce((sum, r) => sum + r.score, 0) / recs.length;
  }

  /** Return sorted unique framework IDs present in the dataset. */
  listFrameworks(): FrameworkId[] {
    return [...this.frameworkIndex.keys()].sort();
  }

  /** Return sorted unique organization IDs present in the dataset. */
  listOrganizations(): OrganizationId[] {
    return [...this.orgIndex.keys()].sort();
  }
}

// ---------------------------------------------------------------------------
// TrendAnalyzer – time-series trend analysis and forecasting
// ---------------------------------------------------------------------------

export class TrendAnalyzer {
  constructor(private readonly aggregator: IntelligenceAggregator) {}

  /**
   * Analyse the compliance score trend for a given organization + framework
   * over time. Uses simple linear regression for slope and projection.
   */
  analyzeOrgFrameworkTrend(
    orgId: OrganizationId,
    fwId: FrameworkId,
    bucketFn: (r: ComplianceRecord) => string = (r) =>
      r.assessedAt.slice(0, 7), // default: monthly bucket
  ): TrendResult {
    const records = this.aggregator
      .getRecordsForOrg(orgId)
      .filter((r) => r.frameworkId === fwId);

    const buckets = this.bucketRecords(records, bucketFn);
    const points = this.buildPoints(buckets);
    const { slope, intercept, confidence } = this.linearRegression(points);

    const lastPeriod =
      points.length > 0 ? points[points.length - 1].period : "";
    const nextIndex = points.length;

    return {
      frameworkId: fwId,
      direction: this.slopeToDirection(slope),
      points,
      slope,
      projectedNext: slope * nextIndex + intercept,
      confidence,
    };
  }

  /**
   * Analyse the overall network trend for a specific framework.
   */
  analyzeNetworkTrend(
    fwId: FrameworkId,
    bucketFn: (r: ComplianceRecord) => string = (r) =>
      r.assessedAt.slice(0, 7),
  ): TrendResult {
    const records = this.aggregator.getRecordsForFramework(fwId);
    const buckets = this.bucketRecords(records, bucketFn);
    const points = this.buildPoints(buckets);
    const { slope, intercept, confidence } = this.linearRegression(points);

    const nextIndex = points.length;

    return {
      frameworkId: fwId,
      direction: this.slopeToDirection(slope),
      points,
      slope,
      projectedNext: slope * nextIndex + intercept,
      confidence,
    };
  }

  /**
   * Return trends for every framework the aggregator knows about.
   */
  analyzeAllFrameworks(
    bucketFn?: (r: ComplianceRecord) => string,
  ): TrendResult[] {
    return this.aggregator
      .listFrameworks()
      .map((fw) => this.analyzeNetworkTrend(fw, bucketFn));
  }

  // ---- private helpers ----------------------------------------------------

  private bucketRecords(
    records: ComplianceRecord[],
    bucketFn: (r: ComplianceRecord) => string,
  ): Map<string, ComplianceRecord[]> {
    const map = new Map<string, ComplianceRecord[]>();
    for (const r of records) {
      const key = bucketFn(r);
      const bucket = map.get(key) ?? [];
      bucket.push(r);
      map.set(key, bucket);
    }
    return map;
  }

  private buildPoints(
    buckets: Map<string, ComplianceRecord[]>,
  ): TrendPoint[] {
    return [...buckets.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([period, recs]) => ({
        period,
        score:
          recs.reduce((s, r) => s + r.score, 0) / recs.length,
        records: recs.length,
      }));
  }

  private linearRegression(points: TrendPoint[]): {
    slope: number;
    intercept: number;
    confidence: number;
  } {
    const n = points.length;
    if (n < 2) return { slope: 0, intercept: points[0]?.score ?? 0, confidence: 0 };

    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumX2 = 0;
    let sumY2 = 0;

    for (let i = 0; i < n; i++) {
      const x = i;
      const y = points[i].score;
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
      sumY2 += y * y;
    }

    const denom = n * sumX2 - sumX * sumX;
    if (denom === 0) return { slope: 0, intercept: sumY / n, confidence: 0 };

    const slope = (n * sumXY - sumX * sumY) / denom;
    const intercept = (sumY - slope * sumX) / n;

    // Pearson correlation coefficient as confidence proxy
    const numR = n * sumXY - sumX * sumY;
    const denR = Math.sqrt(
      (n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY),
    );
    const confidence = denR === 0 ? 0 : Math.abs(numR / denR);

    return { slope, intercept, confidence };
  }

  private slopeToDirection(slope: number): TrendDirection {
    if (slope > 0.01) return TrendDirection.Improving;
    if (slope < -0.01) return TrendDirection.Declining;
    return TrendDirection.Stable;
  }
}

// ---------------------------------------------------------------------------
// BenchmarkEngine – competitive benchmarking across organizations
// ---------------------------------------------------------------------------

export class BenchmarkEngine {
  constructor(private readonly aggregator: IntelligenceAggregator) {}

  /**
   * Benchmark all organizations against a specific framework.
   * Returns ranked entries with percentile information.
   */
  benchmarkByFramework(fwId: FrameworkId): BenchmarkResult {
    const orgIds = this.aggregator.listOrganizations();
    const entries: BenchmarkEntry[] = [];

    for (const orgId of orgIds) {
      const records = this.aggregator
        .getRecordsForOrg(orgId)
        .filter((r) => r.frameworkId === fwId);

      const overallScore =
        records.length > 0
          ? records.reduce((s, r) => s + r.score, 0) / records.length
          : 0;

      entries.push({
        organizationId: orgId,
        organizationName: orgId, // caller may enrich
        overallScore,
        frameworkScores: { [fwId]: overallScore },
        rank: 0,
        percentile: 0,
      });
    }

    entries.sort((a, b) => b.overallScore - a.overallScore);

    const total = entries.length || 1;
    for (let i = 0; i < entries.length; i++) {
      entries[i].rank = i + 1;
      entries[i].percentile = Math.round(((total - i) / total) * 100);
    }

    const scores = entries.map((e) => e.overallScore);
    const networkAverage =
      scores.length > 0
        ? scores.reduce((a, b) => a + b, 0) / scores.length
        : 0;
    const networkMedian = this.median(scores);

    return {
      frameworkId: fwId,
      networkAverage,
      networkMedian,
      entries,
      generatedAt: new Date().toISOString(),
    };
  }

  /**
   * Benchmark a single organization against the rest of the network.
   */
  benchmarkOrganization(
    orgId: OrganizationId,
    fwId?: FrameworkId,
  ): {
    orgScore: number;
    networkAverage: number;
    networkMedian: number;
    rank: number;
    percentile: number;
    frameworkComparisons: Record<
      FrameworkId,
      { orgScore: number; networkAvg: number; delta: number }
    >;
  } {
    const frameworks = fwId
      ? [fwId]
      : this.aggregator.listFrameworks();

    const frameworkComparisons: Record<
      FrameworkId,
      { orgScore: number; networkAvg: number; delta: number }
    > = {};

    let totalOrg = 0;
    let totalNet = 0;
    let count = 0;

    for (const fid of frameworks) {
      const bench = this.benchmarkByFramework(fid);
      const orgEntry = bench.entries.find(
        (e) => e.organizationId === orgId,
      );
      const orgScore = orgEntry?.overallScore ?? 0;
      const delta = orgScore - bench.networkAverage;

      frameworkComparisons[fid] = {
        orgScore,
        networkAvg: bench.networkAverage,
        delta,
      };

      totalOrg += orgScore;
      totalNet += bench.networkAverage;
      count++;
    }

    const orgScore = count > 0 ? totalOrg / count : 0;
    const networkAverage = count > 0 ? totalNet / count : 0;

    // Rank across all orgs on the aggregate score
    const allOrgs = this.aggregator.listOrganizations();
    const allScores = allOrgs.map((oid) => this.aggregator.orgAverage(oid));
    allScores.sort((a, b) => b - a);
    const rank = allScores.indexOf(orgScore) + 1 || allOrgs.length + 1;
    const percentile = Math.round(
      ((allOrgs.length - rank + 1) / (allOrgs.length || 1)) * 100,
    );

    return {
      orgScore,
      networkAverage,
      networkMedian: this.median(allScores),
      rank,
      percentile,
      frameworkComparisons,
    };
  }

  private median(values: number[]): number {
    if (values.length === 0) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0
      ? sorted[mid]
      : (sorted[mid - 1] + sorted[mid]) / 2;
  }
}

// ---------------------------------------------------------------------------
// RiskScorer – compliance risk scoring and prediction
// ---------------------------------------------------------------------------

export class RiskScorer {
  constructor(private readonly aggregator: IntelligenceAggregator) {}

  /**
   * Calculate a composite risk score for an organization.
   * Lower compliance scores yield higher risk values.
   */
  scoreOrganization(orgId: OrganizationId): RiskScore {
    const records = this.aggregator.getRecordsForOrg(orgId);
    const fwBuckets = new Map<FrameworkId, ComplianceRecord[]>();

    for (const r of records) {
      const bucket = fwBuckets.get(r.frameworkId) ?? [];
      bucket.push(r);
      fwBuckets.set(r.frameworkId, bucket);
    }

    const frameworkRisks: Record<FrameworkId, number> = {};
    const topRisks: RiskItem[] = [];

    let totalRisk = 0;
    let fwCount = 0;

    for (const [fwId, recs] of fwBuckets) {
      const avgScore =
        recs.reduce((s, r) => s + r.score, 0) / recs.length;
      const risk = this.scoreToRisk(avgScore);
      frameworkRisks[fwId] = risk;
      totalRisk += risk;
      fwCount++;

      // Collect the worst controls as top risks
      for (const r of recs) {
        if (r.score < 50) {
          topRisks.push({
            controlId: r.controlId,
            frameworkId: fwId,
            severity: this.scoreToSeverity(r.score),
            score: this.scoreToRisk(r.score),
            description: `Control ${r.controlId} has low compliance score (${r.score})`,
            mitigation: `Review and remediate control ${r.controlId} under framework ${fwId}`,
          });
        }
      }
    }

    topRisks.sort((a, b) => b.score - a.score);

    return {
      organizationId: orgId,
      overallRisk: fwCount > 0 ? totalRisk / fwCount : 0,
      frameworkRisks,
      topRisks: topRisks.slice(0, 10),
      generatedAt: new Date().toISOString(),
    };
  }

  /**
   * Score every organization and return sorted by highest risk.
   */
  scoreAllOrganizations(): RiskScore[] {
    return this.aggregator
      .listOrganizations()
      .map((orgId) => this.scoreOrganization(orgId))
      .sort((a, b) => b.overallRisk - a.overallRisk);
  }

  private scoreToRisk(complianceScore: number): number {
    return Math.max(0, Math.min(100, 100 - complianceScore));
  }

  private scoreToSeverity(score: number): RiskSeverity {
    if (score < 20) return RiskSeverity.Critical;
    if (score < 40) return RiskSeverity.High;
    if (score < 60) return RiskSeverity.Medium;
    if (score < 80) return RiskSeverity.Low;
    return RiskSeverity.Informational;
  }
}

// ---------------------------------------------------------------------------
// AnomalyDetector – compliance anomaly detection
// ---------------------------------------------------------------------------

export class AnomalyDetector {
  private anomalyIdCounter = 0;

  constructor(private readonly aggregator: IntelligenceAggregator) {}

  /**
   * Detect anomalies for an organization by comparing recent scores against
   * historical averages. Returns a list of anomalies found.
   */
  detect(
    orgId: OrganizationId,
    lookbackBuckets = 3,
    deviationThreshold = 0.2,
    bucketFn: (r: ComplianceRecord) => string = (r) =>
      r.assessedAt.slice(0, 7),
  ): Anomaly[] {
    const records = this.aggregator.getRecordsForOrg(orgId);
    const anomalies: Anomaly[] = [];

    // Group by framework then by time bucket
    const fwMap = new Map<FrameworkId, Map<string, ComplianceRecord[]>>();
    for (const r of records) {
      const bucket = fwMap.get(r.frameworkId) ?? new Map();
      const timeBucket = bucketFn(r);
      const list = bucket.get(timeBucket) ?? [];
      list.push(r);
      bucket.set(timeBucket, list);
      fwMap.set(r.frameworkId, bucket);
    }

    for (const [fwId, timeMap] of fwMap) {
      const sortedKeys = [...timeMap.keys()].sort();
      if (sortedKeys.length < 2) continue;

      const recentKey = sortedKeys[sortedKeys.length - 1];
      const recentRecs = timeMap.get(recentKey) ?? [];
      const recentAvg =
        recentRecs.reduce((s, r) => s + r.score, 0) / recentRecs.length;

      // Build historical baseline
      const historyKeys = sortedKeys.slice(
        Math.max(0, sortedKeys.length - 1 - lookbackBuckets),
        sortedKeys.length - 1,
      );
      const histScores: number[] = [];
      for (const k of historyKeys) {
        const recs = timeMap.get(k) ?? [];
        const avg = recs.reduce((s, r) => s + r.score, 0) / recs.length;
        histScores.push(avg);
      }

      if (histScores.length === 0) continue;
      const histAvg =
        histScores.reduce((a, b) => a + b, 0) / histScores.length;
      const histStd = this.standardDeviation(histScores);

      const deviation = histStd === 0 ? 0 : Math.abs(recentAvg - histAvg) / histStd;

      if (deviation >= deviationThreshold / histStd || histStd === 0) {
        // Check individual controls for sudden drops
        for (const r of recentRecs) {
          const prevRecs = records.filter(
            (pr) =>
              pr.frameworkId === fwId &&
              pr.controlId === r.controlId &&
              pr.assessedAt !== r.assessedAt,
          );
          if (prevRecs.length > 0) {
            const prevAvg =
              prevRecs.reduce((s, pr) => s + pr.score, 0) / prevRecs.length;
            const change = r.score - prevAvg;

            if (change < -20) {
              anomalies.push(this.createAnomaly(
                orgId,
                fwId,
                r.controlId,
                anomalyType.SuddenDrop,
                this.scoreToSeverity(Math.abs(change)),
                `Score dropped from ${prevAvg.toFixed(1)} to ${r.score}`,
                prevAvg,
                r.score,
              ));
            } else if (change > 30) {
              anomalies.push(this.createAnomaly(
                orgId,
                fwId,
                r.controlId,
                anomalyType.SuddenSpike,
                RiskSeverity.Informational,
                `Score spiked from ${prevAvg.toFixed(1)} to ${r.score}`,
                prevAvg,
                r.score,
              ));
            }
          }
        }

        // Check for stagnation
        if (histScores.length >= 3) {
          const allSimilar = histScores.every(
            (s) => Math.abs(s - histAvg) < 1,
          );
          if (allSimilar && Math.abs(recentAvg - histAvg) < 1) {
            anomalies.push(this.createAnomaly(
              orgId,
              fwId,
              "_aggregate_",
              anomalyType.Stagnation,
              RiskSeverity.Low,
              `Scores have been stagnant around ${histAvg.toFixed(1)} for ${histScores.length + 1} periods`,
              histAvg,
              recentAvg,
            ));
          }
        }
      }
    }

    return anomalies;
  }

  /**
   * Run anomaly detection across every organization.
   */
  detectAll(
    lookbackBuckets?: number,
    deviationThreshold?: number,
    bucketFn?: (r: ComplianceRecord) => string,
  ): Anomaly[] {
    return this.aggregator
      .listOrganizations()
      .flatMap((orgId) =>
        this.detect(orgId, lookbackBuckets, deviationThreshold, bucketFn),
      )
      .sort((a, b) => {
        const severityOrder: Record<RiskSeverity, number> = {
          [RiskSeverity.Critical]: 0,
          [RiskSeverity.High]: 1,
          [RiskSeverity.Medium]: 2,
          [RiskSeverity.Low]: 3,
          [RiskSeverity.Informational]: 4,
        };
        return severityOrder[a.severity] - severityOrder[b.severity];
      });
  }

  // ---- private helpers ----------------------------------------------------

  private createAnomaly(
    orgId: OrganizationId,
    fwId: FrameworkId,
    controlId: ControlId,
    type: anomalyType,
    severity: RiskSeverity,
    description: string,
    expected: number,
    actual: number,
  ): Anomaly {
    this.anomalyIdCounter++;
    return {
      id: `anomaly-${this.anomalyIdCounter}`,
      organizationId: orgId,
      frameworkId: fwId,
      controlId,
      type,
      severity,
      description,
      detectedAt: new Date().toISOString(),
      expectedValue: expected,
      actualValue: actual,
    };
  }

  private standardDeviation(values: number[]): number {
    if (values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const sqDiffs = values.map((v) => (v - mean) ** 2);
    const avgSqDiff = sqDiffs.reduce((a, b) => a + b, 0) / sqDiffs.length;
    return Math.sqrt(avgSqDiff);
  }

  private scoreToSeverity(score: number): RiskSeverity {
    if (score > 40) return RiskSeverity.Critical;
    if (score > 30) return RiskSeverity.High;
    if (score > 20) return RiskSeverity.Medium;
    return RiskSeverity.Low;
  }
}

// ---------------------------------------------------------------------------
// RecommendationEngine – actionable compliance recommendations
// ---------------------------------------------------------------------------

export class RecommendationEngine {
  private recIdCounter = 0;

  constructor(
    private readonly aggregator: IntelligenceAggregator,
    private readonly riskScorer: RiskScorer,
    private readonly trendAnalyzer: TrendAnalyzer,
  ) {}

  /**
   * Generate prioritised recommendations for an organization.
   */
  generateForOrganization(orgId: OrganizationId): Recommendation[] {
    const recommendations: Recommendation[] = [];
    const risk = this.riskScorer.scoreOrganization(orgId);
    const frameworks = this.aggregator.listFrameworks();

    // 1. Address top risk items
    for (const item of risk.topRisks) {
      recommendations.push(
        this.createRec(
          orgId,
          item.severity,
          "Risk Remediation",
          `Remediate ${item.severity} risk on ${item.controlId}`,
          item.mitigation ?? item.description,
          [item.controlId],
          [item.frameworkId],
          item.score,
        ),
      );
    }

    // 2. Address declining trends
    for (const fwId of frameworks) {
      const trend = this.trendAnalyzer.analyzeOrgFrameworkTrend(orgId, fwId);
      if (trend.direction === TrendDirection.Declining) {
        recommendations.push(
          this.createRec(
            orgId,
            RiskSeverity.High,
            "Trend Correction",
            `Reverse declining compliance trend for ${fwId}`,
            `The compliance score for ${fwId} has been declining (slope: ${trend.slope.toFixed(3)}). Immediate review recommended.`,
            [],
            [fwId],
            Math.abs(trend.slope) * 100,
          ),
        );
      }
    }

    // 3. Address stagnation
    for (const fwId of frameworks) {
      const trend = this.trendAnalyzer.analyzeOrgFrameworkTrend(orgId, fwId);
      if (
        trend.direction === TrendDirection.Stable &&
        trend.confidence > 0.8
      ) {
        const orgScore = this.aggregator.orgAverage(orgId);
        if (orgScore < 80) {
          recommendations.push(
            this.createRec(
              orgId,
              RiskSeverity.Medium,
              "Improvement Opportunity",
              `Break stagnation in ${fwId}`,
              `Scores have been stable at ~${orgScore.toFixed(1)}. Consider targeted improvements to break through the plateau.`,
              [],
              [fwId],
              20,
            ),
          );
        }
      }
    }

    // 4. Benchmarking insights
    for (const fwId of frameworks) {
      const bench = this.aggregator.frameworkAverage(fwId);
      const orgRecords = this.aggregator
        .getRecordsForOrg(orgId)
        .filter((r) => r.frameworkId === fwId);
      const orgScore =
        orgRecords.length > 0
          ? orgRecords.reduce((s, r) => s + r.score, 0) / orgRecords.length
          : 0;

      if (orgScore < bench) {
        const gap = bench - orgScore;
        recommendations.push(
          this.createRec(
            orgId,
            gap > 15 ? RiskSeverity.High : RiskSeverity.Medium,
            "Benchmark Gap",
            `Close ${fwId} gap vs network average`,
            `Organization scores ${orgScore.toFixed(1)} vs network average of ${bench.toFixed(1)} (gap: ${gap.toFixed(1)}).`,
            [],
            [fwId],
            gap,
          ),
        );
      }
    }

    // Sort by estimated impact descending
    recommendations.sort((a, b) => b.estimatedImpact - a.estimatedImpact);

    return recommendations;
  }

  /**
   * Generate recommendations for all organizations.
   */
  generateAll(): Map<OrganizationId, Recommendation[]> {
    const map = new Map<OrganizationId, Recommendation[]>();
    for (const orgId of this.aggregator.listOrganizations()) {
      map.set(orgId, this.generateForOrganization(orgId));
    }
    return map;
  }

  /**
   * Generate network-level recommendations (patterns observed across orgs).
   */
  generateNetworkRecommendations(): Recommendation[] {
    const recs: Recommendation[] = [];
    const frameworks = this.aggregator.listFrameworks();

    for (const fwId of frameworks) {
      const trend = this.trendAnalyzer.analyzeNetworkTrend(fwId);
      if (trend.direction === TrendDirection.Declining) {
        recs.push(
          this.createRec(
            "_network_",
            RiskSeverity.Critical,
            "Network Trend Alert",
            `Network-wide decline detected for ${fwId}`,
            `The network average for ${fwId} is trending downward (slope: ${trend.slope.toFixed(3)}). Coordinated remediation recommended.`,
            [],
            [fwId],
            Math.abs(trend.slope) * 200,
          ),
        );
      }

      const avg = this.aggregator.frameworkAverage(fwId);
      if (avg < 50) {
        recs.push(
          this.createRec(
            "_network_",
            RiskSeverity.Critical,
            "Low Network Compliance",
            `Network-wide low compliance for ${fwId}`,
            `The network average for ${fwId} is ${avg.toFixed(1)}, well below acceptable thresholds.`,
            [],
            [fwId],
            100 - avg,
          ),
        );
      }
    }

    recs.sort((a, b) => b.estimatedImpact - a.estimatedImpact);
    return recs;
  }

  private createRec(
    orgId: OrganizationId,
    priority: RiskSeverity,
    category: string,
    title: string,
    description: string,
    controls: ControlId[],
    frameworkIds: FrameworkId[],
    impact: number,
  ): Recommendation {
    this.recIdCounter++;
    return {
      id: `rec-${this.recIdCounter}`,
      organizationId: orgId,
      priority,
      category,
      title,
      description,
      controls,
      frameworkIds,
      estimatedImpact: Math.round(impact * 100) / 100,
      generatedAt: new Date().toISOString(),
    };
  }
}

// ---------------------------------------------------------------------------
// ComplianceIntelligenceAPI – main façade
// ---------------------------------------------------------------------------

export class ComplianceIntelligenceAPI {
  readonly aggregator: IntelligenceAggregator;
  readonly trendAnalyzer: TrendAnalyzer;
  readonly benchmarkEngine: BenchmarkEngine;
  readonly riskScorer: RiskScorer;
  readonly anomalyDetector: AnomalyDetector;
  readonly recommendationEngine: RecommendationEngine;

  constructor() {
    this.aggregator = new IntelligenceAggregator();
    this.trendAnalyzer = new TrendAnalyzer(this.aggregator);
    this.benchmarkEngine = new BenchmarkEngine(this.aggregator);
    this.riskScorer = new RiskScorer(this.aggregator);
    this.anomalyDetector = new AnomalyDetector(this.aggregator);
    this.recommendationEngine = new RecommendationEngine(
      this.aggregator,
      this.riskScorer,
      this.trendAnalyzer,
    );
  }

  /** Ingest compliance records into the intelligence engine. */
  ingest(records: ComplianceRecord[]): void {
    this.aggregator.ingest(records);
  }

  /** Get a network-wide compliance snapshot. */
  getNetworkSnapshot(): NetworkSnapshot {
    return this.aggregator.snapshot();
  }

  /** Analyse trend for a specific org + framework. */
  getTrend(orgId: OrganizationId, fwId: FrameworkId): TrendResult {
    return this.trendAnalyzer.analyzeOrgFrameworkTrend(orgId, fwId);
  }

  /** Get network trend for a framework. */
  getNetworkTrend(fwId: FrameworkId): TrendResult {
    return this.trendAnalyzer.analyzeNetworkTrend(fwId);
  }

  /** Get all framework trends across the network. */
  getAllTrends(): TrendResult[] {
    return this.trendAnalyzer.analyzeAllFrameworks();
  }

  /** Benchmark all organizations on a framework. */
  getBenchmark(fwId: FrameworkId): BenchmarkResult {
    return this.benchmarkEngine.benchmarkByFramework(fwId);
  }

  /** Benchmark a single organization. */
  getOrgBenchmark(orgId: OrganizationId, fwId?: FrameworkId) {
    return this.benchmarkEngine.benchmarkOrganization(orgId, fwId);
  }

  /** Risk score for an organization. */
  getRiskScore(orgId: OrganizationId): RiskScore {
    return this.riskScorer.scoreOrganization(orgId);
  }

  /** Risk scores for every organization. */
  getAllRiskScores(): RiskScore[] {
    return this.riskScorer.scoreAllOrganizations();
  }

  /** Detect anomalies for an organization. */
  detectAnomalies(
    orgId: OrganizationId,
    lookback?: number,
    threshold?: number,
  ): Anomaly[] {
    return this.anomalyDetector.detect(orgId, lookback, threshold);
  }

  /** Detect anomalies across the network. */
  detectAllAnomalies(): Anomaly[] {
    return this.anomalyDetector.detectAll();
  }

  /** Generate recommendations for an organization. */
  getRecommendations(orgId: OrganizationId): Recommendation[] {
    return this.recommendationEngine.generateForOrganization(orgId);
  }

  /** Generate recommendations for every organization. */
  getAllRecommendations(): Map<OrganizationId, Recommendation[]> {
    return this.recommendationEngine.generateAll();
  }

  /** Generate network-level strategic recommendations. */
  getNetworkRecommendations(): Recommendation[] {
    return this.recommendationEngine.generateNetworkRecommendations();
  }
}

export default ComplianceIntelligenceAPI;
