import type { TrustScoreDimensions, RiskFactor, BehavioralSignal, TrustScoreConfig } from "../types.js";

const DEFAULT_CONFIG: TrustScoreConfig = {
  identityWeight: 0.2,
  capabilityWeight: 0.15,
  complianceWeight: 0.25,
  behaviorWeight: 0.25,
  provenanceWeight: 0.15,
  decayRate: 0.01,
  minScore: 0 as any,
  maxScore: 100 as any,
};

export class TrustScoreCalculator {
  private config: TrustScoreConfig;

  constructor(config: Partial<TrustScoreConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  calculateOverallScore(dimensions: TrustScoreDimensions): number {
    const weightedScore =
      dimensions.identity * this.config.identityWeight +
      dimensions.capability * this.config.capabilityWeight +
      dimensions.compliance * this.config.complianceWeight +
      dimensions.behavior * this.config.behaviorWeight +
      dimensions.provenance * this.config.provenanceWeight;

    return Math.round(Math.max(0, Math.min(100, weightedScore)));
  }

  calculateRiskLevel(score: number): "minimal" | "low" | "medium" | "high" | "critical" {
    if (score >= 90) return "minimal";
    if (score >= 70) return "low";
    if (score >= 50) return "medium";
    if (score >= 30) return "high";
    return "critical";
  }

  applyTimeDecay(score: number, lastScoredAt: string): number {
    const hoursSinceLastScore = (Date.now() - new Date(lastScoredAt).getTime()) / 3600000;
    const decay = hoursSinceLastScore * this.config.decayRate;
    return Math.max(0, score - decay);
  }

  identifyRiskFactors(dimensions: TrustScoreDimensions, signals: BehavioralSignal[]): RiskFactor[] {
    const factors: RiskFactor[] = [];

    if (dimensions.identity < 50) {
      factors.push({
        id: "rf-identity-low",
        category: "identity",
        description: "Low identity trust score indicates potential authentication or credential issues",
        severity: "high",
        weight: 0.3,
        mitigated: false,
      });
    }

    if (dimensions.behavior < 40) {
      factors.push({
        id: "rf-behavior-critical",
        category: "behavior",
        description: "Critical behavioral anomalies detected requiring immediate review",
        severity: "critical",
        weight: 0.4,
        mitigated: false,
      });
    }

    if (dimensions.compliance < 60) {
      factors.push({
        id: "rf-compliance-gap",
        category: "compliance",
        description: "Significant compliance gaps affecting agent authorization",
        severity: "medium",
        weight: 0.25,
        mitigated: false,
      });
    }

    const anomalySignals = signals.filter((s) => s.type !== "normal_operation" && s.confidence > 0.7);
    if (anomalySignals.length > 3) {
      factors.push({
        id: "rf-anomaly-cluster",
        category: "behavior",
        description: `Cluster of ${anomalySignals.length} behavioral anomalies detected`,
        severity: "high",
        weight: 0.35,
        mitigated: false,
      });
    }

    return factors;
  }

  calculateDimensionScore(
    dimension: keyof TrustScoreDimensions,
    signals: BehavioralSignal[],
    complianceScore?: number
  ): number {
    let baseScore = 80;

    switch (dimension) {
      case "identity":
        baseScore = 85;
        break;
      case "capability":
        baseScore = 75;
        break;
      case "compliance":
        baseScore = complianceScore ?? 70;
        break;
      case "behavior":
        baseScore = 90;
        for (const signal of signals) {
          if (signal.type !== "normal_operation") {
            baseScore -= signal.impact * signal.confidence;
          }
        }
        break;
      case "provenance":
        baseScore = 80;
        break;
    }

    return Math.max(0, Math.min(100, baseScore));
  }
}
