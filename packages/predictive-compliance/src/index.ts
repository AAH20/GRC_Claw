/**
 * @grc-claw/predictive-compliance
 *
 * AI/ML-powered predictive compliance engine that forecasts compliance failures
 * before they happen by analyzing historical data, current posture, and external
 * signals.
 */

// ---------------------------------------------------------------------------
// Types & Interfaces
// ---------------------------------------------------------------------------

/** Forecast for a single control's compliance outlook. */
export interface ComplianceForecast {
  controlId: string;
  probability: number;
  timeframe: number;
  confidence: number;
  factors: RiskFactor[];
  recommendations: Remediation[];
}

/** Individual risk factor contributing to a forecast. */
export interface RiskFactor {
  name: string;
  weight: number;
  value: number;
  description: string;
}

/** Recommended remediation action. */
export interface Remediation {
  id: string;
  title: string;
  description: string;
  priority: "critical" | "high" | "medium" | "low";
  estimatedEffort: number;
  estimatedImpact: number;
  deadline: string;
}

/** External or internal signal that influences risk posture. */
export interface RiskSignal {
  type: string;
  severity: "critical" | "high" | "medium" | "low" | "informational";
  source: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

/** Trend analysis result for a tracked metric. */
export interface TrendAnalysis {
  metric: string;
  direction: "improving" | "stable" | "degrading" | "volatile";
  velocity: number;
  acceleration: number;
  prediction: DataPoint[];
}

/** Single timestamped measurement. */
export interface DataPoint {
  timestamp: string;
  value: number;
}

/** Result of a Monte Carlo simulation. */
export interface SimulationResult {
  controlId: string;
  iterations: number;
  distribution: number[];
  mean: number;
  median: number;
  stdDev: number;
  percentiles: Record<string, number>;
  confidenceInterval: { lower: number; upper: number };
  estimatedTimeToFailure: number | null;
}

/** Heat map cell for risk visualization. */
export interface HeatMapCell {
  controlId: string;
  inherentRisk: number;
  residualRisk: number;
  velocity: number;
  quadrant: "critical" | "high" | "watch" | "low";
}

/** Time-series data point with metric name. */
export interface TimeSeriesEntry {
  metric: string;
  value: number;
  timestamp: string;
}

/** Export format options. */
export type ExportFormat = "json" | "csv";

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class PredictiveComplianceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PredictiveComplianceError";
  }
}

export class InsufficientDataError extends PredictiveComplianceError {
  constructor(metric: string, required: number, actual: number) {
    super(`Insufficient data for metric "${metric}": need ${required}, have ${actual}`);
    this.name = "InsufficientDataError";
  }
}

// ---------------------------------------------------------------------------
// TimeSeriesAnalyzer
// ---------------------------------------------------------------------------

/**
 * Analyzes time-series data for trends, seasonality, anomalies, and forecasting.
 */
export class TimeSeriesAnalyzer {
  private store: Map<string, DataPoint[]> = new Map();

  /**
   * Add a single data point for a given metric.
   * @param metric - The metric name.
   * @param value  - The numeric value.
   * @param timestamp - ISO-8601 timestamp.
   */
  addDataPoint(metric: string, value: number, timestamp: string): void {
    const points = this.store.get(metric) ?? [];
    points.push({ timestamp, value });
    points.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    this.store.set(metric, points);
  }

  /**
   * Detect the overall trend direction and velocity for a metric.
   * @param metric - The metric to analyze.
   * @returns TrendAnalysis or null if insufficient data.
   */
  detectTrend(metric: string): TrendAnalysis | null {
    const points = this.store.get(metric);
    if (!points || points.length < 3) return null;

    const values = points.map((p) => p.value);
    const n = values.length;

    const { slope } = linearRegression(values);
    const mid = Math.floor(n / 2);
    const firstHalfSlope = linearRegression(values.slice(0, mid)).slope;
    const secondHalfSlope = linearRegression(values.slice(mid)).slope;
    const acceleration = secondHalfSlope - firstHalfSlope;

    const residuals = values.map((v, i) => v - (values[0] + slope * i));
    const volatility = standardDeviation(residuals);

    let direction: TrendAnalysis["direction"];
    if (volatility > Math.abs(slope) * 2) direction = "volatile";
    else if (slope > 0.01) direction = "improving";
    else if (slope < -0.01) direction = "degrading";
    else direction = "stable";

    const horizon = 30;
    const prediction = forecastLinear(values, horizon, points[points.length - 1].timestamp);

    return { metric, direction, velocity: slope, acceleration, prediction };
  }

  /**
   * Detect seasonality in a metric using autocorrelation.
   * @param metric - The metric to analyze.
   * @returns The detected period (in data points) or null.
   */
  detectSeasonality(metric: string): number | null {
    const points = this.store.get(metric);
    if (!points || points.length < 14) return null;

    const values = points.map((p) => p.value);
    const mean = avg(values);
    const centered = values.map((v) => v - mean);

    let bestPeriod = 0;
    let bestCorrelation = 0;
    const maxPeriod = Math.min(Math.floor(values.length / 2), 60);

    for (let period = 2; period <= maxPeriod; period++) {
      let correlation = 0;
      let count = 0;
      for (let i = 0; i < centered.length - period; i++) {
        correlation += centered[i] * centered[i + period];
        count++;
      }
      if (count > 0) {
        correlation /= count;
        if (Math.abs(correlation) > Math.abs(bestCorrelation)) {
          bestCorrelation = correlation;
          bestPeriod = period;
        }
      }
    }

    return Math.abs(bestCorrelation) >= 0.3 ? bestPeriod : null;
  }

  /**
   * Forecast future values for a metric.
   * @param metric  - The metric to forecast.
   * @param horizon - Number of steps ahead.
   * @returns Array of predicted data points.
   */
  forecast(metric: string, horizon: number): DataPoint[] {
    const points = this.store.get(metric);
    if (!points || points.length < 3) {
      throw new InsufficientDataError(metric, 3, points?.length ?? 0);
    }

    const values = points.map((p) => p.value);
    const lastTimestamp = points[points.length - 1].timestamp;
    return forecastLinear(values, horizon, lastTimestamp);
  }

  /**
   * Detect anomalies using Z-score method.
   * @param metric     - The metric to scan.
   * @param sensitivity - Z-score threshold (default 2.0).
   * @returns Indices and values of anomalous data points.
   */
  detectAnomalies(
    metric: string,
    sensitivity: number = 2.0
  ): Array<{ index: number; value: number; zscore: number }> {
    const points = this.store.get(metric);
    if (!points || points.length < 5) return [];

    const values = points.map((p) => p.value);
    const mean = avg(values);
    const std = standardDeviation(values);
    if (std === 0) return [];

    const anomalies: Array<{ index: number; value: number; zscore: number }> = [];
    for (let i = 0; i < values.length; i++) {
      const zscore = (values[i] - mean) / std;
      if (Math.abs(zscore) > sensitivity) {
        anomalies.push({ index: i, value: values[i], zscore });
      }
    }
    return anomalies;
  }

  /** Get all stored metric names. */
  getMetrics(): string[] {
    return Array.from(this.store.keys());
  }

  /** Get raw data points for a metric. */
  getDataPoints(metric: string): DataPoint[] {
    return [...(this.store.get(metric) ?? [])];
  }
}

// ---------------------------------------------------------------------------
// RiskScoringEngine
// ---------------------------------------------------------------------------

/**
 * Calculates inherent risk, residual risk, risk velocity, and produces heat maps.
 */
export class RiskScoringEngine {
  /**
   * Calculate inherent risk for a control (0-1 scale).
   * Considers probability of failure and impact.
   */
  calculateInherentRisk(control: {
    failureProbability: number;
    impact: number;
    complexity: number;
    exposure: number;
  }): number {
    const { failureProbability, impact, complexity, exposure } = control;
    const raw = failureProbability * impact * 0.5 + complexity * 0.2 + exposure * 0.3;
    return clamp(raw, 0, 1);
  }

  /**
   * Calculate residual risk after mitigations are applied.
   * @param control     - The control with inherent risk factors.
   * @param mitigations - Array of mitigation effectiveness values (0-1).
   */
  calculateResidualRisk(
    control: {
      failureProbability: number;
      impact: number;
      complexity: number;
      exposure: number;
    },
    mitigations: number[]
  ): number {
    const inherent = this.calculateInherentRisk(control);
    const mitigationFactor = mitigations.reduce(
      (acc, m) => acc * (1 - clamp(m, 0, 1)),
      1
    );
    return clamp(inherent * mitigationFactor, 0, 1);
  }

  /**
   * Calculate how fast risk is changing per unit time.
   * @param control - Object with historical risk scores as DataPoints.
   */
  calculateRiskVelocity(control: { riskHistory: DataPoint[] }): number {
    if (control.riskHistory.length < 2) return 0;
    const values = control.riskHistory.map((p) => p.value);
    const { slope } = linearRegression(values);
    return slope;
  }

  /**
   * Generate a risk heat map from a set of controls.
   * @param controls - Array of controls with risk data.
   * @returns HeatMapCell array for visualization.
   */
  generateHeatMap(
    controls: Array<{
      id: string;
      failureProbability: number;
      impact: number;
      complexity: number;
      exposure: number;
      mitigations: number[];
      riskHistory: DataPoint[];
    }>
  ): HeatMapCell[] {
    return controls.map((c) => {
      const inherentRisk = this.calculateInherentRisk(c);
      const residualRisk = this.calculateResidualRisk(c, c.mitigations);
      const velocity = this.calculateRiskVelocity(c);

      let quadrant: HeatMapCell["quadrant"];
      if (residualRisk > 0.7 && velocity >= 0) quadrant = "critical";
      else if (residualRisk > 0.7 && velocity < 0) quadrant = "high";
      else if (residualRisk <= 0.7 && velocity >= 0) quadrant = "watch";
      else quadrant = "low";

      return {
        controlId: c.id,
        inherentRisk,
        residualRisk,
        velocity,
        quadrant,
      };
    });
  }
}

// ---------------------------------------------------------------------------
// MonteCarloSimulator
// ---------------------------------------------------------------------------

/**
 * Runs Monte Carlo simulations to estimate compliance failure distributions.
 */
export class MonteCarloSimulator {
  /**
   * Run a Monte Carlo simulation for a control.
   * @param controlId  - The control identifier.
   * @param iterations - Number of simulation iterations (default 10,000).
   * @param parameters - Distribution parameters for the simulation.
   */
  simulate(
    controlId: string,
    iterations: number = 10_000,
    parameters: {
      meanFailureRate: number;
      stdDevFailureRate: number;
      impactMean: number;
      impactStdDev: number;
      seed?: number;
    }
  ): SimulationResult {
    if (iterations < 100) {
      throw new PredictiveComplianceError("Minimum 100 iterations required");
    }

    const rng = createRng(parameters.seed);
    const distribution: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const failureRate = clamp(
        gaussianSample(rng, parameters.meanFailureRate, parameters.stdDevFailureRate),
        0,
        1
      );
      const impact = clamp(
        gaussianSample(rng, parameters.impactMean, parameters.impactStdDev),
        0,
        1
      );
      distribution.push(failureRate * impact);
    }

    distribution.sort((a, b) => a - b);
    const mean = avg(distribution);
    const median = percentile(distribution, 50);
    const stdDev = standardDeviation(distribution);

    const percentiles: Record<string, number> = {};
    for (const p of [5, 10, 25, 50, 75, 90, 95]) {
      percentiles[`p${p}`] = percentile(distribution, p);
    }

    const ci = this.calculateConfidenceInterval(distribution, 0.95);
    const estimatedTimeToFailure = this.estimateTimeToFailure(distribution);

    return {
      controlId,
      iterations,
      distribution,
      mean,
      median,
      stdDev,
      percentiles,
      confidenceInterval: ci,
      estimatedTimeToFailure,
    };
  }

  /**
   * Generate a probability distribution summary from simulation results.
   */
  generateDistribution(
    results: number[],
    buckets: number = 20
  ): Array<{ range: [number, number]; count: number; probability: number }> {
    const min = results[0];
    const max = results[results.length - 1];
    const step = (max - min) / buckets;
    const dist: Array<{ range: [number, number]; count: number; probability: number }> = [];

    for (let i = 0; i < buckets; i++) {
      const lo = min + i * step;
      const hi = lo + step;
      const count = results.filter((v) => v >= lo && (i === buckets - 1 ? v <= hi : v < hi)).length;
      dist.push({ range: [lo, hi], count, probability: count / results.length });
    }

    return dist;
  }

  /**
   * Calculate a confidence interval from sorted simulation results.
   * @param results    - Sorted array of simulation values.
   * @param confidence - Confidence level (e.g. 0.95).
   */
  calculateConfidenceInterval(
    results: number[],
    confidence: number
  ): { lower: number; upper: number } {
    const alpha = (1 - confidence) / 2;
    const lower = percentile(results, alpha * 100);
    const upper = percentile(results, (1 - alpha) * 100);
    return { lower, upper };
  }

  /**
   * Estimate expected time to failure from simulation distribution.
   * Returns null if risk is negligible (< 5th percentile).
   */
  estimateTimeToFailure(results: number[]): number | null {
    const p5 = percentile(results, 5);
    if (p5 < 0.05) return null;

    const mean = avg(results);
    const daysPerUnitRisk = 365;
    return Math.round(daysPerUnitRisk * (1 - mean));
  }
}

// ---------------------------------------------------------------------------
// PredictiveEngine
// ---------------------------------------------------------------------------

/**
 * Main orchestrator that combines forecasting, risk scoring, anomaly detection,
 * and remediation recommendations into a unified predictive compliance engine.
 */
export class PredictiveEngine {
  private timeSeries: TimeSeriesAnalyzer;
  private riskEngine: RiskScoringEngine;
  private simulator: MonteCarloSimulator;
  private forecasts: Map<string, ComplianceForecast> = new Map();

  constructor() {
    this.timeSeries = new TimeSeriesAnalyzer();
    this.riskEngine = new RiskScoringEngine();
    this.simulator = new MonteCarloSimulator();
  }

  /**
   * Analyze a single control and predict its failure probability.
   * @param controlId      - The control identifier.
   * @param historicalData - Past compliance data points.
   * @returns ComplianceForecast with probability, factors, and recommendations.
   */
  analyzeControl(
    controlId: string,
    historicalData: DataPoint[] = []
  ): ComplianceForecast {
    if (historicalData.length < 3) {
      // Return a default forecast when insufficient data
      return {
        controlId,
        probability: 0.5,
        timeframe: 90,
        confidence: 0.3,
        factors: [{
          name: "insufficient_data",
          weight: 1.0,
          value: 0.5,
          description: "Insufficient historical data for accurate prediction",
        }],
        recommendations: [{
          id: `rec-${controlId}-data`,
          title: "Collect more data",
          description: `Control ${controlId} needs at least 3 historical data points for accurate prediction.`,
          priority: "medium" as const,
          estimatedEffort: 8,
          estimatedImpact: 0.3,
          deadline: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        }],
      };
    }

    const metric = `control_${controlId}`;
    for (const dp of historicalData) {
      this.timeSeries.addDataPoint(metric, dp.value, dp.timestamp);
    }

    const trend = this.timeSeries.detectTrend(metric);
    const values = historicalData.map((dp) => dp.value);
    const currentPosture = values[values.length - 1];
    const failureRate = 1 - currentPosture;

    const factors: RiskFactor[] = [
      {
        name: "Current Posture",
        weight: 0.35,
        value: currentPosture,
        description: `Current compliance level at ${(currentPosture * 100).toFixed(1)}%`,
      },
      {
        name: "Historical Failure Rate",
        weight: 0.25,
        value: failureRate,
        description: `Based on ${historicalData.length} historical data points`,
      },
      {
        name: "Trend Velocity",
        weight: 0.2,
        value: trend ? Math.abs(trend.velocity) : 0,
        description: trend
          ? `Trend is ${trend.direction} at velocity ${trend.velocity.toFixed(4)}`
          : "Insufficient data for trend analysis",
      },
      {
        name: "Volatility",
        weight: 0.2,
        value: trend ? Math.abs(trend.velocity + trend.acceleration) * 0.5 : 0.5,
        description: "Measure of score instability",
      },
    ];

    const weightedRisk = factors.reduce(
      (sum, f) => sum + f.weight * (1 - f.value),
      0
    );
    const probability = clamp(weightedRisk, 0, 1);
    const confidence = clamp(0.5 + historicalData.length / 100, 0, 0.99);

    const forecast: ComplianceForecast = {
      controlId,
      probability,
      timeframe: 90,
      confidence,
      factors,
      recommendations: this.generateRecommendations(controlId, probability, trend),
    };

    this.forecasts.set(controlId, forecast);
    return forecast;
  }

  /**
   * Analyze an entire framework and return risk assessments for all controls.
   * @param frameworkId - The framework identifier.
   * @param controls    - Map of controlId to historical data.
   */
  analyzeFramework(
    frameworkId: string,
    controls: Map<string, DataPoint[]>
  ): Map<string, ComplianceForecast> {
    const results = new Map<string, ComplianceForecast>();
    for (const [controlId, data] of controls) {
      try {
        results.set(controlId, this.analyzeControl(controlId, data));
      } catch {
        // Skip controls with insufficient data
      }
    }
    return results;
  }

  /**
   * Organization-wide compliance forecast aggregating all known controls.
   * @param orgData - Map of controlId to historical data arrays.
   */
  analyzeOrganization(
    orgData: Map<string, DataPoint[]>
  ): {
    overallRisk: number;
    controlsAtRisk: number;
    criticalControls: string[];
    forecasts: Map<string, ComplianceForecast>;
  } {
    const forecasts = new Map<string, ComplianceForecast>();
    const criticalControls: string[] = [];

    for (const [controlId, data] of orgData) {
      try {
        const forecast = this.analyzeControl(controlId, data);
        forecasts.set(controlId, forecast);
        if (forecast.probability > 0.7) {
          criticalControls.push(controlId);
        }
      } catch {
        // Skip controls with insufficient data
      }
    }

    const probabilities = Array.from(forecasts.values()).map((f) => f.probability);
    const overallRisk = probabilities.length > 0 ? avg(probabilities) : 0;
    const controlsAtRisk = probabilities.filter((p) => p > 0.5).length;

    return { overallRisk, controlsAtRisk, criticalControls, forecasts };
  }

  /**
   * Detect anomalies across time-series data.
   * @param timeSeriesData - Array of time-series entries.
   * @param sensitivity    - Z-score threshold.
   */
  detectAnomalies(
    timeSeriesData: TimeSeriesEntry[],
    sensitivity: number = 2.0
  ): Map<string, Array<{ index: number; value: number; zscore: number }>> {
    const byMetric = new Map<string, TimeSeriesEntry[]>();
    for (const entry of timeSeriesData) {
      const arr = byMetric.get(entry.metric) ?? [];
      arr.push(entry);
      byMetric.set(entry.metric, arr);
    }

    for (const [metric, entries] of byMetric) {
      for (const e of entries) {
        this.timeSeries.addDataPoint(metric, e.value, e.timestamp);
      }
    }

    const results = new Map<string, Array<{ index: number; value: number; zscore: number }>>();
    for (const metric of byMetric.keys()) {
      const anomalies = this.timeSeries.detectAnomalies(metric, sensitivity);
      if (anomalies.length > 0) {
        results.set(metric, anomalies);
      }
    }

    return results;
  }

  /**
   * Generate a risk score for a control based on weighted factors.
   * @param controlId - The control identifier.
   * @param factors   - Array of risk factors with weights and values.
   */
  generateRiskScore(
    controlId: string,
    factors: RiskFactor[]
  ): { score: number; level: "critical" | "high" | "medium" | "low" } {
    const totalWeight = factors.reduce((s, f) => s + f.weight, 0);
    const score =
      totalWeight > 0
        ? factors.reduce((s, f) => s + f.weight * (1 - f.value), 0) / totalWeight
        : 0;

    let level: "critical" | "high" | "medium" | "low";
    if (score > 0.75) level = "critical";
    else if (score > 0.5) level = "high";
    else if (score > 0.25) level = "medium";
    else level = "low";

    return { score: clamp(score, 0, 1), level };
  }

  /**
   * Generate AI-powered remediation recommendations from a forecast.
   * @param forecast - The compliance forecast to act on.
   */
  recommendRemediation(forecast: ComplianceForecast): Remediation[] {
    return forecast.recommendations;
  }

  /**
   * Track a metric over time and return trend analysis.
   * @param metric     - The metric name.
   * @param dataPoints - Historical data points.
   */
  trackTrend(
    metric: string,
    dataPoints: DataPoint[]
  ): TrendAnalysis | null {
    for (const dp of dataPoints) {
      this.timeSeries.addDataPoint(metric, dp.value, dp.timestamp);
    }
    return this.timeSeries.detectTrend(metric);
  }

  /**
   * Export all stored forecasts in the specified format.
   * @param format - "json" or "csv".
   */
  exportForecast(format: ExportFormat): string {
    const forecasts = Array.from(this.forecasts.values());

    if (format === "json") {
      return JSON.stringify(forecasts, null, 2);
    }

    if (forecasts.length === 0) return "";

    const headers = [
      "controlId",
      "probability",
      "timeframe",
      "confidence",
      "recommendationCount",
    ];
    const rows = forecasts.map((f) =>
      [
        f.controlId,
        f.probability.toFixed(4),
        f.timeframe.toString(),
        f.confidence.toFixed(4),
        f.recommendations.length.toString(),
      ].join(",")
    );
    return [headers.join(","), ...rows].join("\n");
  }

  /** Access the underlying TimeSeriesAnalyzer. */
  get timeSeriesAnalyzer(): TimeSeriesAnalyzer {
    return this.timeSeries;
  }

  /** Access the underlying RiskScoringEngine. */
  get riskScoringEngine(): RiskScoringEngine {
    return this.riskEngine;
  }

  /** Access the underlying MonteCarloSimulator. */
  get monteCarloSimulator(): MonteCarloSimulator {
    return this.simulator;
  }

  /**
   * Return all stored forecasts.
   */
  forecastAll(): ComplianceForecast[] {
    return Array.from(this.forecasts.values());
  }

  /**
   * Rank all forecasts by risk score (descending).
   */
  rankByRisk(): ComplianceForecast[] {
    return Array.from(this.forecasts.values()).sort(
      (a, b) => b.probability - a.probability
    );
  }

  /**
   * Generate a forecast for a specific control.
   * Alias for analyzeControl.
   */
  generateForecast(
    controlId: string,
    historicalData?: DataPoint[]
  ): ComplianceForecast {
    return this.analyzeControl(controlId, historicalData ?? []);
  }

  // -- Private Helpers --

  private generateRecommendations(
    controlId: string,
    probability: number,
    trend: TrendAnalysis | null
  ): Remediation[] {
    const recs: Remediation[] = [];
    const now = new Date();

    if (probability > 0.7) {
      recs.push({
        id: `rec-${controlId}-critical`,
        title: "Immediate intervention required",
        description: `Control ${controlId} has a ${(probability * 100).toFixed(0)}% failure probability. Escalate to compliance team immediately.`,
        priority: "critical",
        estimatedEffort: 8,
        estimatedImpact: 0.4,
        deadline: new Date(now.getTime() + 3 * 86400000).toISOString(),
      });
    } else if (probability > 0.5) {
      recs.push({
        id: `rec-${controlId}-high`,
        title: "Schedule remediation review",
        description: `Control ${controlId} is at risk with ${(probability * 100).toFixed(0)}% failure probability.`,
        priority: "high",
        estimatedEffort: 4,
        estimatedImpact: 0.3,
        deadline: new Date(now.getTime() + 14 * 86400000).toISOString(),
      });
    }

    if (trend?.direction === "degrading") {
      recs.push({
        id: `rec-${controlId}-trend`,
        title: "Investigate root cause of degrading trend",
        description: `Compliance trend for ${controlId} is degrading at velocity ${trend.velocity.toFixed(4)}. Root cause analysis recommended.`,
        priority: "high",
        estimatedEffort: 6,
        estimatedImpact: 0.25,
        deadline: new Date(now.getTime() + 7 * 86400000).toISOString(),
      });
    }

    if (trend?.direction === "volatile") {
      recs.push({
        id: `rec-${controlId}-volatile`,
        title: "Stabilize control monitoring",
        description: `Metric for ${controlId} shows high volatility. Implement tighter monitoring thresholds.`,
        priority: "medium",
        estimatedEffort: 3,
        estimatedImpact: 0.15,
        deadline: new Date(now.getTime() + 21 * 86400000).toISOString(),
      });
    }

    return recs;
  }
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function avg(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((s, v) => s + v, 0) / values.length;
}

function standardDeviation(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = avg(values);
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

function linearRegression(values: number[]): { slope: number; intercept: number } {
  const n = values.length;
  if (n < 2) return { slope: 0, intercept: values[0] ?? 0 };

  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumXX = 0;

  for (let i = 0; i < n; i++) {
    sumX += i;
    sumY += values[i];
    sumXY += i * values[i];
    sumXX += i * i;
  }

  const denom = n * sumXX - sumX * sumX;
  if (denom === 0) return { slope: 0, intercept: sumY / n };

  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

function forecastLinear(
  values: number[],
  horizon: number,
  lastTimestamp: string
): DataPoint[] {
  const { slope, intercept } = linearRegression(values);
  const n = values.length;
  const lastDate = new Date(lastTimestamp);
  const result: DataPoint[] = [];

  for (let i = 1; i <= horizon; i++) {
    const date = new Date(lastDate.getTime() + i * 86400000);
    const predicted = intercept + slope * (n - 1 + i);
    result.push({
      timestamp: date.toISOString(),
      value: clamp(predicted, 0, 1),
    });
  }

  return result;
}

function gaussianSample(rng: () => number, mean: number, stdDev: number): number {
  const u1 = rng();
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1 || 1e-10)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

function createRng(seed?: number): () => number {
  if (seed === undefined) return Math.random;
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

/** Alias for backward compatibility */
export { PredictiveEngine as PredictiveComplianceEngine };
