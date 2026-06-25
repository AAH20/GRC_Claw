export type ThreatSeverity = "critical" | "high" | "medium" | "low" | "informational";
export type DetectionMethod = "anomaly" | "signature" | "behavioral" | "predictive" | "llm";

export interface ThreatSignal {
  id: string;
  source: string;
  timestamp: string;
  category: string;
  severity: ThreatSeverity;
  confidence: number;
  data: Record<string, unknown>;
}

export interface ThreatDetection {
  id: string;
  signalId: string;
  method: DetectionMethod;
  rule: string;
  description: string;
  severity: ThreatSeverity;
  confidence: number;
  affectedControls: string[];
  recommendation: string;
  detectedAt: string;
}

export interface AnomalyBaseline {
  metric: string;
  mean: number;
  stdDev: number;
  sampleCount: number;
  lastUpdated: string;
}

export interface LLMAnalysisRequest {
  signals: ThreatSignal[];
  context: string;
  framework: string;
}

export interface LLMAnalysisResponse {
  summary: string;
  threats: ThreatDetection[];
  recommendations: string[];
  confidence: number;
}

export interface PredictiveForecast {
  metric: string;
  currentValue: number;
  predictedValue: number;
  timeframe: string;
  confidence: number;
  trend: "increasing" | "decreasing" | "stable";
}
