export type DistributionType = 'normal' | 'lognormal' | 'uniform' | 'triangular' | 'betaPERT';

export interface DistributionParams {
  type: DistributionType;
  mean?: number;
  stdDev?: number;
  min?: number;
  max?: number;
  mode?: number;
  shape?: number;
  scale?: number;
}

export interface RiskScenario {
  id: string;
  name: string;
  threat: string;
  vulnerability: string;
  impact: DistributionParams;
  probability: DistributionParams;
  tags?: string[];
  owner?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface FAIRFactor {
  value: number;
  confidence?: number;
  source?: string;
}

export interface FAIRModel {
  threatEventFrequency: FAIRFactor;
  threatCapability: FAIRFactor;
  vulnerability: FAIRFactor;
  primaryLoss: FAIRFactor;
  secondaryLossFrequency?: FAIRFactor;
  secondaryLossMagnitude?: FAIRFactor;
  lossEventFrequency: number;
  lossMagnitude: number;
  annualizedLossExpectancy: number;
}

export interface MonteCarloResult {
  iterations: number;
  percentiles: {
    P10: number;
    P25: number;
    P50: number;
    P75: number;
    P90: number;
    P95: number;
    P99: number;
  };
  mean: number;
  stdDev: number;
  variance: number;
  min: number;
  max: number;
  valueAtRisk: { confidence95: number; confidence99: number };
  conditionalValueAtRisk: { confidence95: number; confidence99: number };
  histogram: Array<{ bucket: number; count: number; frequency: number }>;
  rawSamples: number[];
}

export interface RiskQuantification {
  scenario: RiskScenario;
  fairModel: FAIRModel;
  monteCarloResult: MonteCarloResult;
  riskScore: number;
  riskLevel: 'critical' | 'high' | 'medium' | 'low' | 'negligible';
  recommendation: string;
  calculatedAt: Date;
}

export interface RiskTrend {
  date: Date;
  riskScore: number;
  ale: number;
  scenarioId: string;
}

export interface RiskHeatMapCell {
  likelihood: number;
  impact: number;
  scenarios: string[];
  totalRisk: number;
}

export interface RiskHeatMap {
  cells: RiskHeatMapCell[];
  axisLabels: { x: string; y: string };
}

export interface RiskAppetite {
  maxRiskScore: number;
  maxALE: number;
  maxVaR95: number;
  tolerableScenarios: string[];
  boundaryExceedances: string[];
}

export interface RiskRegisterEntry {
  scenario: RiskScenario;
  quantification?: RiskQuantification;
  status: 'identified' | 'assessed' | 'treated' | 'accepted' | 'monitoring';
  lastAssessed?: Date;
  nextReview?: Date;
}
