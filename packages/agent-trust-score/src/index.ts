import type { FrameworkCode } from "./types.js";
import type {
  AgentTrustProfile,
  TrustScoreDimensions,
  TrustScoreConfig,
  BehavioralSignal,
  RiskFactor,
  TrustCredential,
  TrustScoreEntry,
  AgentStatus,
  TrustScore,
} from "./types.js";
import { TrustScoreCalculator } from "./scoring/TrustScoreCalculator.js";
import { BehavioralAnalyzer, type BehavioralPattern } from "./scoring/BehavioralAnalyzer.js";
import { TrustCredentialIssuer, type CredentialStore } from "./credentials/TrustCredentialIssuer.js";

export interface AgentTrustScoreConfig extends Partial<TrustScoreConfig> {
  issuerId: string;
  credentialStore: CredentialStore;
  behavioralPatterns?: BehavioralPattern[];
}

export class AgentTrustScoreEngine {
  private calculator: TrustScoreCalculator;
  private behavioralAnalyzer: BehavioralAnalyzer;
  private credentialIssuer: TrustCredentialIssuer;
  private profiles: Map<string, AgentTrustProfile> = new Map();
  private config: { issuerId: string };

  constructor(config: AgentTrustScoreConfig) {
    this.config = { issuerId: config.issuerId };
    this.calculator = new TrustScoreCalculator(config);
    this.behavioralAnalyzer = new BehavioralAnalyzer(config.behavioralPatterns);
    this.credentialIssuer = new TrustCredentialIssuer(config.credentialStore, config.issuerId);
  }

  async scoreAgent(
    agentDid: string,
    agentName: string,
    tenantId: string,
    signals: BehavioralSignal[],
    complianceScore: number = 70,
    frameworks: FrameworkCode[] = []
  ): Promise<AgentTrustProfile> {
    const dimensions: TrustScoreDimensions = {
      identity: this.calculator.calculateDimensionScore("identity", signals),
      capability: this.calculator.calculateDimensionScore("capability", signals),
      compliance: this.calculator.calculateDimensionScore("compliance", signals, complianceScore),
      behavior: this.calculator.calculateDimensionScore("behavior", signals),
      provenance: this.calculator.calculateDimensionScore("provenance", signals),
    };

    const overallScore = this.calculator.calculateOverallScore(dimensions) as TrustScore;
    const riskLevel = this.calculator.calculateRiskLevel(overallScore);
    const riskFactors = this.calculator.identifyRiskFactors(dimensions, signals);
    const behavioralAnalysis = this.behavioralAnalyzer.analyze(agentDid, signals);

    const credentialSummary = await this.credentialIssuer.getCredentialSummary(agentDid);

    const existingProfile = this.profiles.get(agentDid);
    const scoreHistory = existingProfile?.scoreHistory || [];

    scoreHistory.push({
      timestamp: new Date().toISOString(),
      score: overallScore,
      dimensions,
      trigger: "scheduled_scoring",
    });

    if (scoreHistory.length > 100) scoreHistory.shift();

    const profile: AgentTrustProfile = {
      agentDid,
      agentName,
      tenantId,
      status: this.determineStatus(overallScore, riskLevel),
      overallTrustScore: overallScore,
      dimensions,
      riskLevel,
      riskFactors,
      behavioralSignals: signals,
      compliancePosture: {
        frameworks,
        overallScore: complianceScore,
        controlScores: new Map(),
        lastAuditAt: new Date().toISOString(),
        openFindings: riskFactors.filter((f) => !f.mitigated).length,
      },
      credentialSummary,
      lastScoredAt: new Date().toISOString(),
      scoreHistory,
    };

    this.profiles.set(agentDid, profile);
    return profile;
  }

  async getAgentProfile(agentDid: string): Promise<AgentTrustProfile | undefined> {
    return this.profiles.get(agentDid);
  }

  async updateAgentSignals(agentDid: string, newSignals: BehavioralSignal[]): Promise<AgentTrustProfile | undefined> {
    const existing = this.profiles.get(agentDid);
    if (!existing) return undefined;

    const allSignals = [...existing.behavioralSignals, ...newSignals].slice(-100);
    return this.scoreAgent(
      agentDid,
      existing.agentName,
      existing.tenantId,
      allSignals,
      existing.compliancePosture.overallScore,
      existing.compliancePosture.frameworks
    );
  }

  async issueTrustCredential(agentDid: string, type: "identity" | "capability" | "compliance" | "behavior" | "composite"): Promise<TrustCredential> {
    const profile = this.profiles.get(agentDid);
    if (!profile) throw new Error("Agent not scored yet");

    switch (type) {
      case "identity":
        return this.credentialIssuer.issueIdentityCredential(agentDid, { agentName: profile.agentName });
      case "capability":
        return this.credentialIssuer.issueCapabilityCredential(agentDid, ["read", "write"], profile.compliancePosture.frameworks);
      case "compliance":
        return this.credentialIssuer.issueComplianceCredential(agentDid, profile.dimensions, profile.compliancePosture.overallScore);
      case "behavior":
        return this.credentialIssuer.issueBehaviorCredential(agentDid, profile.dimensions.behavior, profile.riskFactors.length);
      case "composite":
        return this.credentialIssuer.issueCompositeCredential(agentDid, profile);
    }
  }

  async verifyAgentCredential(credential: TrustCredential): Promise<{ valid: boolean; reason?: string }> {
    return this.credentialIssuer.verifyCredential(credential);
  }

  getAgentsByRiskLevel(riskLevel: "minimal" | "low" | "medium" | "high" | "critical"): AgentTrustProfile[] {
    return Array.from(this.profiles.values()).filter((p) => p.riskLevel === riskLevel);
  }

  getAgentsOnProbation(): AgentTrustProfile[] {
    return Array.from(this.profiles.values()).filter((p) => p.status === "probation" || p.status === "suspended");
  }

  getEmergingThreats(): { agentDid: string; threatLevel: number }[] {
    return this.behavioralAnalyzer.detectEmergingThreats(Array.from(this.profiles.keys()));
  }

  private determineStatus(score: number, riskLevel: string): AgentStatus {
    if (riskLevel === "critical") return "suspended";
    if (riskLevel === "high") return "probation";
    return "active";
  }

  // ─── Behavioral runtime integration (#5) ──────────────────────────────────
  // Called by agent-runtime after each ExecDecision to feed real behavioral data.
  // Accumulates signals and re-scores the agent incrementally.

  async recordExecDecision(
    agentDid: string,
    agentName: string,
    tenantId: string,
    decision: { allowed: boolean; sandbox: string; requiresApproval: boolean; tool: string; tier: string; reason: string }
  ): Promise<void> {
    const signal: BehavioralSignal = {
      type: decision.allowed ? "normal_operation" : "suspicious_pattern",
      timestamp: new Date().toISOString(),
      confidence: decision.sandbox === "denied" ? 0.9 : decision.requiresApproval ? 0.6 : 0.3,
      details: `Tool: ${decision.tool} | Tier: ${decision.tier} | Decision: ${decision.sandbox} | ${decision.reason}`,
      impact: decision.sandbox === "denied" ? -5 : decision.requiresApproval ? -1 : +1,
    };

    const existing = this.profiles.get(agentDid);
    if (existing) {
      await this.updateAgentSignals(agentDid, [signal]);
    } else {
      await this.scoreAgent(agentDid, agentName, tenantId, [signal]);
    }

    // Publish to A2Z SOC agent trust API if env var set
    const a2zApiKey = process.env.A2Z_SOC_API_KEY;
    const a2zEndpoint = process.env.A2Z_SOC_ENDPOINT ?? "https://a2zsoc.com";
    if (a2zApiKey) {
      fetch(`${a2zEndpoint}/api/platform/agent-trust/record`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${a2zApiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentDid, decision: decision.sandbox, tool: decision.tool, tier: decision.tier, reason: decision.reason }),
      }).catch(() => { /* non-fatal */ });
    }
  }

  getCurrentTrustScore(agentDid: string): number {
    return this.profiles.get(agentDid)?.overallTrustScore ?? 50;
  }

  isToolAccessGranted(agentDid: string, toolTier: "read" | "write" | "destructive"): boolean {
    const score = this.getCurrentTrustScore(agentDid);
    if (toolTier === "read") return score >= 30;
    if (toolTier === "write") return score >= 60;
    if (toolTier === "destructive") return score >= 80;
    return false;
  }

  getTrustScoreCalculator(): TrustScoreCalculator {
    return this.calculator;
  }

  getBehavioralAnalyzer(): BehavioralAnalyzer {
    return this.behavioralAnalyzer;
  }

  getTrustCredentialIssuer(): TrustCredentialIssuer {
    return this.credentialIssuer;
  }
}

export { TrustScoreCalculator } from "./scoring/TrustScoreCalculator.js";
export { BehavioralAnalyzer } from "./scoring/BehavioralAnalyzer.js";
export { TrustCredentialIssuer } from "./credentials/TrustCredentialIssuer.js";
export type * from "./types.js";
