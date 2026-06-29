/**
 * @grc-claw/predictive-compliance
 * AI-powered predictive compliance engine that predicts compliance failures
 * before they happen using historical data, real-time monitoring, and risk scoring.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ComplianceStatus = "compliant" | "non_compliant" | "at_risk" | "unknown";

export type SeverityLevel = "critical" | "high" | "medium" | "low" | "informational";

export type TrendDirection = "improving" | "stable" | "degrading" | "volatile";

export interface Control {
  id: string;
  frameworkId: string;
  controlId: string;
  name: string;
  description: string;
  status: ComplianceStatus;
  lastAssessedAt: string;
  nextAssessmentAt: string;
  tags: string[];
}

export interface ComplianceEvent {
  id: string;
  controlId: string;
  timestamp: string;
  status: ComplianceStatus;
  severity: SeverityLevel;
  metadata: Record<string, unknown>;
}

export interface RiskScore {
  controlId: string;
  score: number;
  confidence: number;
  factors: RiskFactor[];
  trend: TrendDirection;
  predictedFailureDate: string | null;
  updatedAt: string;
}

export interface RiskFactor {
  name: string;
  weight: number;
  value: number;
  description: string;
}

export interface TrendDataPoint {
  timestamp: string;
  value: number;
}

export interface TrendAnalysis {
  controlId: string;
  direction: TrendDirection;
  slope: number;
  volatility: number;
  seasonality: SeasonalityPattern | null;
  dataPoints: TrendDataPoint[];
  analysisWindow: number;
}

export interface SeasonalityPattern {
  period: number;
  amplitude: number;
  phase: number;
}

export interface ComplianceForecast {
  controlId: string;
  forecastDate: string;
  predictions: ForecastPoint[];
  confidenceLevel: number;
  riskRating: SeverityLevel;
  recommendedActions: RemediationAction[];
  modelUsed: string;
}

export interface ForecastPoint {
  timestamp: string;
  predictedStatus: ComplianceStatus;
  probability: number;
  lowerBound: number;
  upperBound: number;
}

export interface RemediationAction {
  id: string;
  title: string;
  description: string;
  priority: SeverityLevel;
  estimatedImpact: number;
  estimatedEffort: number;
  deadline: string;
}

export interface PredictionModel {
  id: string;
  name: string;
  version: string;
  train(data: TrainingData[]): void;
  predict(features: FeatureVector): PredictionResult;
  evaluate(testData: TrainingData[]): EvaluationResult;
}

export interface TrainingData {
  features: FeatureVector;
  label: ComplianceStatus;
  timestamp: string;
}

export interface FeatureVector {
  controlId: string;
  historicalComplianceRate: number;
  daysSinceLastFailure: number;
  averageRemediationTime: number;
  controlComplexity: number;
  organizationMaturity: number;
  industryRiskBaseline: number;
  recentAuditFindings: number;
  patchVelocity: number;
  changeFrequency: number;
}

export interface PredictionResult {
  status: ComplianceStatus;
  probability: number;
  confidence: number;
  contributingFactors: string[];
}

export interface EvaluationResult {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  auc: number;
}

export interface MonitoringSignal {
  controlId: string;
  metric: string;
  value: number;
  timestamp: string;
  source: string;
}

export interface EngineConfig {
  predictionHorizonDays: number;
  confidenceLevel: number;
  riskScoreWeights: RiskScoreWeights;
  trendAnalysisWindowDays: number;
  minimumDataPoints: number;
  models: PredictionModel[];
}

export interface RiskScoreWeights {
  historicalFailureRate: number;
  timeSinceLastAssessment: number;
  remediationLag: number;
  controlComplexity: number;
  organizationalReadiness: number;
}

export interface ContinuousTrustEvent {
  type: "trust_update" | "control_status_change" | "risk_threshold_exceeded";
  controlId: string;
  trustScore: number;
  metadata: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Default Configuration
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG: EngineConfig = {
  predictionHorizonDays: 60,
  confidenceLevel: 0.95,
  riskScoreWeights: {
    historicalFailureRate: 0.25,
    timeSinceLastAssessment: 0.2,
    remediationLag: 0.2,
    controlComplexity: 0.15,
    organizationalReadiness: 0.2,
  },
  trendAnalysisWindowDays: 180,
  minimumDataPoints: 10,
  models: [],
};

// ---------------------------------------------------------------------------
// CompliancePredictor
// ---------------------------------------------------------------------------

export class CompliancePredictor {
  private models: Map<string, PredictionModel> = new Map();
  private activeModelId: string | null = null;

  constructor(models: PredictionModel[] = []) {
    for (const model of models) {
      this.models.set(model.id, model);
    }
    if (models.length > 0) {
      this.activeModelId = models[0].id;
    }
  }

  registerModel(model: PredictionModel): void {
    this.models.set(model.id, model);
    if (this.activeModelId === null) {
      this.activeModelId = model.id;
    }
  }

  setActiveModel(modelId: string): void {
    if (!this.models.has(modelId)) {
      throw new Error(`Model "${modelId}" is not registered`);
    }
    this.activeModelId = modelId;
  }

  getActiveModel(): PredictionModel | null {
    if (this.activeModelId === null) return null;
    return this.models.get(this.activeModelId) ?? null;
  }

  trainActiveModel(data: TrainingData[]): void {
    const model = this.getActiveModel();
    if (model === null) {
      throw new Error("No active model set. Register a model first.");
    }
    model.train(data);
  }

  predict(features: FeatureVector): PredictionResult {
    const model = this.getActiveModel();
    if (model === null) {
      return this.fallbackPrediction(features);
    }
    return model.predict(features);
  }

  private fallbackPrediction(features: FeatureVector): PredictionResult {
    const complianceRate = features.historicalComplianceRate;
    const daysSinceFailure = features.daysSinceLastFailure;
    const complexity = features.controlComplexity;

    const baseProbability = complianceRate;
    const timeDecay = Math.max(0, 1 - daysSinceFailure / 365);
    const complexityPenalty = complexity * 0.1;

    const failureProbability = Math.min(
      1,
      Math.max(0, (1 - baseProbability) + timeDecay * 0.1 + complexityPenalty)
    );

    let status: ComplianceStatus;
    if (failureProbability > 0.7) status = "non_compliant";
    else if (failureProbability > 0.4) status = "at_risk";
    else status = "compliant";

    return {
      status,
      probability: 1 - failureProbability,
      confidence: Math.min(0.8, complianceRate * 0.9),
      contributingFactors: [
        "Historical compliance rate",
        "Days since last failure",
        "Control complexity",
      ],
    };
  }

  evaluateModel(modelId: string, testData: TrainingData[]): EvaluationResult | null {
    const model = this.models.get(modelId);
    if (!model) return null;
    return model.evaluate(testData);
  }

  listModels(): PredictionModel[] {
    return Array.from(this.models.values());
  }
}

// ---------------------------------------------------------------------------
// RiskScorer
// ---------------------------------------------------------------------------

export class RiskScorer {
  private weights: RiskScoreWeights;
  private scoreCache: Map<string, RiskScore> = new Map();

  constructor(weights: RiskScoreWeights = DEFAULT_CONFIG.riskScoreWeights) {
    this.weights = weights;
  }

  updateWeights(weights: Partial<RiskScoreWeights>): void {
    this.weights = { ...this.weights, ...weights };
  }

  calculateScore(
    control: Control,
    events: ComplianceEvent[],
    trend: TrendAnalysis | null
  ): RiskScore {
    const controlEvents = events.filter((e) => e.controlId === control.id);
    const failureCount = controlEvents.filter(
      (e) => e.status === "non_compliant"
    ).length;
    const totalEvents = controlEvents.length || 1;
    const historicalFailureRate = failureCount / totalEvents;

    const now = Date.now();
    const lastAssessed = new Date(control.lastAssessedAt).getTime();
    const daysSinceAssessment = (now - lastAssessed) / (1000 * 60 * 60 * 24);
    const assessmentRecency = Math.min(1, daysSinceAssessment / 90);

    const remediationTimes = controlEvents
      .filter((e) => e.status === "non_compliant")
      .map((e) => {
        const nextCompliant = controlEvents
          .filter(
            (ne) =>
              ne.controlId === e.controlId &&
              ne.status === "compliant" &&
              new Date(ne.timestamp).getTime() > new Date(e.timestamp).getTime()
          )
          .sort(
            (a, b) =>
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          )[0];
        if (!nextCompliant) return 30;
        return (
          (new Date(nextCompliant.timestamp).getTime() -
            new Date(e.timestamp).getTime()) /
          (1000 * 60 * 60 * 24)
        );
      });
    const avgRemediationTime =
      remediationTimes.length > 0
        ? remediationTimes.reduce((a, b) => a + b, 0) / remediationTimes.length
        : 15;
    const remediationLag = Math.min(1, avgRemediationTime / 60);

    const complexityFactors = control.tags.length * 0.05 + (control.description.length > 200 ? 0.2 : 0);
    const controlComplexity = Math.min(1, complexityFactors);

    const maturityProxy =
      1 -
      (controlEvents.filter((e) => e.severity === "critical").length /
        totalEvents);
    const organizationalReadiness = Math.max(0, Math.min(1, maturityProxy));

    const weightedScore =
      historicalFailureRate * this.weights.historicalFailureRate +
      assessmentRecency * this.weights.timeSinceLastAssessment +
      remediationLag * this.weights.remediationLag +
      controlComplexity * this.weights.controlComplexity +
      organizationalReadiness * this.weights.organizationalReadiness;

    const score = Math.min(1, Math.max(0, weightedScore));

    const factors: RiskFactor[] = [
      {
        name: "Historical Failure Rate",
        weight: this.weights.historicalFailureRate,
        value: historicalFailureRate,
        description: `Based on ${failureCount} failures out of ${totalEvents} events`,
      },
      {
        name: "Assessment Recency",
        weight: this.weights.timeSinceLastAssessment,
        value: assessmentRecency,
        description: `Last assessed ${Math.round(daysSinceAssessment)} days ago`,
      },
      {
        name: "Remediation Lag",
        weight: this.weights.remediationLag,
        value: remediationLag,
        description: `Average remediation takes ${Math.round(avgRemediationTime)} days`,
      },
      {
        name: "Control Complexity",
        weight: this.weights.controlComplexity,
        value: controlComplexity,
        description: `Complexity score based on tags and description`,
      },
      {
        name: "Organizational Readiness",
        weight: this.weights.organizationalReadiness,
        value: organizationalReadiness,
        description: `Maturity proxy from critical event ratio`,
      },
    ];

    const trendDirection = trend?.direction ?? "stable";
    const predictedFailureDate = this.predictFailureDate(score, trendDirection);

    const riskScore: RiskScore = {
      controlId: control.id,
      score,
      confidence: this.calculateConfidence(events.length),
      factors,
      trend: trendDirection,
      predictedFailureDate,
      updatedAt: new Date().toISOString(),
    };

    this.scoreCache.set(control.id, riskScore);
    return riskScore;
  }

  getCachedScore(controlId: string): RiskScore | undefined {
    return this.scoreCache.get(controlId);
  }

  clearCache(): void {
    this.scoreCache.clear();
  }

  rankControls(controls: Control[], events: ComplianceEvent[]): RiskScore[] {
    const scores = controls.map((control) => {
      const score = this.scoreCache.get(control.id);
      if (score) return score;
      return this.calculateScore(control, events, null);
    });
    return scores.sort((a, b) => b.score - a.score);
  }

  private predictFailureDate(
    score: number,
    trend: TrendDirection
  ): string | null {
    if (score < 0.3) return null;

    const baseDays = Math.round(180 * (1 - score));
    let adjustedDays: number;
    switch (trend) {
      case "degrading":
        adjustedDays = Math.round(baseDays * 0.6);
        break;
      case "improving":
        adjustedDays = Math.round(baseDays * 1.5);
        break;
      case "volatile":
        adjustedDays = Math.round(baseDays * 0.8);
        break;
      default:
        adjustedDays = baseDays;
    }

    const failureDate = new Date();
    failureDate.setDate(failureDate.getDate() + adjustedDays);
    return failureDate.toISOString();
  }

  private calculateConfidence(dataPointCount: number): number {
    return Math.min(0.99, 0.3 + (dataPointCount / 100) * 0.7);
  }
}

// ---------------------------------------------------------------------------
// TrendAnalyzer
// ---------------------------------------------------------------------------

export class TrendAnalyzer {
  private windowDays: number;
  private minimumDataPoints: number;

  constructor(
    windowDays: number = DEFAULT_CONFIG.trendAnalysisWindowDays,
    minimumDataPoints: number = DEFAULT_CONFIG.minimumDataPoints
  ) {
    this.windowDays = windowDays;
    this.minimumDataPoints = minimumDataPoints;
  }

  analyze(
    controlId: string,
    events: ComplianceEvent[]
  ): TrendAnalysis | null {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - this.windowDays);

    const relevantEvents = events
      .filter(
        (e) =>
          e.controlId === controlId &&
          new Date(e.timestamp).getTime() >= cutoff.getTime()
      )
      .sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

    if (relevantEvents.length < this.minimumDataPoints) {
      return null;
    }

    const dataPoints: TrendDataPoint[] = relevantEvents.map((e) => ({
      timestamp: e.timestamp,
      value: this.statusToNumeric(e.status),
    }));

    const values = dataPoints.map((dp) => dp.value);
    const n = values.length;
    const xMean = (n - 1) / 2;
    const yMean = values.reduce((a, b) => a + b, 0) / n;

    let numerator = 0;
    let denominator = 0;
    for (let i = 0; i < n; i++) {
      numerator += (i - xMean) * (values[i] - yMean);
      denominator += (i - xMean) * (i - xMean);
    }
    const slope = denominator !== 0 ? numerator / denominator : 0;

    const mean = yMean;
    const variance =
      values.reduce((sum, v) => sum + (v - mean) * (v - mean), 0) / n;
    const volatility = Math.sqrt(variance);

    const direction = this.classifyDirection(slope, volatility);
    const seasonality = this.detectSeasonality(values);

    return {
      controlId,
      direction,
      slope,
      volatility,
      seasonality,
      dataPoints,
      analysisWindow: this.windowDays,
    };
  }

  detectSeasonality(values: number[]): SeasonalityPattern | null {
    if (values.length < 14) return null;

    const n = values.length;
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const centered = values.map((v) => v - mean);

    let bestPeriod = 0;
    let bestCorrelation = 0;

    const maxPeriod = Math.min(Math.floor(n / 2), 30);
    for (let period = 2; period <= maxPeriod; period++) {
      let correlation = 0;
      let count = 0;
      for (let i = 0; i < n - period; i++) {
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

    if (Math.abs(bestCorrelation) < 0.3) return null;

    return {
      period: bestPeriod,
      amplitude: Math.abs(bestCorrelation),
      phase: 0,
    };
  }

  forecastFromTrend(
    trend: TrendAnalysis,
    horizonDays: number
  ): TrendDataPoint[] {
    const result: TrendDataPoint[] = [];
    const lastPoint = trend.dataPoints[trend.dataPoints.length - 1];
    const baseDate = new Date(lastPoint.timestamp);

    for (let d = 1; d <= horizonDays; d++) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() + d);

      let value = lastPoint.value + trend.slope * d;

      if (trend.seasonality) {
        const seasonalComponent =
          trend.seasonality.amplitude *
          Math.sin((2 * Math.PI * d) / trend.seasonality.period +
            trend.seasonality.phase);
        value += seasonalComponent;
      }

      value = Math.max(0, Math.min(1, value));

      result.push({
        timestamp: date.toISOString(),
        value,
      });
    }

    return result;
  }

  private statusToNumeric(status: ComplianceStatus): number {
    switch (status) {
      case "compliant":
        return 1;
      case "at_risk":
        return 0.5;
      case "non_compliant":
        return 0;
      case "unknown":
        return 0.5;
      default:
        return 0.5;
    }
  }

  private classifyDirection(
    slope: number,
    volatility: number
  ): TrendDirection {
    if (volatility > 0.3) return "volatile";
    if (slope > 0.01) return "improving";
    if (slope < -0.01) return "degrading";
    return "stable";
  }
}

// ---------------------------------------------------------------------------
// ComplianceForecast
// ---------------------------------------------------------------------------

export class ComplianceForecastModel implements ComplianceForecast {
  controlId: string;
  forecastDate: string;
  predictions: ForecastPoint[];
  confidenceLevel: number;
  riskRating: SeverityLevel;
  recommendedActions: RemediationAction[];
  modelUsed: string;

  constructor(params: {
    controlId: string;
    forecastDate: string;
    predictions: ForecastPoint[];
    confidenceLevel: number;
    riskRating: SeverityLevel;
    recommendedActions: RemediationAction[];
    modelUsed: string;
  }) {
    this.controlId = params.controlId;
    this.forecastDate = params.forecastDate;
    this.predictions = params.predictions;
    this.confidenceLevel = params.confidenceLevel;
    this.riskRating = params.riskRating;
    this.recommendedActions = params.recommendedActions;
    this.modelUsed = params.modelUsed;
  }

  getFailureProbability(): number {
    const failurePoints = this.predictions.filter(
      (p) => p.predictedStatus === "non_compliant"
    );
    if (failurePoints.length === 0) return 0;
    return failurePoints.reduce((max, p) => Math.max(max, p.probability), 0);
  }

  getTimeToFailure(): number | null {
    const firstFailure = this.predictions.find(
      (p) => p.predictedStatus === "non_compliant" && p.probability > 0.5
    );
    if (!firstFailure) return null;
    const now = new Date();
    const failureDate = new Date(firstFailure.timestamp);
    return Math.round(
      (failureDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );
  }

  getConfidenceInterval(
    timestamp: string
  ): { lower: number; upper: number } | null {
    const point = this.predictions.find((p) => p.timestamp === timestamp);
    if (!point) return null;
    return { lower: point.lowerBound, upper: point.upperBound };
  }

  toJSON(): Record<string, unknown> {
    return {
      controlId: this.controlId,
      forecastDate: this.forecastDate,
      predictions: this.predictions,
      confidenceLevel: this.confidenceLevel,
      riskRating: this.riskRating,
      recommendedActions: this.recommendedActions,
      modelUsed: this.modelUsed,
      failureProbability: this.getFailureProbability(),
      timeToFailure: this.getTimeToFailure(),
    };
  }
}

// ---------------------------------------------------------------------------
// PredictiveComplianceEngine
// ---------------------------------------------------------------------------

export class PredictiveComplianceEngine {
  private config: EngineConfig;
  private predictor: CompliancePredictor;
  private riskScorer: RiskScorer;
  private trendAnalyzer: TrendAnalyzer;
  private controls: Map<string, Control> = new Map();
  private events: ComplianceEvent[] = [];
  private signals: MonitoringSignal[] = [];
  private trustListeners: Array<(event: ContinuousTrustEvent) => void> = [];

  constructor(config: Partial<EngineConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.predictor = new CompliancePredictor(this.config.models);
    this.riskScorer = new RiskScorer(this.config.riskScoreWeights);
    this.trendAnalyzer = new TrendAnalyzer(
      this.config.trendAnalysisWindowDays,
      this.config.minimumDataPoints
    );
  }

  // -- Data Ingestion --

  registerControl(control: Control): void {
    this.controls.set(control.id, control);
  }

  registerControls(controls: Control[]): void {
    for (const c of controls) {
      this.controls.set(c.id, c);
    }
  }

  ingestEvent(event: ComplianceEvent): void {
    this.events.push(event);
  }

  ingestEvents(events: ComplianceEvent[]): void {
    this.events.push(...events);
  }

  ingestSignal(signal: MonitoringSignal): void {
    this.signals.push(signal);
  }

  ingestSignals(signals: MonitoringSignal[]): void {
    this.signals.push(...signals);
  }

  // -- Model Management --

  registerPredictionModel(model: PredictionModel): void {
    this.predictor.registerModel(model);
  }

  setActiveModel(modelId: string): void {
    this.predictor.setActiveModel(modelId);
  }

  trainModel(trainingData: TrainingData[]): void {
    this.predictor.trainActiveModel(trainingData);
  }

  // -- Prediction & Analysis --

  predictControl(controlId: string): PredictionResult | null {
    const control = this.controls.get(controlId);
    if (!control) return null;

    const features = this.buildFeatureVector(control);
    return this.predictor.predict(features);
  }

  scoreRisk(controlId: string): RiskScore | null {
    const control = this.controls.get(controlId);
    if (!control) return null;

    const trend = this.trendAnalyzer.analyze(controlId, this.events);
    return this.riskScorer.calculateScore(control, this.events, trend);
  }

  analyzeTrend(controlId: string): TrendAnalysis | null {
    return this.trendAnalyzer.analyze(controlId, this.events);
  }

  generateForecast(controlId: string): ComplianceForecastModel | null {
    const control = this.controls.get(controlId);
    if (!control) return null;

    const prediction = this.predictControl(controlId);
    const riskScore = this.scoreRisk(controlId);
    const trend = this.analyzeTrend(controlId);

    const horizonDays = this.config.predictionHorizonDays;
    const predictions = this.buildForecastPoints(
      control,
      prediction,
      trend,
      horizonDays
    );

    const riskRating = this.determineRiskRating(riskScore);
    const actions = this.generateRemediationActions(
      control,
      riskScore,
      trend,
      prediction
    );

    const modelName = this.predictor.getActiveModel()?.name ?? "fallback";

    return new ComplianceForecastModel({
      controlId,
      forecastDate: new Date().toISOString(),
      predictions,
      confidenceLevel: this.config.confidenceLevel,
      riskRating,
      recommendedActions: actions,
      modelUsed: modelName,
    });
  }

  forecastAll(): ComplianceForecastModel[] {
    const forecasts: ComplianceForecastModel[] = [];
    for (const controlId of this.controls.keys()) {
      const forecast = this.generateForecast(controlId);
      if (forecast) {
        forecasts.push(forecast);
      }
    }
    return forecasts;
  }

  rankByRisk(): RiskScore[] {
    return this.riskScorer.rankControls(
      Array.from(this.controls.values()),
      this.events
    );
  }

  // -- Continuous Trust Integration --

  onTrustEvent(listener: (event: ContinuousTrustEvent) => void): void {
    this.trustListeners.push(listener);
  }

  emitTrustEvent(event: ContinuousTrustEvent): void {
    for (const listener of this.trustListeners) {
      try {
        listener(event);
      } catch {
        // Listener errors should not break the engine
      }
    }
  }

  processTrustUpdate(
    controlId: string,
    trustScore: number
  ): PredictionResult | null {
    const control = this.controls.get(controlId);
    if (!control) return null;

    const prediction = this.predictControl(controlId);
    if (prediction && prediction.status === "non_compliant") {
      this.emitTrustEvent({
        type: "risk_threshold_exceeded",
        controlId,
        trustScore,
        metadata: {
          predictedStatus: prediction.status,
          probability: prediction.probability,
        },
        timestamp: new Date().toISOString(),
      });
    }
    return prediction;
  }

  // -- Diagnostics --

  getControlCount(): number {
    return this.controls.size;
  }

  getEventCount(): number {
    return this.events.length;
  }

  getSignalCount(): number {
    return this.signals.length;
  }

  // -- Private Helpers --

  private buildFeatureVector(control: Control): FeatureVector {
    const controlEvents = this.events.filter(
      (e) => e.controlId === control.id
    );
    const failureEvents = controlEvents.filter(
      (e) => e.status === "non_compliant"
    );

    const historicalComplianceRate =
      controlEvents.length > 0
        ? 1 - failureEvents.length / controlEvents.length
        : 0.5;

    const lastFailure = failureEvents
      .sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )[0];
    const daysSinceLastFailure = lastFailure
      ? (Date.now() - new Date(lastFailure.timestamp).getTime()) /
        (1000 * 60 * 60 * 24)
      : 365;

    const remediationTimes = failureEvents.map((fe) => {
      const nextCompliant = controlEvents
        .filter(
          (e) =>
            e.status === "compliant" &&
            new Date(e.timestamp).getTime() > new Date(fe.timestamp).getTime()
        )
        .sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        )[0];
      if (!nextCompliant) return 30;
      return (
        (new Date(nextCompliant.timestamp).getTime() -
          new Date(fe.timestamp).getTime()) /
        (1000 * 60 * 60 * 24)
      );
    });
    const averageRemediationTime =
      remediationTimes.length > 0
        ? remediationTimes.reduce((a, b) => a + b, 0) / remediationTimes.length
        : 15;

    const controlSignals = this.signals.filter(
      (s) => s.controlId === control.id
    );
    const patchVelocity =
      controlSignals.filter((s) => s.metric === "patch_applied").length;
    const changeFrequency =
      controlSignals.filter((s) => s.metric === "config_change").length;

    return {
      controlId: control.id,
      historicalComplianceRate,
      daysSinceLastFailure,
      averageRemediationTime,
      controlComplexity: control.tags.length * 0.1,
      organizationMaturity: 0.6,
      industryRiskBaseline: 0.3,
      recentAuditFindings: failureEvents.length,
      patchVelocity,
      changeFrequency,
    };
  }

  private buildForecastPoints(
    control: Control,
    prediction: PredictionResult | null,
    trend: TrendAnalysis | null,
    horizonDays: number
  ): ForecastPoint[] {
    const points: ForecastPoint[] = [];
    const now = new Date();
    const baseProbability = prediction?.probability ?? 0.5;

    for (let d = 0; d <= horizonDays; d += 7) {
      const date = new Date(now);
      date.setDate(date.getDate() + d);

      let decayedProbability = baseProbability;
      if (trend) {
        decayedProbability += trend.slope * d;
      }
      decayedProbability = Math.max(0, Math.min(1, decayedProbability));

      const uncertainty = (d / horizonDays) * 0.2 * (1 - (prediction?.confidence ?? 0.5));
      const lowerBound = Math.max(0, decayedProbability - uncertainty);
      const upperBound = Math.min(1, decayedProbability + uncertainty);

      let status: ComplianceStatus;
      if (decayedProbability > 0.7) status = "compliant";
      else if (decayedProbability > 0.4) status = "at_risk";
      else status = "non_compliant";

      points.push({
        timestamp: date.toISOString(),
        predictedStatus: status,
        probability: decayedProbability,
        lowerBound,
        upperBound,
      });
    }

    return points;
  }

  private determineRiskRating(
    riskScore: RiskScore | null
  ): SeverityLevel {
    if (!riskScore) return "low";
    const s = riskScore.score;
    if (s >= 0.8) return "critical";
    if (s >= 0.6) return "high";
    if (s >= 0.4) return "medium";
    if (s >= 0.2) return "low";
    return "informational";
  }

  private generateRemediationActions(
    control: Control,
    riskScore: RiskScore | null,
    trend: TrendAnalysis | null,
    prediction: PredictionResult | null
  ): RemediationAction[] {
    const actions: RemediationAction[] = [];

    if (riskScore && riskScore.score > 0.5) {
      actions.push({
        id: `rem-${control.id}-immediate`,
        title: `Immediate review of ${control.name}`,
        description:
          `Control "${control.name}" has a risk score of ${(riskScore.score * 100).toFixed(0)}%. Conduct an immediate compliance review.`,
        priority: riskScore.score > 0.7 ? "critical" : "high",
        estimatedImpact: 0.3,
        estimatedEffort: 2,
        deadline: new Date(
          Date.now() + 7 * 24 * 60 * 60 * 1000
        ).toISOString(),
      });
    }

    if (trend && trend.direction === "degrading") {
      actions.push({
        id: `rem-${control.id}-trend`,
        title: `Address degrading trend for ${control.name}`,
        description:
          `Compliance trend is degrading with a slope of ${trend.slope.toFixed(4)}. Investigate root cause and implement corrective measures.`,
        priority: "high",
        estimatedImpact: 0.25,
        estimatedEffort: 4,
        deadline: new Date(
          Date.now() + 14 * 24 * 60 * 60 * 1000
        ).toISOString(),
      });
    }

    if (
      prediction &&
      prediction.status === "at_risk" &&
      prediction.probability < 0.5
    ) {
      actions.push({
        id: `rem-${control.id}-preventive`,
        title: `Preventive action for ${control.name}`,
        description:
          `Control is predicted to become non-compliant with ${(prediction.probability * 100).toFixed(0)}% confidence. Implement preventive controls.`,
        priority: "medium",
        estimatedImpact: 0.2,
        estimatedEffort: 3,
        deadline: new Date(
          Date.now() + 30 * 24 * 60 * 60 * 1000
        ).toISOString(),
      });
    }

    const daysSinceAssessment =
      (Date.now() - new Date(control.lastAssessedAt).getTime()) /
      (1000 * 60 * 60 * 24);
    if (daysSinceAssessment > 60) {
      actions.push({
        id: `rem-${control.id}-reassess`,
        title: `Schedule reassessment for ${control.name}`,
        description:
          `Control has not been assessed for ${Math.round(daysSinceAssessment)} days. Schedule a reassessment to update compliance status.`,
        priority: "medium",
        estimatedImpact: 0.15,
        estimatedEffort: 1,
        deadline: new Date(
          Date.now() + 14 * 24 * 60 * 60 * 1000
        ).toISOString(),
      });
    }

    return actions;
  }
}
