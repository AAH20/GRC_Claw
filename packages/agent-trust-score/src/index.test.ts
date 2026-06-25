import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { AgentTrustScoreEngine } from "./index.js";
import type { TrustCredential, BehavioralSignal } from "./types.js";
import type { CredentialStore } from "./credentials/TrustCredentialIssuer.js";

const mockCredentialStore: CredentialStore = {
  async store(): Promise<void> {},
  async get(): Promise<TrustCredential | undefined> { return undefined; },
  async listByAgent(): Promise<TrustCredential[]> { return []; },
  async revoke(): Promise<boolean> { return true; },
};

const testSignals: BehavioralSignal[] = [
  { type: "normal_operation", timestamp: new Date().toISOString(), confidence: 0.9, details: "Normal tool usage", impact: 0 },
  { type: "normal_operation", timestamp: new Date().toISOString(), confidence: 0.85, details: "Standard queries", impact: 0 },
];

describe("AgentTrustScoreEngine", () => {
  it("should score agent successfully", async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: "did:grc:test",
      credentialStore: mockCredentialStore,
    });

    const profile = await engine.scoreAgent(
      "did:grc:agent-1",
      "Test Agent",
      "tenant-1",
      testSignals,
      75,
      ["iso27001"]
    );

    assert.equal(profile.agentDid, "did:grc:agent-1");
    assert.equal(profile.agentName, "Test Agent");
    assert.equal(profile.status, "active");
    assert.ok(profile.overallTrustScore >= 0);
    assert.ok(profile.overallTrustScore <= 100);
  });

  it("should detect behavioral anomalies", async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: "did:grc:test",
      credentialStore: mockCredentialStore,
    });

    const anomalousSignals: BehavioralSignal[] = [
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.9, details: "Loop detected", impact: 20 },
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.85, details: "Loop again", impact: 20 },
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.9, details: "Loop third", impact: 20 },
    ];

    const profile = await engine.scoreAgent(
      "did:grc:agent-anomaly",
      "Anomaly Agent",
      "tenant-1",
      anomalousSignals,
      50
    );

    assert.ok(profile.riskFactors.length > 0);
  });

  it("should issue trust credential", async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: "did:grc:test",
      credentialStore: mockCredentialStore,
    });

    await engine.scoreAgent("did:grc:agent-cred", "Cred Agent", "tenant-1", testSignals, 80);
    const credential = await engine.issueTrustCredential("did:grc:agent-cred", "identity");

    assert.ok(credential.id.startsWith("vc-trust-"));
    assert.equal(credential.type, "identity");
    assert.ok(credential.signature);
  });

  it("should get agents by risk level", async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: "did:grc:test",
      credentialStore: mockCredentialStore,
    });

    await engine.scoreAgent("did:grc:agent-low", "Low Risk", "tenant-1", testSignals, 90);
    const lowRiskAgents = engine.getAgentsByRiskLevel("low");
    assert.ok(lowRiskAgents.length > 0);
  });
});

describe("TrustScoreCalculator", () => {
  it("should calculate weighted overall score", async () => {
    const { TrustScoreCalculator } = await import("./scoring/TrustScoreCalculator.js");
    const calculator = new TrustScoreCalculator();

    const score = calculator.calculateOverallScore({
      identity: 90,
      capability: 80,
      compliance: 85,
      behavior: 95,
      provenance: 88,
    });

    assert.ok(score >= 0);
    assert.ok(score <= 100);
  });

  it("should apply time decay", async () => {
    const { TrustScoreCalculator } = await import("./scoring/TrustScoreCalculator.js");
    const calculator = new TrustScoreCalculator({ decayRate: 0.1 });

    const decayedScore = calculator.applyTimeDecay(80, new Date(Date.now() - 3600000).toISOString());
    assert.ok(decayedScore < 80);
    assert.ok(decayedScore >= 0);
  });

  it("should identify risk factors for low scores", async () => {
    const { TrustScoreCalculator } = await import("./scoring/TrustScoreCalculator.js");
    const calculator = new TrustScoreCalculator();

    const factors = calculator.identifyRiskFactors(
      { identity: 30, capability: 40, compliance: 20, behavior: 50, provenance: 60 },
      []
    );

    assert.ok(factors.length > 0);
  });
});

describe("BehavioralAnalyzer", () => {
  it("should detect loop patterns", async () => {
    const { BehavioralAnalyzer } = await import("./scoring/BehavioralAnalyzer.js");
    const analyzer = new BehavioralAnalyzer();

    const signals: BehavioralSignal[] = [
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.9, details: "Loop 1", impact: 20 },
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.85, details: "Loop 2", impact: 20 },
      { type: "loop_detected", timestamp: new Date().toISOString(), confidence: 0.9, details: "Loop 3", impact: 20 },
    ];

    const analysis = analyzer.analyze("did:grc:test", signals);
    assert.ok(analysis.anomalies.includes("loop_detected"));
    assert.ok(analysis.riskScore > 0);
  });

  it("should return normal analysis for clean signals", async () => {
    const { BehavioralAnalyzer } = await import("./scoring/BehavioralAnalyzer.js");
    const analyzer = new BehavioralAnalyzer();

    const signals: BehavioralSignal[] = [
      { type: "normal_operation", timestamp: new Date().toISOString(), confidence: 0.9, details: "Normal", impact: 0 },
    ];

    const analysis = analyzer.analyze("did:grc:clean", signals);
    assert.equal(analysis.anomalyCount, 0);
  });
});
