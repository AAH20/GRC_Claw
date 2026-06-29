/**
 * @grc-claw/compliance-digital-twin
 * Compliance digital twin that creates a virtual representation of the entire
 * compliance landscape. Enables simulation, forecasting, and what-if analysis
 * for compliance decisions.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ComplianceStatus =
  | "compliant"
  | "non_compliant"
  | "at_risk"
  | "unknown";

export type SeverityLevel =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

export type SimulationState = "idle" | "running" | "completed" | "failed";

export type SyncMode = "full" | "incremental" | "manual";

export type TwinHealthStatus = "healthy" | "degraded" | "disconnected" | "stale";

// -- Domain Models --

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

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  controls: string[];
  description: string;
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
  trend: "improving" | "stable" | "degrading" | "volatile";
  predictedFailureDate: string | null;
  updatedAt: string;
}

export interface RiskFactor {
  name: string;
  weight: number;
  value: number;
  description: string;
}

// -- Digital Twin Models --

export interface TwinSnapshot {
  id: string;
  twinId: string;
  timestamp: string;
  controls: Map<string, Control>;
  events: ComplianceEvent[];
  riskScores: Map<string, RiskScore>;
  complianceRate: number;
  metadata: Record<string, unknown>;
}

export interface TwinConfiguration {
  twinId: string;
  name: string;
  description: string;
  frameworks: string[];
  syncMode: SyncMode;
  syncIntervalMs: number;
  snapshotRetentionCount: number;
  riskThresholds: RiskThresholds;
  createdAt: string;
  updatedAt: string;
}

export interface RiskThresholds {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface TwinState {
  id: string;
  config: TwinConfiguration;
  controls: Map<string, Control>;
  events: ComplianceEvent[];
  riskScores: Map<string, RiskScore>;
  snapshots: TwinSnapshot[];
  lastSyncedAt: string | null;
  health: TwinHealthStatus;
  version: number;
}

// -- Simulation Models --

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  baselineTwinId: string;
  changes: SimulationChange[];
  parameters: SimulationParameters;
}

export interface SimulationChange {
  type: "status_change" | "control_add" | "control_remove" | "framework_update" | "event_inject";
  controlId?: string;
  frameworkId?: string;
  fromStatus?: ComplianceStatus;
  toStatus?: ComplianceStatus;
  event?: Partial<ComplianceEvent>;
  metadata?: Record<string, unknown>;
}

export interface SimulationParameters {
  timeHorizonDays: number;
  stepSizeDays: number;
  monteCarloRuns: number;
  randomSeed?: number;
  includeSeasonality: boolean;
}

export interface SimulationResult {
  id: string;
  scenarioId: string;
  state: SimulationState;
  startedAt: string;
  completedAt: string | null;
  baselineComplianceRate: number;
  finalComplianceRate: number;
  complianceRateOverTime: TimeSeriesDataPoint[];
  riskScoreChanges: RiskScoreDelta[];
  controlImpact: ControlImpactSummary[];
  statistics: SimulationStatistics;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  lowerBound?: number;
  upperBound?: number;
}

export interface RiskScoreDelta {
  controlId: string;
  before: number;
  after: number;
  delta: number;
  direction: "improved" | "degraded" | "unchanged";
}

export interface ControlImpactSummary {
  controlId: string;
  controlName: string;
  impactScore: number;
  affectedByChanges: string[];
  riskContribution: number;
}

export interface SimulationStatistics {
  meanComplianceRate: number;
  medianComplianceRate: number;
  stdDevComplianceRate: number;
  minComplianceRate: number;
  maxComplianceRate: number;
  probabilityOfFailure: number;
  expectedTimeToFailure: number | null;
  valueAtRisk: number;
}

// -- What-If Analysis Models --

export interface WhatIfQuery {
  id: string;
  name: string;
  description: string;
  twinId: string;
  hypothesis: WhatIfHypothesis;
  parameters: WhatIfParameters;
}

export interface WhatIfHypothesis {
  type: "resource_allocation" | "policy_change" | "control_upgrade" | "framework_adoption" | "incident_response";
  description: string;
  affectedControls: string[];
  resourceDelta?: ResourceDelta;
  policyChanges?: PolicyChange[];
}

export interface ResourceDelta {
  budgetChange: number;
  staffingChange: number;
  toolingChange: string[];
}

export interface PolicyChange {
  policyId: string;
  fromValue: unknown;
  toValue: unknown;
  description: string;
}

export interface WhatIfParameters {
  analysisWindowDays: number;
  confidenceLevel: number;
  includeCascadingEffects: boolean;
  maxCascadingDepth: number;
}

export interface WhatIfResult {
  id: string;
  queryId: string;
  hypothesis: WhatIfHypothesis;
  baselineState: TwinSnapshot;
  projectedState: TwinSnapshot;
  impactAnalysis: WhatIfImpactAnalysis;
  recommendations: WhatIfRecommendation[];
  confidence: number;
  generatedAt: string;
}

export interface WhatIfImpactAnalysis {
  overallScoreChange: number;
  complianceRateChange: number;
  riskReduction: number;
  affectedControls: WhatIfControlImpact[];
  cascadingEffects: CascadingEffect[];
  timeToImpact: number;
}

export interface WhatIfControlImpact {
  controlId: string;
  currentRisk: number;
  projectedRisk: number;
  riskDelta: number;
  confidence: number;
}

export interface CascadingEffect {
  sourceControlId: string;
  targetControlId: string;
  effectType: "risk_propagation" | "dependency_enhancement" | "shared_failure";
  magnitude: number;
  description: string;
}

export interface WhatIfRecommendation {
  id: string;
  priority: SeverityLevel;
  title: string;
  description: string;
  estimatedImpact: number;
  estimatedEffort: number;
  prerequisites: string[];
}

// -- Forecasting Models --

export interface ForecastRequest {
  twinId: string;
  controlIds: string[];
  horizonDays: number;
  confidenceLevel: number;
  includeSeasonality: boolean;
}

export interface ComplianceForecast {
  controlId: string;
  forecastDate: string;
  predictions: ForecastPoint[];
  confidenceLevel: number;
  riskRating: SeverityLevel;
  recommendedActions: ForecastAction[];
}

export interface ForecastPoint {
  timestamp: string;
  predictedStatus: ComplianceStatus;
  probability: number;
  lowerBound: number;
  upperBound: number;
}

export interface ForecastAction {
  id: string;
  title: string;
  description: string;
  priority: SeverityLevel;
  estimatedImpact: number;
  deadline: string;
}

export interface ForecastAccuracy {
  controlId: string;
  mape: number;
  rmse: number;
  directionalAccuracy: number;
  sampleSize: number;
}

// -- Synchronization Models --

export interface SyncCheckpoint {
  id: string;
  twinId: string;
  timestamp: string;
  version: number;
  changesApplied: SyncChange[];
  durationMs: number;
}

export interface SyncChange {
  entityType: "control" | "event" | "risk_score" | "framework";
  entityId: string;
  action: "created" | "updated" | "deleted";
  previousValue: unknown;
  newValue: unknown;
}

export interface SyncHealthReport {
  twinId: string;
  status: TwinHealthStatus;
  lastSyncAt: string | null;
  syncLatencyMs: number;
  dataFreshnessMs: number;
  driftScore: number;
  issues: SyncIssue[];
}

export interface SyncIssue {
  type: "data_drift" | "sync_failure" | "stale_data" | "schema_mismatch";
  severity: SeverityLevel;
  message: string;
  detectedAt: string;
  resolvedAt: string | null;
}

// -- Visualization & Reporting Models --

export interface TwinDashboard {
  twinId: string;
  generatedAt: string;
  summary: DashboardSummary;
  controlStatus: ControlStatusBreakdown;
  riskHeatmap: RiskHeatmapData[];
  trendChart: TrendChartData;
  frameworkCompliance: FrameworkComplianceData[];
}

export interface DashboardSummary {
  totalControls: number;
  compliantCount: number;
  nonCompliantCount: number;
  atRiskCount: number;
  unknownCount: number;
  overallComplianceRate: number;
  criticalRisks: number;
  highRisks: number;
  lastUpdated: string;
}

export interface ControlStatusBreakdown {
  byFramework: Array<{
    frameworkId: string;
    frameworkName: string;
    compliant: number;
    nonCompliant: number;
    atRisk: number;
    unknown: number;
  }>;
  bySeverity: Record<SeverityLevel, number>;
}

export interface RiskHeatmapData {
  controlId: string;
  controlName: string;
  frameworkId: string;
  likelihood: number;
  impact: number;
  riskScore: number;
  status: ComplianceStatus;
}

export interface TrendChartData {
  timestamps: string[];
  series: Array<{
    name: string;
    data: number[];
  }>;
}

export interface FrameworkComplianceData {
  frameworkId: string;
  frameworkName: string;
  complianceRate: number;
  totalControls: number;
  compliantControls: number;
  lastAssessed: string;
}

// -- Event Types --

export interface TwinEvent {
  type:
    | "twin_created"
    | "twin_updated"
    | "snapshot_taken"
    | "simulation_started"
    | "simulation_completed"
    | "whatif_analyzed"
    | "forecast_generated"
    | "sync_completed"
    | "sync_failed"
    | "health_changed";
  twinId: string;
  timestamp: string;
  data: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Default Configuration
// ---------------------------------------------------------------------------

const DEFAULT_RISK_THRESHOLDS: RiskThresholds = {
  critical: 0.8,
  high: 0.6,
  medium: 0.4,
  low: 0.2,
};

const DEFAULT_SIMULATION_PARAMS: SimulationParameters = {
  timeHorizonDays: 90,
  stepSizeDays: 7,
  monteCarloRuns: 100,
  includeSeasonality: false,
};

const DEFAULT_WHATIF_PARAMS: WhatIfParameters = {
  analysisWindowDays: 90,
  confidenceLevel: 0.95,
  includeCascadingEffects: true,
  maxCascadingDepth: 3,
};

// ---------------------------------------------------------------------------
// ComplianceDigitalTwin
// ---------------------------------------------------------------------------

/**
 * Main digital twin class that creates and manages a virtual representation
 * of the compliance environment.
 */
export class ComplianceDigitalTwin {
  private twins: Map<string, TwinState> = new Map();
  private eventListeners: Array<(event: TwinEvent) => void> = [];

  createTwin(config: Omit<TwinConfiguration, "createdAt" | "updatedAt">): TwinState {
    if (this.twins.has(config.twinId)) {
      throw new Error(`Twin "${config.twinId}" already exists`);
    }

    const now = new Date().toISOString();
    const fullConfig: TwinConfiguration = {
      ...config,
      createdAt: now,
      updatedAt: now,
    };

    const state: TwinState = {
      id: config.twinId,
      config: fullConfig,
      controls: new Map(),
      events: [],
      riskScores: new Map(),
      snapshots: [],
      lastSyncedAt: null,
      health: "healthy",
      version: 1,
    };

    this.twins.set(config.twinId, state);
    this.emit({
      type: "twin_created",
      twinId: config.twinId,
      timestamp: now,
      data: { name: config.name },
    });

    return state;
  }

  getTwin(twinId: string): TwinState | undefined {
    return this.twins.get(twinId);
  }

  deleteTwin(twinId: string): boolean {
    const existed = this.twins.has(twinId);
    this.twins.delete(twinId);
    return existed;
  }

  listTwins(): TwinState[] {
    return Array.from(this.twins.values());
  }

  loadControls(twinId: string, controls: Control[]): void {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    for (const control of controls) {
      twin.controls.set(control.id, control);
    }
    twin.version++;
  }

  ingestEvents(twinId: string, events: ComplianceEvent[]): void {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    twin.events.push(...events);
    twin.version++;
  }

  updateRiskScores(twinId: string, scores: RiskScore[]): void {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    for (const score of scores) {
      twin.riskScores.set(score.controlId, score);
    }
    twin.version++;
  }

  takeSnapshot(twinId: string, metadata: Record<string, unknown> = {}): TwinSnapshot {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    const snapshot: TwinSnapshot = {
      id: `snap-${twinId}-${Date.now()}`,
      twinId,
      timestamp: new Date().toISOString(),
      controls: new Map(twin.controls),
      events: [...twin.events],
      riskScores: new Map(twin.riskScores),
      complianceRate: this.calculateComplianceRate(twin),
      metadata,
    };

    twin.snapshots.push(snapshot);

    if (twin.snapshots.length > twin.config.snapshotRetentionCount) {
      twin.snapshots.shift();
    }

    this.emit({
      type: "snapshot_taken",
      twinId,
      timestamp: snapshot.timestamp,
      data: { snapshotId: snapshot.id, complianceRate: snapshot.complianceRate },
    });

    return snapshot;
  }

  getComplianceRate(twinId: string): number {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);
    return this.calculateComplianceRate(twin);
  }

  getControlStatusSummary(twinId: string): Record<ComplianceStatus, number> {
    const twin = this.twins.get(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    const summary: Record<ComplianceStatus, number> = {
      compliant: 0,
      non_compliant: 0,
      at_risk: 0,
      unknown: 0,
    };

    for (const control of twin.controls.values()) {
      summary[control.status]++;
    }

    return summary;
  }

  calculateComplianceRate(twin: TwinState): number {
    if (twin.controls.size === 0) return 0;

    let compliant = 0;
    for (const control of twin.controls.values()) {
      if (control.status === "compliant") compliant++;
    }
    return compliant / twin.controls.size;
  }

  onEvent(listener: (event: TwinEvent) => void): () => void {
    this.eventListeners.push(listener);
    return () => {
      const idx = this.eventListeners.indexOf(listener);
      if (idx >= 0) this.eventListeners.splice(idx, 1);
    };
  }

  private emit(event: TwinEvent): void {
    for (const listener of this.eventListeners) {
      try {
        listener(event);
      } catch {
        // Listener errors should not break the twin
      }
    }
  }
}

// ---------------------------------------------------------------------------
// TwinSimulator
// ---------------------------------------------------------------------------

/**
 * Simulation engine that runs scenarios against digital twins to model
 * the impact of compliance changes over time.
 */
export class TwinSimulator {
  private twin: ComplianceDigitalTwin;
  private scenarios: Map<string, SimulationScenario> = new Map();
  private results: Map<string, SimulationResult> = new Map();

  constructor(twin: ComplianceDigitalTwin) {
    this.twin = twin;
  }

  createScenario(
    scenario: Omit<SimulationScenario, "id"> & { id?: string }
  ): SimulationScenario {
    const id = scenario.id ?? `sim-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const full: SimulationScenario = { ...scenario, id };
    this.scenarios.set(id, full);
    return full;
  }

  getScenario(id: string): SimulationScenario | undefined {
    return this.scenarios.get(id);
  }

  listScenarios(): SimulationScenario[] {
    return Array.from(this.scenarios.values());
  }

  runSimulation(scenarioId: string): SimulationResult {
    const scenario = this.scenarios.get(scenarioId);
    if (!scenario) throw new Error(`Scenario "${scenarioId}" not found`);

    const twinState = this.twin.getTwin(scenario.baselineTwinId);
    if (!twinState) throw new Error(`Twin "${scenario.baselineTwinId}" not found`);

    const resultId = `result-${scenarioId}-${Date.now()}`;
    const baselineRate = this.twin.calculateComplianceRate(twinState);

    const result: SimulationResult = {
      id: resultId,
      scenarioId,
      state: "running",
      startedAt: new Date().toISOString(),
      completedAt: null,
      baselineComplianceRate: baselineRate,
      finalComplianceRate: baselineRate,
      complianceRateOverTime: [],
      riskScoreChanges: [],
      controlImpact: [],
      statistics: this.emptyStatistics(),
    };

    this.results.set(resultId, result);

    try {
      const simulatedState = this.applyChanges(twinState, scenario.changes);
      const timeSeries = this.simulateOverTime(simulatedState, scenario.parameters);
      const riskChanges = this.computeRiskDeltas(twinState, simulatedState);
      const controlImpact = this.computeControlImpact(scenario, simulatedState);
      const stats = this.computeStatistics(timeSeries, scenario.parameters);

      result.finalComplianceRate = timeSeries[timeSeries.length - 1]?.value ?? baselineRate;
      result.complianceRateOverTime = timeSeries;
      result.riskScoreChanges = riskChanges;
      result.controlImpact = controlImpact;
      result.statistics = stats;
      result.state = "completed";
      result.completedAt = new Date().toISOString();
    } catch (err) {
      result.state = "failed";
      result.completedAt = new Date().toISOString();
    }

    return result;
  }

  getResult(id: string): SimulationResult | undefined {
    return this.results.get(id);
  }

  listResults(): SimulationResult[] {
    return Array.from(this.results.values());
  }

  private applyChanges(
    twinState: TwinState,
    changes: SimulationChange[]
  ): TwinState {
    const cloned: TwinState = {
      ...twinState,
      controls: new Map(
        Array.from(twinState.controls.entries()).map(([k, v]) => [k, { ...v }])
      ),
      events: [...twinState.events],
      riskScores: new Map(
        Array.from(twinState.riskScores.entries()).map(([k, v]) => [k, { ...v }])
      ),
      snapshots: [],
    };

    for (const change of changes) {
      switch (change.type) {
        case "status_change": {
          if (change.controlId && change.toStatus) {
            const ctrl = cloned.controls.get(change.controlId);
            if (ctrl) {
              ctrl.status = change.toStatus;
            }
          }
          break;
        }
        case "control_add": {
          if (change.controlId && change.metadata) {
            const newControl: Control = {
              id: change.controlId,
              frameworkId: (change.metadata.frameworkId as string) ?? "unknown",
              controlId: change.controlId,
              name: (change.metadata.name as string) ?? change.controlId,
              description: (change.metadata.description as string) ?? "",
              status: "compliant",
              lastAssessedAt: new Date().toISOString(),
              nextAssessmentAt: new Date(Date.now() + 90 * 86400000).toISOString(),
              tags: (change.metadata.tags as string[]) ?? [],
            };
            cloned.controls.set(change.controlId, newControl);
          }
          break;
        }
        case "control_remove": {
          if (change.controlId) {
            cloned.controls.delete(change.controlId);
          }
          break;
        }
        case "event_inject": {
          if (change.event) {
            const event: ComplianceEvent = {
              id: change.event.id ?? `evt-${Date.now()}`,
              controlId: change.event.controlId ?? "",
              timestamp: change.event.timestamp ?? new Date().toISOString(),
              status: change.event.status ?? "unknown",
              severity: change.event.severity ?? "low",
              metadata: change.event.metadata ?? {},
            };
            cloned.events.push(event);
          }
          break;
        }
      }
    }

    return cloned;
  }

  private simulateOverTime(
    state: TwinState,
    params: SimulationParameters
  ): TimeSeriesDataPoint[] {
    const points: TimeSeriesDataPoint[] = [];
    const now = new Date();
    const steps = Math.ceil(params.timeHorizonDays / params.stepSizeDays);

    let currentRate = this.twin.calculateComplianceRate(state);

    for (let i = 0; i <= steps; i++) {
      const date = new Date(now);
      date.setDate(date.getDate() + i * params.stepSizeDays);

      const noise = this.generateNoise(i, params);
      const trendComponent = this.computeTrendComponent(state, i, params);

      let rate = currentRate + trendComponent + noise;
      rate = Math.max(0, Math.min(1, rate));

      const uncertainty = (i / steps) * 0.15;
      points.push({
        timestamp: date.toISOString(),
        value: rate,
        lowerBound: Math.max(0, rate - uncertainty),
        upperBound: Math.min(1, rate + uncertainty),
      });

      currentRate = rate;
    }

    return points;
  }

  private generateNoise(step: number, params: SimulationParameters): number {
    if (params.randomSeed !== undefined) {
      const seed = params.randomSeed + step;
      const x = Math.sin(seed) * 10000;
      return (x - Math.floor(x)) * 0.04 - 0.02;
    }
    return Math.random() * 0.04 - 0.02;
  }

  private computeTrendComponent(
    state: TwinState,
    step: number,
    params: SimulationParameters
  ): number {
    let trendSum = 0;
    let count = 0;

    for (const score of state.riskScores.values()) {
      if (score.trend === "degrading") trendSum -= 0.005;
      else if (score.trend === "improving") trendSum += 0.003;
      count++;
    }

    if (count === 0) return 0;
    return (trendSum / count) * (1 + step * 0.01);
  }

  private computeRiskDeltas(
    original: TwinState,
    simulated: TwinState
  ): RiskScoreDelta[] {
    const deltas: RiskScoreDelta[] = [];

    for (const [controlId, originalScore] of original.riskScores) {
      const simulatedScore = simulated.riskScores.get(controlId);
      if (!simulatedScore) continue;

      const delta = simulatedScore.score - originalScore.score;
      deltas.push({
        controlId,
        before: originalScore.score,
        after: simulatedScore.score,
        delta,
        direction: delta > 0.01 ? "degraded" : delta < -0.01 ? "improved" : "unchanged",
      });
    }

    return deltas;
  }

  private computeControlImpact(
    scenario: SimulationScenario,
    state: TwinState
  ): ControlImpactSummary[] {
    const impact: ControlImpactSummary[] = [];

    for (const change of scenario.changes) {
      if (!change.controlId) continue;

      const control = state.controls.get(change.controlId);
      const score = state.riskScores.get(change.controlId);

      impact.push({
        controlId: change.controlId,
        controlName: control?.name ?? change.controlId,
        impactScore: score?.score ?? 0.5,
        affectedByChanges: [change.type],
        riskContribution: score?.score ?? 0.5,
      });
    }

    return impact;
  }

  private computeStatistics(
    timeSeries: TimeSeriesDataPoint[],
    params: SimulationParameters
  ): SimulationStatistics {
    if (timeSeries.length === 0) return this.emptyStatistics();

    const values = timeSeries.map((p) => p.value);
    const sorted = [...values].sort((a, b) => a - b);
    const n = values.length;

    const mean = values.reduce((a, b) => a + b, 0) / n;
    const median = n % 2 === 0
      ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
      : sorted[Math.floor(n / 2)];

    const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / n;
    const stdDev = Math.sqrt(variance);

    const failureThreshold = 0.3;
    const failureRuns = values.filter((v) => v < failureThreshold).length;
    const probabilityOfFailure = failureRuns / n;

    const timeToFailure = this.estimateTimeToFailure(timeSeries, failureThreshold);

    const varIndex = Math.floor(n * 0.05);
    const valueAtRisk = sorted[varIndex] ?? 0;

    return {
      meanComplianceRate: mean,
      medianComplianceRate: median,
      stdDevComplianceRate: stdDev,
      minComplianceRate: sorted[0],
      maxComplianceRate: sorted[n - 1],
      probabilityOfFailure,
      expectedTimeToFailure: timeToFailure,
      valueAtRisk,
    };
  }

  private estimateTimeToFailure(
    timeSeries: TimeSeriesDataPoint[],
    threshold: number
  ): number | null {
    for (let i = 0; i < timeSeries.length; i++) {
      if (timeSeries[i].value < threshold) {
        const now = Date.now();
        const failureTime = new Date(timeSeries[i].timestamp).getTime();
        return Math.round((failureTime - now) / (1000 * 60 * 60 * 24));
      }
    }
    return null;
  }

  private emptyStatistics(): SimulationStatistics {
    return {
      meanComplianceRate: 0,
      medianComplianceRate: 0,
      stdDevComplianceRate: 0,
      minComplianceRate: 0,
      maxComplianceRate: 0,
      probabilityOfFailure: 0,
      expectedTimeToFailure: null,
      valueAtRisk: 0,
    };
  }
}

// ---------------------------------------------------------------------------
// WhatIfAnalyzer
// ---------------------------------------------------------------------------

/**
 * Performs what-if analysis to evaluate hypothetical compliance scenarios
 * and their impact on the overall compliance posture.
 */
export class WhatIfAnalyzer {
  private twin: ComplianceDigitalTwin;
  private queries: Map<string, WhatIfQuery> = new Map();
  private results: Map<string, WhatIfResult> = new Map();

  constructor(twin: ComplianceDigitalTwin) {
    this.twin = twin;
  }

  createQuery(
    query: Omit<WhatIfQuery, "id"> & { id?: string }
  ): WhatIfQuery {
    const id = query.id ?? `wif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const full: WhatIfQuery = { ...query, id };
    this.queries.set(id, full);
    return full;
  }

  getQuery(id: string): WhatIfQuery | undefined {
    return this.queries.get(id);
  }

  analyze(queryId: string): WhatIfResult {
    const query = this.queries.get(queryId);
    if (!query) throw new Error(`What-if query "${queryId}" not found`);

    const twinState = this.twin.getTwin(query.twinId);
    if (!twinState) throw new Error(`Twin "${query.twinId}" not found`);

    const baselineSnapshot = this.createSnapshot(twinState, "baseline");
    const projectedSnapshot = this.applyHypothesis(twinState, query);

    const impactAnalysis = this.analyzeImpact(
      baselineSnapshot,
      projectedSnapshot,
      query
    );

    const cascadingEffects = query.parameters.includeCascadingEffects
      ? this.computeCascadingEffects(twinState, query)
      : [];

    const recommendations = this.generateRecommendations(
      impactAnalysis,
      cascadingEffects,
      query
    );

    const confidence = this.computeConfidence(twinState, query);

    const result: WhatIfResult = {
      id: `wifr-${queryId}-${Date.now()}`,
      queryId,
      hypothesis: query.hypothesis,
      baselineState: baselineSnapshot,
      projectedState: projectedSnapshot,
      impactAnalysis: {
        ...impactAnalysis,
        cascadingEffects,
      },
      recommendations,
      confidence,
      generatedAt: new Date().toISOString(),
    };

    this.results.set(result.id, result);

    this.twin["emit"]({
      type: "whatif_analyzed",
      twinId: query.twinId,
      timestamp: result.generatedAt,
      data: { queryId, resultId: result.id },
    });

    return result;
  }

  getResult(id: string): WhatIfResult | undefined {
    return this.results.get(id);
  }

  listResults(): WhatIfResult[] {
    return Array.from(this.results.values());
  }

  private createSnapshot(twinState: TwinState, label: string): TwinSnapshot {
    return {
      id: `snapshot-${label}-${Date.now()}`,
      twinId: twinState.id,
      timestamp: new Date().toISOString(),
      controls: new Map(twinState.controls),
      events: [...twinState.events],
      riskScores: new Map(twinState.riskScores),
      complianceRate: this.twin.calculateComplianceRate(twinState),
      metadata: { label },
    };
  }

  private applyHypothesis(
    twinState: TwinState,
    query: WhatIfQuery
  ): TwinSnapshot {
    const projected: TwinState = {
      ...twinState,
      controls: new Map(
        Array.from(twinState.controls.entries()).map(([k, v]) => [k, { ...v }])
      ),
      events: [...twinState.events],
      riskScores: new Map(
        Array.from(twinState.riskScores.entries()).map(([k, v]) => [k, { ...v }])
      ),
      snapshots: [],
    };

    for (const controlId of query.hypothesis.affectedControls) {
      const control = projected.controls.get(controlId);
      if (!control) continue;

      switch (query.hypothesis.type) {
        case "resource_allocation":
          if (query.hypothesis.resourceDelta) {
            const improvement = this.estimateResourceImpact(
              query.hypothesis.resourceDelta
            );
            const score = projected.riskScores.get(controlId);
            if (score) {
              projected.riskScores.set(controlId, {
                ...score,
                score: Math.max(0, score.score - improvement),
                updatedAt: new Date().toISOString(),
              });
            }
          }
          break;

        case "control_upgrade":
          control.status = "compliant";
          control.lastAssessedAt = new Date().toISOString();
          const upgradeScore = projected.riskScores.get(controlId);
          if (upgradeScore) {
            projected.riskScores.set(controlId, {
              ...upgradeScore,
              score: Math.max(0, upgradeScore.score - 0.3),
              updatedAt: new Date().toISOString(),
            });
          }
          break;

        case "policy_change":
          if (query.hypothesis.policyChanges) {
            const policyImpact = this.estimatePolicyImpact(
              query.hypothesis.policyChanges
            );
            const polScore = projected.riskScores.get(controlId);
            if (polScore) {
              projected.riskScores.set(controlId, {
                ...polScore,
                score: Math.max(0, polScore.score - policyImpact),
                updatedAt: new Date().toISOString(),
              });
            }
          }
          break;

        case "framework_adoption":
          control.status = "at_risk";
          break;

        case "incident_response":
          control.status = "at_risk";
          const incScore = projected.riskScores.get(controlId);
          if (incScore) {
            projected.riskScores.set(controlId, {
              ...incScore,
              score: Math.min(1, incScore.score + 0.2),
              updatedAt: new Date().toISOString(),
            });
          }
          break;
      }
    }

    return {
      id: `snapshot-projected-${Date.now()}`,
      twinId: twinState.id,
      timestamp: new Date().toISOString(),
      controls: projected.controls,
      events: projected.events,
      riskScores: projected.riskScores,
      complianceRate: this.twin.calculateComplianceRate(projected),
      metadata: { label: "projected" },
    };
  }

  private estimateResourceImpact(delta: ResourceDelta): number {
    let impact = 0;
    if (delta.budgetChange > 0) impact += Math.min(0.2, delta.budgetChange / 100000);
    if (delta.staffingChange > 0) impact += Math.min(0.15, delta.staffingChange * 0.05);
    impact += Math.min(0.1, delta.toolingChange.length * 0.03);
    return impact;
  }

  private estimatePolicyImpact(changes: PolicyChange[]): number {
    return Math.min(0.25, changes.length * 0.08);
  }

  private analyzeImpact(
    baseline: TwinSnapshot,
    projected: TwinSnapshot,
    query: WhatIfQuery
  ): Omit<WhatIfImpactAnalysis, "cascadingEffects"> {
    const overallScoreChange = this.computeAverageRiskDelta(
      baseline.riskScores,
      projected.riskScores
    );

    const complianceRateChange = projected.complianceRate - baseline.complianceRate;

    const riskReduction = Math.max(0, -overallScoreChange);

    const affectedControls: WhatIfControlImpact[] = [];
    for (const controlId of query.hypothesis.affectedControls) {
      const before = baseline.riskScores.get(controlId)?.score ?? 0.5;
      const after = projected.riskScores.get(controlId)?.score ?? 0.5;
      affectedControls.push({
        controlId,
        currentRisk: before,
        projectedRisk: after,
        riskDelta: after - before,
        confidence: 0.8,
      });
    }

    const timeToImpact = this.estimateTimeToImpact(query.hypothesis.type);

    return {
      overallScoreChange,
      complianceRateChange,
      riskReduction,
      affectedControls,
      timeToImpact,
    };
  }

  private computeAverageRiskDelta(
    baseline: Map<string, RiskScore>,
    projected: Map<string, RiskScore>
  ): number {
    let totalDelta = 0;
    let count = 0;

    for (const [controlId, baseScore] of baseline) {
      const projScore = projected.get(controlId);
      if (projScore) {
        totalDelta += projScore.score - baseScore.score;
        count++;
      }
    }

    return count > 0 ? totalDelta / count : 0;
  }

  private computeCascadingEffects(
    twinState: TwinState,
    query: WhatIfQuery
  ): CascadingEffect[] {
    const effects: CascadingEffect[] = [];
    const visited = new Set<string>();

    const traverse = (controlId: string, depth: number): void => {
      if (depth >= query.parameters.maxCascadingDepth) return;
      if (visited.has(controlId)) return;
      visited.add(controlId);

      for (const [otherId, otherControl] of twinState.controls) {
        if (otherId === controlId) continue;
        if (visited.has(otherId)) continue;

        const sharedFrameworks = otherControl.frameworkId === twinState.controls.get(controlId)?.frameworkId;
        const sharedTags = otherControl.tags.some((t) =>
          twinState.controls.get(controlId)?.tags.includes(t)
        );

        if (sharedFrameworks || sharedTags) {
          const sourceScore = twinState.riskScores.get(controlId)?.score ?? 0.5;
          const targetScore = twinState.riskScores.get(otherId)?.score ?? 0.5;
          const magnitude = Math.abs(sourceScore - targetScore) * 0.3;

          if (magnitude > 0.05) {
            effects.push({
              sourceControlId: controlId,
              targetControlId: otherId,
              effectType: sharedFrameworks ? "dependency_enhancement" : "shared_failure",
              magnitude,
              description: sharedFrameworks
                ? `Framework dependency propagates risk from ${controlId} to ${otherId}`
                : `Shared tag dependency between ${controlId} and ${otherId}`,
            });
          }

          traverse(otherId, depth + 1);
        }
      }
    };

    for (const controlId of query.hypothesis.affectedControls) {
      traverse(controlId, 0);
    }

    return effects;
  }

  private estimateTimeToImpact(
    hypothesisType: WhatIfHypothesis["type"]
  ): number {
    switch (hypothesisType) {
      case "resource_allocation": return 30;
      case "control_upgrade": return 14;
      case "policy_change": return 45;
      case "framework_adoption": return 60;
      case "incident_response": return 7;
      default: return 30;
    }
  }

  private generateRecommendations(
    impact: Omit<WhatIfImpactAnalysis, "cascadingEffects">,
    cascadingEffects: CascadingEffect[],
    query: WhatIfQuery
  ): WhatIfRecommendation[] {
    const recs: WhatIfRecommendation[] = [];

    if (impact.riskReduction < 0.1) {
      recs.push({
        id: `rec-${query.id}-low-impact`,
        priority: "medium",
        title: "Consider alternative approach",
        description:
          "The projected risk reduction is below 10%. Consider combining multiple changes or prioritizing high-impact controls.",
        estimatedImpact: impact.riskReduction,
        estimatedEffort: 5,
        prerequisites: [],
      });
    }

    if (cascadingEffects.length > 3) {
      recs.push({
        id: `rec-${query.id}-cascade`,
        priority: "high",
        title: "Address cascading dependencies",
        description:
          `${cascadingEffects.length} cascading effects detected. Implement changes in phases to manage propagation risk.`,
        estimatedImpact: 0.2,
        estimatedEffort: 8,
        prerequisites: [],
      });
    }

    if (impact.complianceRateChange > 0.1) {
      recs.push({
        id: `rec-${query.id}-compliance-boost`,
        priority: "low",
        title: "Validate compliance improvement",
        description:
          `Projected compliance rate improvement of ${(impact.complianceRateChange * 100).toFixed(1)}%. Validate with actual assessments.`,
        estimatedImpact: impact.complianceRateChange,
        estimatedEffort: 2,
        prerequisites: [],
      });
    }

    if (recs.length === 0) {
      recs.push({
        id: `rec-${query.id}-default`,
        priority: "low",
        title: "Proceed with implementation",
        description:
          "The what-if analysis shows acceptable impact. Proceed with the proposed changes.",
        estimatedImpact: impact.riskReduction,
        estimatedEffort: 3,
        prerequisites: [],
      });
    }

    return recs;
  }

  private computeConfidence(twinState: TwinState, query: WhatIfQuery): number {
    let confidence = 0.7;

    if (twinState.events.length > 100) confidence += 0.1;
    else if (twinState.events.length > 50) confidence += 0.05;

    if (twinState.snapshots.length > 5) confidence += 0.1;

    if (query.hypothesis.affectedControls.length > 0) {
      const allHaveScores = query.hypothesis.affectedControls.every((c) =>
        twinState.riskScores.has(c)
      );
      if (allHaveScores) confidence += 0.05;
    }

    return Math.min(0.95, confidence);
  }
}

// ---------------------------------------------------------------------------
// ComplianceForecaster
// ---------------------------------------------------------------------------

/**
 * Generates compliance forecasts based on historical data, trends, and
 * current state of the digital twin.
 */
export class ComplianceForecaster {
  private twin: ComplianceDigitalTwin;
  private forecasts: Map<string, ComplianceForecast[]> = new Map();

  constructor(twin: ComplianceDigitalTwin) {
    this.twin = twin;
  }

  generateForecast(request: ForecastRequest): ComplianceForecast[] {
    const twinState = this.twin.getTwin(request.twinId);
    if (!twinState) throw new Error(`Twin "${request.twinId}" not found`);

    const results: ComplianceForecast[] = [];
    const controlIds = request.controlIds.length > 0
      ? request.controlIds
      : Array.from(twinState.controls.keys());

    for (const controlId of controlIds) {
      const forecast = this.forecastControl(
        twinState,
        controlId,
        request.horizonDays,
        request.confidenceLevel,
        request.includeSeasonality
      );
      if (forecast) {
        results.push(forecast);
      }
    }

    this.forecasts.set(request.twinId, results);

    this.twin["emit"]({
      type: "forecast_generated",
      twinId: request.twinId,
      timestamp: new Date().toISOString(),
      data: { controlCount: results.length, horizonDays: request.horizonDays },
    });

    return results;
  }

  getForecasts(twinId: string): ComplianceForecast[] {
    return this.forecasts.get(twinId) ?? [];
  }

  private forecastControl(
    twinState: TwinState,
    controlId: string,
    horizonDays: number,
    confidenceLevel: number,
    includeSeasonality: boolean
  ): ComplianceForecast | null {
    const control = twinState.controls.get(controlId);
    if (!control) return null;

    const events = twinState.events.filter((e) => e.controlId === controlId);
    const riskScore = twinState.riskScores.get(controlId);

    const historicalRate = this.computeHistoricalRate(events);
    const trendSlope = this.computeTrendSlope(events);
    const seasonality = includeSeasonality ? this.detectSeasonality(events) : null;

    const predictions = this.generatePredictions(
      historicalRate,
      trendSlope,
      seasonality,
      horizonDays,
      confidenceLevel
    );

    const riskRating = this.determineRiskRating(riskScore);
    const actions = this.generateActions(control, riskScore, predictions);

    const forecast: ComplianceForecast = {
      controlId,
      forecastDate: new Date().toISOString(),
      predictions,
      confidenceLevel,
      riskRating,
      recommendedActions: actions,
    };

    return forecast;
  }

  private computeHistoricalRate(events: ComplianceEvent[]): number {
    if (events.length === 0) return 0.5;

    const compliant = events.filter((e) => e.status === "compliant").length;
    return compliant / events.length;
  }

  private computeTrendSlope(events: ComplianceEvent[]): number {
    if (events.length < 3) return 0;

    const sorted = [...events].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const values = sorted.map((e) =>
      e.status === "compliant" ? 1 : e.status === "non_compliant" ? 0 : 0.5
    );

    const n = values.length;
    const xMean = (n - 1) / 2;
    const yMean = (values as number[]).reduce((a, b) => a + b, 0) / n;

    let numerator = 0;
    let denominator = 0;
    for (let i = 0; i < n; i++) {
      numerator += (i - xMean) * (values[i] - yMean);
      denominator += (i - xMean) * (i - xMean);
    }

    return denominator !== 0 ? numerator / denominator / n : 0;
  }

  private detectSeasonality(
    events: ComplianceEvent[]
  ): { period: number; amplitude: number } | null {
    if (events.length < 14) return null;

    const sorted = [...events].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
    const values = sorted.map((e) =>
      e.status === "compliant" ? 1 : e.status === "non_compliant" ? 0 : 0.5
    );

    const n = values.length;
    const mean = (values as number[]).reduce((a, b) => a + b, 0) / n;
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
    return { period: bestPeriod, amplitude: Math.abs(bestCorrelation) };
  }

  private generatePredictions(
    baseRate: number,
    trendSlope: number,
    seasonality: { period: number; amplitude: number } | null,
    horizonDays: number,
    confidenceLevel: number
  ): ForecastPoint[] {
    const points: ForecastPoint[] = [];
    const now = new Date();
    const zScore = confidenceLevel >= 0.99 ? 2.576 : confidenceLevel >= 0.95 ? 1.96 : 1.645;

    for (let d = 0; d <= horizonDays; d += 7) {
      const date = new Date(now);
      date.setDate(date.getDate() + d);

      let rate = baseRate + trendSlope * d;

      if (seasonality) {
        rate +=
          seasonality.amplitude *
          Math.sin((2 * Math.PI * d) / seasonality.period);
      }

      rate = Math.max(0, Math.min(1, rate));

      const uncertainty = (d / horizonDays) * 0.2;
      const lowerBound = Math.max(0, rate - zScore * uncertainty);
      const upperBound = Math.min(1, rate + zScore * uncertainty);

      let status: ComplianceStatus;
      if (rate > 0.7) status = "compliant";
      else if (rate > 0.4) status = "at_risk";
      else status = "non_compliant";

      points.push({
        timestamp: date.toISOString(),
        predictedStatus: status,
        probability: rate,
        lowerBound,
        upperBound,
      });
    }

    return points;
  }

  private determineRiskRating(riskScore: RiskScore | undefined): SeverityLevel {
    if (!riskScore) return "low";
    if (riskScore.score >= 0.8) return "critical";
    if (riskScore.score >= 0.6) return "high";
    if (riskScore.score >= 0.4) return "medium";
    if (riskScore.score >= 0.2) return "low";
    return "informational";
  }

  private generateActions(
    control: Control,
    riskScore: RiskScore | undefined,
    predictions: ForecastPoint[]
  ): ForecastAction[] {
    const actions: ForecastAction[] = [];

    if (riskScore && riskScore.score > 0.5) {
      actions.push({
        id: `fa-${control.id}-risk`,
        title: `Address elevated risk for ${control.name}`,
        description: `Risk score is ${(riskScore.score * 100).toFixed(0)}%. Implement controls to reduce risk.`,
        priority: riskScore.score > 0.7 ? "critical" : "high",
        estimatedImpact: 0.3,
        deadline: new Date(Date.now() + 14 * 86400000).toISOString(),
      });
    }

    const failurePoints = predictions.filter(
      (p) => p.predictedStatus === "non_compliant"
    );
    if (failurePoints.length > 0) {
      actions.push({
        id: `fa-${control.id}-predict`,
        title: `Prevent predicted non-compliance for ${control.name}`,
        description: `${failurePoints.length} non-compliant periods predicted. Take preventive action.`,
        priority: "medium",
        estimatedImpact: 0.2,
        deadline: new Date(Date.now() + 30 * 86400000).toISOString(),
      });
    }

    return actions;
  }
}

// ---------------------------------------------------------------------------
// TwinSynchronizer
// ---------------------------------------------------------------------------

/**
 * Manages real-time synchronization between the digital twin and the actual
 * compliance state. Handles incremental updates, drift detection, and
 * health monitoring.
 */
export class TwinSynchronizer {
  private twin: ComplianceDigitalTwin;
  private syncCallbacks: Map<string, () => Promise<SyncChange[]>> = new Map();
  private checkpoints: Map<string, SyncCheckpoint[]> = new Map();
  private healthReports: Map<string, SyncHealthReport> = new Map();
  private syncIntervals: Map<string, ReturnType<typeof setInterval>> = new Map();

  constructor(twin: ComplianceDigitalTwin) {
    this.twin = twin;
  }

  registerDataSource(
    twinId: string,
    fetchFn: () => Promise<SyncChange[]>
  ): void {
    this.syncCallbacks.set(twinId, fetchFn);
  }

  startAutoSync(twinId: string): void {
    const twin = this.twin.getTwin(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    if (this.syncIntervals.has(twinId)) {
      this.stopAutoSync(twinId);
    }

    const interval = setInterval(async () => {
      try {
        await this.sync(twinId);
      } catch {
        this.updateHealth(twinId, "degraded");
      }
    }, twin.config.syncIntervalMs);

    this.syncIntervals.set(twinId, interval);
  }

  stopAutoSync(twinId: string): void {
    const interval = this.syncIntervals.get(twinId);
    if (interval) {
      clearInterval(interval);
      this.syncIntervals.delete(twinId);
    }
  }

  async sync(twinId: string): Promise<SyncCheckpoint> {
    const twin = this.twin.getTwin(twinId);
    if (!twin) throw new Error(`Twin "${twinId}" not found`);

    const fetchFn = this.syncCallbacks.get(twinId);
    if (!fetchFn) throw new Error(`No data source registered for twin "${twinId}"`);

    const startTime = Date.now();
    const changes: SyncChange[] = [];

    try {
      const fetchedChanges = await fetchFn();
      changes.push(...fetchedChanges);

      this.applyChanges(twin, changes);
      twin.lastSyncedAt = new Date().toISOString();
      twin.version++;

      const checkpoint: SyncCheckpoint = {
        id: `chk-${twinId}-${Date.now()}`,
        twinId,
        timestamp: new Date().toISOString(),
        version: twin.version,
        changesApplied: changes,
        durationMs: Date.now() - startTime,
      };

      const twinCheckpoints = this.checkpoints.get(twinId) ?? [];
      twinCheckpoints.push(checkpoint);
      if (twinCheckpoints.length > 50) twinCheckpoints.shift();
      this.checkpoints.set(twinId, twinCheckpoints);

      this.updateHealth(twinId, "healthy");

      this.twin["emit"]({
        type: "sync_completed",
        twinId,
        timestamp: checkpoint.timestamp,
        data: {
          changesCount: changes.length,
          durationMs: checkpoint.durationMs,
        },
      });

      return checkpoint;
    } catch (err) {
      this.updateHealth(twinId, "disconnected");

      this.twin["emit"]({
        type: "sync_failed",
        twinId,
        timestamp: new Date().toISOString(),
        data: { error: err instanceof Error ? err.message : "Unknown error" },
      });

      throw err;
    }
  }

  getCheckpoints(twinId: string): SyncCheckpoint[] {
    return this.checkpoints.get(twinId) ?? [];
  }

  getHealthReport(twinId: string): SyncHealthReport {
    return (
      this.healthReports.get(twinId) ?? {
        twinId,
        status: "disconnected",
        lastSyncAt: null,
        syncLatencyMs: 0,
        dataFreshnessMs: 0,
        driftScore: 0,
        issues: [],
      }
    );
  }

  private applyChanges(twin: TwinState, changes: SyncChange[]): void {
    for (const change of changes) {
      switch (change.entityType) {
        case "control": {
          if (change.action === "deleted") {
            twin.controls.delete(change.entityId);
          } else if (change.newValue) {
            twin.controls.set(change.entityId, change.newValue as Control);
          }
          break;
        }
        case "event": {
          if (change.newValue) {
            twin.events.push(change.newValue as ComplianceEvent);
          }
          break;
        }
        case "risk_score": {
          if (change.action === "deleted") {
            twin.riskScores.delete(change.entityId);
          } else if (change.newValue) {
            const score = change.newValue as RiskScore;
            twin.riskScores.set(score.controlId, score);
          }
          break;
        }
      }
    }
  }

  private updateHealth(
    twinId: string,
    status: TwinHealthStatus
  ): void {
    const twin = this.twin.getTwin(twinId);
    const existing = this.healthReports.get(twinId);

    const lastSyncAt = twin?.lastSyncedAt ?? existing?.lastSyncAt ?? null;
    const dataFreshnessMs = lastSyncAt
      ? Date.now() - new Date(lastSyncAt).getTime()
      : Infinity;

    let issues: SyncIssue[] = existing?.issues ?? [];

    if (dataFreshnessMs > 3600000) {
      issues = [
        ...issues.filter((i) => i.type !== "stale_data"),
        {
          type: "stale_data",
          severity: "medium",
          message: `Data is stale by ${Math.round(dataFreshnessMs / 60000)} minutes`,
          detectedAt: new Date().toISOString(),
          resolvedAt: null,
        },
      ];
    } else {
      issues = issues.filter((i) => i.type !== "stale_data");
    }

    if (status === "disconnected") {
      issues = [
        ...issues.filter((i) => i.type !== "sync_failure"),
        {
          type: "sync_failure",
          severity: "high",
          message: "Sync connection lost",
          detectedAt: new Date().toISOString(),
          resolvedAt: null,
        },
      ];
    } else {
      issues = issues.filter((i) => i.type !== "sync_failure");
    }

    const driftScore = twin ? this.calculateDriftScore(twin) : 0;

    const report: SyncHealthReport = {
      twinId,
      status,
      lastSyncAt,
      syncLatencyMs: existing?.syncLatencyMs ?? 0,
      dataFreshnessMs,
      driftScore,
      issues,
    };

    this.healthReports.set(twinId, report);

    if (existing && existing.status !== status) {
      this.twin["emit"]({
        type: "health_changed",
        twinId,
        timestamp: new Date().toISOString(),
        data: { previousStatus: existing.status, newStatus: status },
      });
    }
  }

  private calculateDriftScore(twin: TwinState): number {
    if (twin.snapshots.length < 2) return 0;

    const latest = twin.snapshots[twin.snapshots.length - 1];
    const previous = twin.snapshots[twin.snapshots.length - 2];

    const rateDiff = Math.abs(latest.complianceRate - previous.complianceRate);

    let controlChanges = 0;
    for (const [id, ctrl] of latest.controls) {
      const prevCtrl = previous.controls.get(id);
      if (prevCtrl && prevCtrl.status !== ctrl.status) {
        controlChanges++;
      }
    }

    const normalizedChanges = twin.controls.size > 0
      ? controlChanges / twin.controls.size
      : 0;

    return Math.min(1, rateDiff + normalizedChanges);
  }
}
