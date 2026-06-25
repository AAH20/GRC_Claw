import type { ThreatSignal, ThreatDetection, AnomalyBaseline, PredictiveForecast } from "../types.js";

export class AnomalyDetector {
  private baselines: Map<string, AnomalyBaseline> = new Map();
  private threshold: number;

  constructor(threshold: number = 2.0) {
    this.threshold = threshold;
  }

  updateBaseline(metric: string, value: number): void {
    const existing = this.baselines.get(metric);
    if (existing) {
      const newMean = (existing.mean * existing.sampleCount + value) / (existing.sampleCount + 1);
      const variance = Math.pow(value - newMean, 2);
      const newStdDev = Math.sqrt((Math.pow(existing.stdDev, 2) * existing.sampleCount + variance) / (existing.sampleCount + 1));
      this.baselines.set(metric, {
        metric,
        mean: newMean,
        stdDev: newStdDev,
        sampleCount: existing.sampleCount + 1,
        lastUpdated: new Date().toISOString(),
      });
    } else {
      this.baselines.set(metric, {
        metric,
        mean: value,
        stdDev: 0,
        sampleCount: 1,
        lastUpdated: new Date().toISOString(),
      });
    }
  }

  detect(metric: string, value: number): ThreatDetection | null {
    const baseline = this.baselines.get(metric);
    if (!baseline || baseline.sampleCount < 10) return null;

    const zScore = Math.abs((value - baseline.mean) / (baseline.stdDev || 1));
    if (zScore < this.threshold) return null;

    return {
      id: `anomaly-${Date.now()}`,
      signalId: "",
      method: "anomaly",
      rule: `z_score_${metric}`,
      description: `Anomalous value for ${metric}: ${value} (z-score: ${zScore.toFixed(2)})`,
      severity: zScore > 4 ? "critical" : zScore > 3 ? "high" : "medium",
      confidence: Math.min(0.99, 0.5 + zScore * 0.1),
      affectedControls: [],
      recommendation: `Investigate ${metric} deviation from baseline`,
      detectedAt: new Date().toISOString(),
    };
  }

  forecast(metric: string, steps: number = 5): PredictiveForecast | null {
    const baseline = this.baselines.get(metric);
    if (!baseline || baseline.sampleCount < 20) return null;

    const trend = baseline.mean > 0 ? "stable" : "stable";
    return {
      metric,
      currentValue: baseline.mean,
      predictedValue: baseline.mean + (baseline.stdDev * steps * 0.1),
      timeframe: `${steps * 5} minutes`,
      confidence: Math.min(0.9, baseline.sampleCount / 100),
      trend,
    };
  }

  getBaselines(): AnomalyBaseline[] {
    return Array.from(this.baselines.values());
  }
}
