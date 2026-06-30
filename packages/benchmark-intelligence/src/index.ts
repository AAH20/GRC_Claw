import { createHash } from 'node:crypto';

export type BenchmarkCategory =
  | 'audit_cycle_time'
  | 'evidence_freshness'
  | 'remediation_latency'
  | 'vendor_response_time'
  | 'automation_success_rate'
  | 'policy_denial_rate'
  | 'verifier_acceptance_rate'
  | 'procurement_blocker_frequency'
  | 'control_reuse_rate'
  | 'mttr'
  | 'mttd'
  | 'sprs_score'
  | 'trust_score'
  | 'compliance_readiness';

export type BenchmarkScope = 'tenant' | 'industry' | 'framework' | 'region' | 'company_size' | 'global';

export interface BenchmarkSignal {
  signalId: string;
  timestamp: string;
  tenantId: number;
  orgSlug: string;
  category: BenchmarkCategory;
  scope: BenchmarkScope;
  value: number;
  unit: string;
  framework?: string;
  controlId?: string;
  industry?: string;
  region?: string;
  companySize?: string;
  metadata?: Record<string, unknown>;
}

export interface BenchmarkAggregation {
  category: BenchmarkCategory;
  scope: BenchmarkScope;
  period: { from: string; to: string };
  sampleSize: number;
  statistics: {
    mean: number;
    median: number;
    p25: number;
    p75: number;
    p90: number;
    stddev: number;
    min: number;
    max: number;
  };
  breakdown: Array<{
    label: string;
    value: number;
    count: number;
  }>;
  trend: Array<{
    period: string;
    value: number;
  }>;
}

export interface BenchmarkRecommendation {
  recommendationId: string;
  category: BenchmarkCategory;
  currentPercentile: number;
  targetPercentile: number;
  benchmarkValue: number;
  currentValue: number;
  impact: string;
  suggestedAction: string;
  confidence: number;
  estimatedImprovementDays?: number;
  estimatedCostImpactUsd?: number;
}

export interface BenchmarkComparison {
  comparisonId: string;
  tenantId: number;
  orgSlug: string;
  comparedAt: string;
  tenantMetrics: Record<BenchmarkCategory, number>;
  peerMetrics: Record<BenchmarkCategory, number>;
  percentiles: Record<BenchmarkCategory, number>;
  recommendations: BenchmarkRecommendation[];
  overallScore: number;
  overallPercentile: number;
}

export interface BenchmarkInsight {
  insightId: string;
  category: BenchmarkCategory;
  title: string;
  description: string;
  benchmarkValue: number;
  peerValue: number;
  delta: number;
  deltaPercent: number;
  severity: 'info' | 'warning' | 'critical';
  recommendation: string;
}

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, v]) => v !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => [k, stable(v)]),
    );
  }
  return value;
}

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

export function createBenchmarkSignal(input: {
  tenantId: number;
  orgSlug: string;
  category: BenchmarkCategory;
  scope: BenchmarkScope;
  value: number;
  unit: string;
  framework?: string;
  controlId?: string;
  industry?: string;
  region?: string;
  companySize?: string;
  metadata?: Record<string, unknown>;
}): BenchmarkSignal {
  return {
    signalId: `bsig:${sha256({ ...input, ts: Date.now() }).slice(0, 16)}`,
    timestamp: new Date().toISOString(),
    ...input,
  };
}

export function aggregateBenchmarkSignals(
  signals: BenchmarkSignal[],
  category: BenchmarkCategory,
  scope: BenchmarkScope,
  period: { from: string; to: string },
): BenchmarkAggregation {
  const filtered = signals.filter(
    (s) => s.category === category && s.scope === scope && s.timestamp >= period.from && s.timestamp <= period.to,
  );

  const values = filtered.map((s) => s.value).sort((a, b) => a - b);
  const n = values.length;

  if (n === 0) {
    return {
      category,
      scope,
      period,
      sampleSize: 0,
      statistics: { mean: 0, median: 0, p25: 0, p75: 0, p90: 0, stddev: 0, min: 0, max: 0 },
      breakdown: [],
      trend: [],
    };
  }

  const mean = values.reduce((a, b) => a + b, 0) / n;
  const median = n % 2 === 0 ? (values[n / 2 - 1] + values[n / 2]) / 2 : values[Math.floor(n / 2)];
  const p25 = values[Math.floor(n * 0.25)] ?? values[0];
  const p75 = values[Math.floor(n * 0.75)] ?? values[n - 1];
  const p90 = values[Math.floor(n * 0.9)] ?? values[n - 1];
  const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / n;
  const stddev = Math.sqrt(variance);

  const byIndustry = new Map<string, { sum: number; count: number }>();
  for (const s of filtered) {
    const key = s.industry ?? 'unknown';
    const existing = byIndustry.get(key) ?? { sum: 0, count: 0 };
    existing.sum += s.value;
    existing.count++;
    byIndustry.set(key, existing);
  }

  const breakdown = [...byIndustry.entries()]
    .map(([label, data]) => ({ label, value: data.sum / data.count, count: data.count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const byMonth = new Map<string, { sum: number; count: number }>();
  for (const s of filtered) {
    const month = s.timestamp.slice(0, 7);
    const existing = byMonth.get(month) ?? { sum: 0, count: 0 };
    existing.sum += s.value;
    existing.count++;
    byMonth.set(month, existing);
  }
  const trend = [...byMonth.entries()]
    .map(([period, data]) => ({ period, value: data.sum / data.count }))
    .sort((a, b) => a.period.localeCompare(b.period));

  return {
    category,
    scope,
    period,
    sampleSize: n,
    statistics: { mean, median, p25, p75, p90, stddev, min: values[0], max: values[n - 1] },
    breakdown,
    trend,
  };
}

export function generateRecommendations(
  tenantMetrics: Record<BenchmarkCategory, number>,
  peerAggregations: Map<BenchmarkCategory, BenchmarkAggregation>,
): BenchmarkRecommendation[] {
  const recommendations: BenchmarkRecommendation[] = [];

  for (const [category, tenantValue] of Object.entries(tenantMetrics)) {
    const agg = peerAggregations.get(category as BenchmarkCategory);
    if (!agg || agg.sampleSize === 0) continue;

    const percentile = calculatePercentile(tenantValue, agg);
    if (percentile < 75) {
      recommendations.push({
        recommendationId: `rec:${sha256({ category, tenantValue, ts: Date.now() }).slice(0, 12)}`,
        category: category as BenchmarkCategory,
        currentPercentile: percentile,
        targetPercentile: Math.min(90, percentile + 20),
        benchmarkValue: agg.statistics.median,
        currentValue: tenantValue,
        impact: `Improving ${category.replace(/_/g, ' ')} from ${tenantValue} to ${agg.statistics.median} would move you from the ${percentile}th to the ${Math.min(90, percentile + 20)}th percentile`,
        suggestedAction: getRecommendationAction(category as BenchmarkCategory, tenantValue, agg.statistics.median),
        confidence: 0.7 + (agg.sampleSize / 1000) * 0.25,
      });
    }
  }

  return recommendations.sort((a, b) => b.confidence - a.confidence);
}

function calculatePercentile(value: number, agg: BenchmarkAggregation): number {
  if (agg.sampleSize === 0) return 50;
  if (value <= agg.statistics.p25) return 25;
  if (value <= agg.statistics.median) return 50;
  if (value <= agg.statistics.p75) return 75;
  if (value <= agg.statistics.p90) return 90;
  return 95;
}

function getRecommendationAction(category: BenchmarkCategory, current: number, target: number): string {
  const actions: Record<BenchmarkCategory, string> = {
    audit_cycle_time: 'Automate evidence collection and pre-audit simulations to reduce audit cycle time',
    evidence_freshness: 'Enable the Evidence Daemon for continuous evidence refresh and set up staleness alerts',
    remediation_latency: 'Deploy SOAR playbooks for automated remediation of common control failures',
    vendor_response_time: 'Implement vendor risk automation with escalation workflows and SLA tracking',
    automation_success_rate: 'Review and fix failing automation workflows; add error handling and retry logic',
    policy_denial_rate: 'Review policy firewall rules; adjust approval thresholds for low-risk actions',
    verifier_acceptance_rate: 'Improve evidence quality and completeness before submitting to verifier rooms',
    procurement_blocker_frequency: 'Complete SSP/POA&M documentation and resolve critical findings proactively',
    control_reuse_rate: 'Leverage the framework crosswalk to reuse evidence across multiple frameworks',
    mttr: 'Implement automated incident response playbooks with escalation and evidence collection',
    mttd: 'Deploy real-time compliance monitoring with anomaly detection and alerting',
    sprs_score: 'Address open POA&M items and implement missing controls to improve SPRS scoring',
    trust_score: 'Improve evidence freshness, reduce vulnerabilities, and increase control test pass rates',
    compliance_readiness: 'Run compliance autopilot to identify and remediate gaps before audit windows',
  };
  return actions[category] ?? 'Review benchmark data and implement targeted improvements';
}

export function computeOverallScore(metrics: Record<BenchmarkCategory, number>): { score: number; percentile: number } {
  const weights: Partial<Record<BenchmarkCategory, number>> = {
    evidence_freshness: 15,
    control_reuse_rate: 15,
    audit_cycle_time: 10,
    remediation_latency: 10,
    automation_success_rate: 10,
    verifier_acceptance_rate: 10,
    mttr: 10,
    trust_score: 10,
  };

  let totalWeight = 0;
  let weightedScore = 0;

  for (const [category, weight] of Object.entries(weights)) {
    const value = metrics[category as BenchmarkCategory];
    if (value !== undefined) {
      const normalized = Math.min(100, Math.max(0, value));
      weightedScore += normalized * (weight as number);
      totalWeight += weight as number;
    }
  }

  const score = totalWeight > 0 ? Math.round(weightedScore / totalWeight) : 0;
  const percentile = Math.min(99, Math.max(1, score));

  return { score, percentile };
}

export function formatBenchmarkForEvidenceGraph(comparison: BenchmarkComparison): Record<string, unknown> {
  return {
    objectKind: 'node',
    objectType: 'benchmark_intelligence',
    label: `Benchmark: ${comparison.orgSlug} (${comparison.overallPercentile}th percentile)`,
    source: 'benchmark-intelligence',
    payload: {
      comparison_id: comparison.comparisonId,
      overall_score: comparison.overallScore,
      overall_percentile: comparison.overallPercentile,
      recommendations_count: comparison.recommendations.length,
      tenant_metrics: comparison.tenantMetrics,
      peer_metrics: comparison.peerMetrics,
    },
  };
}
