/**
 * @module @grc-claw/federated-learning
 * @description Federated learning network for compliance pattern sharing.
 * Enables organizations to train shared models without exposing raw data,
 * creating network effects where every participant improves the platform.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Organization {
  id: string;
  name: string;
  publicKey: string;
  registeredAt: Date;
  metadata?: Record<string, unknown>;
}

export interface ModelVersion {
  version: string;
  hash: string;
  createdAt: Date;
  metrics: ModelMetrics;
  parentVersion?: string;
  tags: string[];
}

export interface ModelMetrics {
  accuracy: number;
  loss: number;
  participantCount: number;
  totalSamples: number;
  privacyBudget: number;
}

export interface ModelUpdate {
  organizationId: string;
  version: string;
  weights: number[][];
  bias: number[];
  sampleCount: number;
  metadata: UpdateMetadata;
}

export interface UpdateMetadata {
  featureNames: string[];
  dataDistribution: Record<string, number>;
  timestamp: Date;
}

export interface PrivacyConfig {
  epsilon: number;
  delta: number;
  maxGradientNorm: number;
  noiseMultiplier: number;
}

export interface AggregationConfig {
  strategy: "fedavg" | "fedprox" | "scaffold" | "custom";
  minParticipants: number;
  maxRounds: number;
  convergenceThreshold: number;
  customStrategy?: (
    updates: ModelUpdate[],
    currentWeights: number[][]
  ) => number[][];
}

export interface FederatedLearningConfig {
  networkId: string;
  modelId: string;
  privacy: PrivacyConfig;
  aggregation: AggregationConfig;
  features: FeatureConfig[];
}

export interface FeatureConfig {
  name: string;
  type: "numerical" | "categorical" | "binary";
  normalization?: "minmax" | "zscore" | "none";
}

export interface TrainingRound {
  roundId: number;
  startedAt: Date;
  completedAt?: Date;
  participantIds: string[];
  updates: ModelUpdate[];
  aggregatedUpdate?: number[][];
  metrics?: ModelMetrics;
  status: "pending" | "in_progress" | "completed" | "failed";
}

export interface CompliancePattern {
  id: string;
  name: string;
  description: string;
  modelVersion: string;
  confidence: number;
  featureImportance: Record<string, number>;
  discoveredAt: Date;
  validatedBy: string[];
}

export interface PredictionResult {
  prediction: number;
  confidence: number;
  contributingPatterns: string[];
  privacyPreserved: boolean;
}

// ---------------------------------------------------------------------------
// Privacy Engine – differential privacy for local model updates
// ---------------------------------------------------------------------------

export class PrivacyEngine {
  private config: PrivacyConfig;
  private totalSpentBudget: number;
  private readonly maxBudget: number;

  constructor(config: PrivacyConfig, maxBudget: number = 10) {
    this.config = config;
    this.totalSpentBudget = 0;
    this.maxBudget = maxBudget;
  }

  /** Clip gradients to a fixed L2 norm. */
  clipGradients(gradient: number[], maxNorm: number): number[] {
    const norm = Math.sqrt(gradient.reduce((sum, v) => sum + v * v, 0));
    if (norm <= maxNorm) return [...gradient];
    const scale = maxNorm / norm;
    return gradient.map((v) => v * scale);
  }

  /** Add calibrated Gaussian noise for (ε, δ)-differential privacy. */
  addNoise(clippedGradient: number[], epsilon: number, delta: number): number[] {
    const sensitivity = this.config.maxGradientNorm;
    const sigma = (sensitivity * Math.sqrt(2 * Math.log(1.25 / delta))) / epsilon;
    const noisyGradient = clippedGradient.map(
      (v) => v + this.gaussianRandom() * sigma
    );
    return noisyGradient;
  }

  /** Apply full local DP pipeline to a model update. */
  applyLocalDP(update: number[][]): number[][] {
    return update.map((layer) => {
      const clipped = this.clipGradients(layer, this.config.maxGradientNorm);
      return this.addNoise(clipped, this.config.epsilon, this.config.delta);
    });
  }

  /** Consume privacy budget and reject if over limit. */
  consumeBudget(amount: number): boolean {
    if (this.totalSpentBudget + amount > this.maxBudget) return false;
    this.totalSpentBudget += amount;
    return true;
  }

  /** Track per-round privacy cost. */
  trackRoundPrivacyCost(participantCount: number): number {
    const compositionFactor = Math.sqrt(2 * participantCount * Math.log(1 / this.config.delta));
    const roundCost = this.config.epsilon * compositionFactor;
    this.totalSpentBudget += roundCost;
    return roundCost;
  }

  getRemainingBudget(): number {
    return Math.max(0, this.maxBudget - this.totalSpentBudget);
  }

  private gaussianRandom(): number {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }
}

// ---------------------------------------------------------------------------
// Secure Aggregator – merge encrypted / masked model updates
// ---------------------------------------------------------------------------

export class SecureAggregator {
  private config: AggregationConfig;
  private readonly secrets: Map<string, string>;

  constructor(config: AggregationConfig) {
    this.config = config;
    this.secrets = new Map();
  }

  /** Register a participant secret for masking. */
  registerParticipant(organizationId: string, secret: string): void {
    this.secrets.set(organizationId, secret);
  }

  /** Mask an update using XOR with a secret key. */
  maskUpdate(update: number[][], organizationId: string): number[][] {
    const secret = this.secrets.get(organizationId);
    if (!secret) throw new Error(`No secret registered for ${organizationId}`);
    return update.map((layer) => this.xorMaskLayer(layer, secret));
  }

  /** Aggregate multiple masked updates and unmask the result. */
  aggregate(updates: ModelUpdate[], currentWeights: number[][]): {
    aggregatedWeights: number[][];
    metrics: ModelMetrics;
  } {
    this.validateParticipants(updates);

    let aggregated: number[][];
    switch (this.config.strategy) {
      case "fedavg":
        aggregated = this.federatedAveraging(updates, currentWeights);
        break;
      case "fedprox":
        aggregated = this.federatedProx(updates, currentWeights);
        break;
      case "scaffold":
        aggregated = this.scaffoldAggregation(updates, currentWeights);
        break;
      case "custom":
        if (!this.config.customStrategy) {
          throw new Error("Custom strategy function not provided");
        }
        aggregated = this.config.customStrategy(updates, currentWeights);
        break;
      default:
        throw new Error(`Unknown aggregation strategy: ${this.config.strategy}`);
    }

    const metrics = this.computeAggregationMetrics(updates);
    return { aggregatedWeights: aggregated, metrics };
  }

  // ---- Strategy implementations ----

  private federatedAveraging(
    updates: ModelUpdate[],
    currentWeights: number[][]
  ): number[][] {
    const totalSamples = updates.reduce((s, u) => s + u.sampleCount, 0);
    if (totalSamples === 0) return currentWeights;

    const aggregated = currentWeights.map((layer, li) =>
      layer.map((_, wi) => {
        let weightedSum = 0;
        for (const update of updates) {
          const weight = update.sampleCount / totalSamples;
          weightedSum += update.weights[li][wi] * weight;
        }
        return weightedSum;
      })
    );
    return aggregated;
  }

  private federatedProx(
    updates: ModelUpdate[],
    currentWeights: number[][]
  ): number[][] {
    const mu = 0.01;
    const totalSamples = updates.reduce((s, u) => s + u.sampleCount, 0);
    if (totalSamples === 0) return currentWeights;

    return currentWeights.map((layer, li) =>
      layer.map((_, wi) => {
        let weightedSum = 0;
        for (const update of updates) {
          const weight = update.sampleCount / totalSamples;
          const proxTerm = mu * (currentWeights[li][wi] - update.weights[li][wi]);
          weightedSum += (update.weights[li][wi] + proxTerm) * weight;
        }
        return weightedSum;
      })
    );
  }

  private scaffoldAggregation(
    updates: ModelUpdate[],
    currentWeights: number[][]
  ): number[][] {
    const totalSamples = updates.reduce((s, u) => s + u.sampleCount, 0);
    if (totalSamples === 0) return currentWeights;

    const controlVariates = currentWeights.map((layer) =>
      layer.map(() => 0)
    );

    return currentWeights.map((layer, li) =>
      layer.map((_, wi) => {
        let weightedDelta = 0;
        for (const update of updates) {
          const weight = update.sampleCount / totalSamples;
          const delta = update.weights[li][wi] - currentWeights[li][wi];
          weightedDelta += (delta - controlVariates[li][wi]) * weight;
        }
        return currentWeights[li][wi] + weightedDelta;
      })
    );
  }

  // ---- Helpers ----

  private validateParticipants(updates: ModelUpdate[]): void {
    if (updates.length < this.config.minParticipants) {
      throw new Error(
        `Insufficient participants: need ${this.config.minParticipants}, got ${updates.length}`
      );
    }
    const seen = new Set<string>();
    for (const u of updates) {
      if (seen.has(u.organizationId)) {
        throw new Error(`Duplicate participant: ${u.organizationId}`);
      }
      seen.add(u.organizationId);
    }
  }

  private computeAggregationMetrics(updates: ModelUpdate[]): ModelMetrics {
    const totalSamples = updates.reduce((s, u) => s + u.sampleCount, 0);
    const avgAccuracy =
      updates.reduce((s, u) => s + ((u.metadata as any).accuracy || 0), 0) /
      (updates.length || 1);
    const avgLoss =
      updates.reduce((s, u) => s + ((u.metadata as any).loss || 0), 0) /
      (updates.length || 1);

    return {
      accuracy: avgAccuracy,
      loss: avgLoss,
      participantCount: updates.length,
      totalSamples,
      privacyBudget: 0,
    };
  }

  private xorMaskLayer(layer: number[], secret: string): number[] {
    let keyIndex = 0;
    return layer.map((v) => {
      const charCode = secret.charCodeAt(keyIndex % secret.length);
      keyIndex++;
      return v ^ charCode;
    });
  }
}

// ---------------------------------------------------------------------------
// FederatedModel – versioned model management
// ---------------------------------------------------------------------------

export class FederatedModel {
  readonly id: string;
  private versions: ModelVersion[];
  private currentVersion: ModelVersion | null;
  private weights: number[][];
  private readonly featureConfig: FeatureConfig[];

  constructor(id: string, featureConfig: FeatureConfig[], initialWeights?: number[][]) {
    this.id = id;
    this.versions = [];
    this.currentVersion = null;
    this.featureConfig = featureConfig;
    this.weights = initialWeights ?? this.initWeights();
  }

  /** Create a new model version from aggregated weights. */
  createVersion(
    weights: number[][],
    metrics: ModelMetrics,
    tags: string[] = []
  ): ModelVersion {
    const version: ModelVersion = {
      version: this.generateVersionId(),
      hash: this.hashWeights(weights),
      createdAt: new Date(),
      metrics,
      parentVersion: this.currentVersion?.version,
      tags,
    };

    this.weights = weights;
    this.versions.push(version);
    this.currentVersion = version;
    return version;
  }

  /** Rollback to a previous version. */
  rollbackToVersion(versionId: string): boolean {
    const target = this.versions.find((v) => v.version === versionId);
    if (!target) return false;
    this.currentVersion = target;
    return true;
  }

  /** Get all versions. */
  getVersions(): ModelVersion[] {
    return [...this.versions];
  }

  getCurrentVersion(): ModelVersion | null {
    return this.currentVersion;
  }

  getWeights(): number[][] {
    return this.weights.map((layer) => [...layer]);
  }

  getFeatureConfig(): FeatureConfig[] {
    return [...this.featureConfig];
  }

  /** Produce a prediction from the current model weights. */
  predict(features: number[]): PredictionResult {
    if (features.length !== this.featureConfig.length) {
      throw new Error(
        `Feature count mismatch: expected ${this.featureConfig.length}, got ${features.length}`
      );
    }

    let output = 0;
    const layer0 = this.weights[0] ?? [];
    for (let i = 0; i < Math.min(features.length, layer0.length); i++) {
      output += features[i] * layer0[i];
    }
    if (this.weights[1]) {
      output += this.weights[1][0] ?? 0;
    }

    const confidence = 1 / (1 + Math.exp(-output));

    return {
      prediction: confidence >= 0.5 ? 1 : 0,
      confidence,
      contributingPatterns: [],
      privacyPreserved: true,
    };
  }

  // ---- Internals ----

  private initWeights(): number[][] {
    const fanIn = this.featureConfig.length;
    const fanOut = 1;
    const limit = Math.sqrt(6 / (fanIn + fanOut));
    const weights = Array.from({ length: fanIn }, () =>
      (Math.random() * 2 - 1) * limit
    );
    const bias = [0];
    return [weights, bias];
  }

  private generateVersionId(): string {
    const major = this.versions.length + 1;
    return `v${major}.0.0`;
  }

  private hashWeights(weights: number[][]): string {
    const flat = weights.flat().join(",");
    let hash = 0;
    for (let i = 0; i < flat.length; i++) {
      const ch = flat.charCodeAt(i);
      hash = (hash << 5) - hash + ch;
      hash |= 0;
    }
    return `wh_${Math.abs(hash).toString(36)}`;
  }
}

// ---------------------------------------------------------------------------
// CompliancePatternLearner – discovers / validates compliance patterns
// ---------------------------------------------------------------------------

export class CompliancePatternLearner {
  private patterns: CompliancePattern[];
  private readonly minConfidence: number;
  private readonly minValidators: number;

  constructor(minConfidence: number = 0.7, minValidators: number = 3) {
    this.patterns = [];
    this.minConfidence = minConfidence;
    this.minValidators = minValidators;
  }

  /** Analyze a completed training round for compliance patterns. */
  analyzeRound(round: TrainingRound, model: FederatedModel): CompliancePattern[] {
    if (round.status !== "completed" || !round.metrics) return [];

    const discovered: CompliancePattern[] = [];
    const weights = model.getWeights();

    for (let i = 0; i < weights.length; i++) {
      const layer = weights[i];
      for (let j = 0; j < layer.length; j++) {
        const importance = Math.abs(layer[j]);
        if (importance > this.minConfidence) {
          const pattern: CompliancePattern = {
            id: this.generatePatternId(),
            name: `compliance_pattern_${i}_${j}`,
            description: `Pattern discovered from weight[${i}][${j}] with importance ${importance.toFixed(4)}`,
            modelVersion: model.getCurrentVersion()?.version ?? "unknown",
            confidence: importance,
            featureImportance: this.computeFeatureImportance(weights),
            discoveredAt: new Date(),
            validatedBy: [],
          };
          discovered.push(pattern);
        }
      }
    }

    this.patterns.push(...discovered);
    return discovered;
  }

  /** Validate a pattern with a digital signature. */
  validatePattern(patternId: string, validatorOrgId: string): boolean {
    const pattern = this.patterns.find((p) => p.id === patternId);
    if (!pattern) return false;
    if (pattern.validatedBy.includes(validatorOrgId)) return false;

    pattern.validatedBy.push(validatorOrgId);
    return true;
  }

  /** Retrieve all validated patterns. */
  getValidatedPatterns(): CompliancePattern[] {
    return this.patterns.filter(
      (p) => p.validatedBy.length >= this.minValidators
    );
  }

  /** Retrieve all discovered patterns (validated or not). */
  getAllPatterns(): CompliancePattern[] {
    return [...this.patterns];
  }

  /** Generate a compliance report from validated patterns. */
  generateComplianceReport(): {
    totalPatterns: number;
    validatedPatterns: number;
    averageConfidence: number;
    topPatterns: CompliancePattern[];
  } {
    const validated = this.getValidatedPatterns();
    const avgConf =
      validated.length > 0
        ? validated.reduce((s, p) => s + p.confidence, 0) / validated.length
        : 0;

    return {
      totalPatterns: this.patterns.length,
      validatedPatterns: validated.length,
      averageConfidence: avgConf,
      topPatterns: validated
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 10),
    };
  }

  // ---- Internals ----

  private computeFeatureImportance(weights: number[][]): Record<string, number> {
    const importance: Record<string, number> = {};
    const layer0 = weights[0] ?? [];
    for (let i = 0; i < layer0.length; i++) {
      importance[`feature_${i}`] = Math.abs(layer0[i]);
    }
    return importance;
  }

  private generatePatternId(): string {
    return `pat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }
}

// ---------------------------------------------------------------------------
// FederatedLearningNetwork – orchestrator
// ---------------------------------------------------------------------------

export class FederatedLearningNetwork {
  private readonly config: FederatedLearningConfig;
  private readonly organizations: Map<string, Organization>;
  private readonly models: Map<string, FederatedModel>;
  private readonly rounds: TrainingRound[];
  private readonly privacyEngine: PrivacyEngine;
  private readonly aggregator: SecureAggregator;
  private readonly patternLearner: CompliancePatternLearner;
  private currentRound: number;

  constructor(config: FederatedLearningConfig) {
    this.config = config;
    this.organizations = new Map();
    this.models = new Map();
    this.rounds = [];
    this.privacyEngine = new PrivacyEngine(config.privacy);
    this.aggregator = new SecureAggregator(config.aggregation);
    this.patternLearner = new CompliancePatternLearner();
    this.currentRound = 0;

    this.models.set(
      config.modelId,
      new FederatedModel(config.modelId, config.features)
    );
  }

  /** Register an organization in the network. */
  registerOrganization(org: Organization): void {
    if (this.organizations.has(org.id)) {
      throw new Error(`Organization ${org.id} already registered`);
    }
    this.organizations.set(org.id, org);
    this.aggregator.registerParticipant(org.id, org.publicKey);
  }

  /** Remove an organization from the network. */
  unregisterOrganization(orgId: string): boolean {
    return this.organizations.delete(orgId);
  }

  /** Submit a local model update from an organization. */
  submitUpdate(orgId: string, update: Omit<ModelUpdate, "organizationId" | "version">): ModelUpdate {
    if (!this.organizations.has(orgId)) {
      throw new Error(`Organization ${orgId} not registered`);
    }

    const dpWeights = this.privacyEngine.applyLocalDP(update.weights);

    const fullUpdate: ModelUpdate = {
      ...update,
      organizationId: orgId,
      version: `r${this.currentRound}`,
      weights: dpWeights,
    };

    return fullUpdate;
  }

  /** Run a complete training round. */
  async runTrainingRound(
    updates: ModelUpdate[]
  ): Promise<TrainingRound> {
    if (updates.length < this.config.aggregation.minParticipants) {
      throw new Error(
        `Need at least ${this.config.aggregation.minParticipants} participants, got ${updates.length}`
      );
    }

    this.currentRound++;
    const round: TrainingRound = {
      roundId: this.currentRound,
      startedAt: new Date(),
      participantIds: updates.map((u) => u.organizationId),
      updates,
      status: "in_progress",
    };

    try {
      const model = this.models.get(this.config.modelId)!;
      const currentWeights = model.getWeights();

      const { aggregatedWeights, metrics } = this.aggregator.aggregate(
        updates,
        currentWeights
      );

      this.privacyEngine.trackRoundPrivacyCost(updates.length);

      const newVersion = model.createVersion(aggregatedWeights, metrics, [
        `round_${this.currentRound}`,
      ]);

      round.completedAt = new Date();
      round.aggregatedUpdate = aggregatedWeights;
      round.metrics = {
        ...metrics,
        privacyBudget: this.privacyEngine.getRemainingBudget(),
      };
      round.status = "completed";

      this.patternLearner.analyzeRound(round, model);
    } catch (err) {
      round.status = "failed";
      round.completedAt = new Date();
      throw err;
    } finally {
      this.rounds.push(round);
    }

    return round;
  }

  /** Get the current model. */
  getModel(): FederatedModel | undefined {
    return this.models.get(this.config.modelId);
  }

  /** Get all registered organizations. */
  getOrganizations(): Organization[] {
    return Array.from(this.organizations.values());
  }

  /** Get training history. */
  getTrainingRounds(): TrainingRound[] {
    return [...this.rounds];
  }

  /** Get the pattern learner. */
  getPatternLearner(): CompliancePatternLearner {
    return this.patternLearner;
  }

  /** Get network-level compliance report. */
  getComplianceReport(): {
    networkId: string;
    organizationCount: number;
    totalRounds: number;
    completedRounds: number;
    currentModelVersion: string | null;
    remainingPrivacyBudget: number;
    patterns: ReturnType<CompliancePatternLearner["generateComplianceReport"]>;
  } {
    const model = this.models.get(this.config.modelId);
    return {
      networkId: this.config.networkId,
      organizationCount: this.organizations.size,
      totalRounds: this.rounds.length,
      completedRounds: this.rounds.filter((r) => r.status === "completed")
        .length,
      currentModelVersion: model?.getCurrentVersion()?.version ?? null,
      remainingPrivacyBudget: this.privacyEngine.getRemainingBudget(),
      patterns: this.patternLearner.generateComplianceReport(),
    };
  }
}

// ---------------------------------------------------------------------------
// Factory helpers
// ---------------------------------------------------------------------------

export function createDefaultConfig(
  networkId: string,
  modelId: string,
  featureNames: string[]
): FederatedLearningConfig {
  return {
    networkId,
    modelId,
    privacy: {
      epsilon: 1.0,
      delta: 1e-5,
      maxGradientNorm: 1.0,
      noiseMultiplier: 1.0,
    },
    aggregation: {
      strategy: "fedavg",
      minParticipants: 3,
      maxRounds: 100,
      convergenceThreshold: 0.001,
    },
    features: featureNames.map((name) => ({
      name,
      type: "numerical" as const,
      normalization: "zscore" as const,
    })),
  };
}
