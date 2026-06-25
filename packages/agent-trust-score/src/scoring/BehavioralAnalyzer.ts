import type { BehavioralSignal, BehavioralAnomaly, BehavioralAnalysis } from "../types.js";

export interface BehavioralPattern {
  id: string;
  name: string;
  detector: (signals: BehavioralSignal[]) => boolean;
  anomalyType: BehavioralAnomaly;
  confidence: number;
  impact: number;
}

const DEFAULT_PATTERNS: BehavioralPattern[] = [
  {
    id: "bp-loop",
    name: "Loop Detection",
    detector: (signals) => {
      const loopSignals = signals.filter((s) => s.type === "loop_detected");
      return loopSignals.length >= 3;
    },
    anomalyType: "loop_detected",
    confidence: 0.9,
    impact: 20,
  },
  {
    id: "bp-rapid",
    name: "Rapid Discovery",
    detector: (signals) => {
      const now = Date.now();
      const recent = signals.filter((s) => now - new Date(s.timestamp).getTime() < 60000);
      return recent.length > 10;
    },
    anomalyType: "rapid_discovery",
    confidence: 0.85,
    impact: 15,
  },
  {
    id: "bp-semantic",
    name: "Semantic Thought Loop",
    detector: (signals) => {
      const semantic = signals.filter((s) => s.type === "semantic_thought_loop");
      return semantic.length >= 2;
    },
    anomalyType: "semantic_thought_loop",
    confidence: 0.8,
    impact: 25,
  },
  {
    id: "bp-tool-abuse",
    name: "Tool Abuse Pattern",
    detector: (signals) => {
      const toolAbuse = signals.filter((s) => s.type === "tool_abuse");
      return toolAbuse.length >= 2;
    },
    anomalyType: "tool_abuse",
    confidence: 0.9,
    impact: 30,
  },
  {
    id: "bp-exfil",
    name: "Data Exfiltration Pattern",
    detector: (signals) => {
      const exfil = signals.filter((s) => s.type === "data_exfiltration");
      return exfil.length >= 1;
    },
    anomalyType: "data_exfiltration",
    confidence: 0.95,
    impact: 40,
  },
  {
    id: "bp-privilege",
    name: "Privilege Escalation Pattern",
    detector: (signals) => {
      const priv = signals.filter((s) => s.type === "privilege_escalation");
      return priv.length >= 1;
    },
    anomalyType: "privilege_escalation",
    confidence: 0.9,
    impact: 35,
  },
];

export class BehavioralAnalyzer {
  private patterns: BehavioralPattern[];
  private analysisHistory: Map<string, BehavioralAnalysis[]> = new Map();

  constructor(patterns: BehavioralPattern[] = DEFAULT_PATTERNS) {
    this.patterns = patterns;
  }

  analyze(agentDid: string, signals: BehavioralSignal[], timespan: number = 3600000): BehavioralAnalysis {
    const anomalies: BehavioralAnomaly[] = [];
    const recommendations: string[] = [];

    for (const pattern of this.patterns) {
      if (pattern.detector(signals)) {
        anomalies.push(pattern.anomalyType);
        recommendations.push(`Investigate ${pattern.name} for agent ${agentDid}`);
      }
    }

    const riskScore = this.calculateRiskScore(anomalies, signals);
    const analysis: BehavioralAnalysis = {
      agentDid,
      timespan,
      totalActions: signals.length,
      anomalies,
      anomalyCount: anomalies.length,
      riskScore,
      recommendations,
    };

    const history = this.analysisHistory.get(agentDid) || [];
    history.push(analysis);
    if (history.length > 100) history.shift();
    this.analysisHistory.set(agentDid, history);

    return analysis;
  }

  private calculateRiskScore(anomalies: BehavioralAnomaly[], signals: BehavioralSignal[]): number {
    let riskScore = 0;

    for (const anomaly of anomalies) {
      const pattern = this.patterns.find((p) => p.anomalyType === anomaly);
      if (pattern) {
        riskScore += pattern.impact * pattern.confidence;
      }
    }

    const suspiciousSignals = signals.filter((s) => s.type !== "normal_operation");
    riskScore += suspiciousSignals.length * 2;

    return Math.min(100, riskScore);
  }

  getAnalysisHistory(agentDid: string): BehavioralAnalysis[] {
    return this.analysisHistory.get(agentDid) || [];
  }

  getLatestAnalysis(agentDid: string): BehavioralAnalysis | undefined {
    const history = this.analysisHistory.get(agentDid);
    return history ? history[history.length - 1] : undefined;
  }

  detectEmergingThreats(agentDids: string[]): { agentDid: string; threatLevel: number }[] {
    const threats: { agentDid: string; threatLevel: number }[] = [];

    for (const agentDid of agentDids) {
      const history = this.analysisHistory.get(agentDid) || [];
      if (history.length < 2) continue;

      const recent = history.slice(-5);
      const avgRisk = recent.reduce((sum, a) => sum + a.riskScore, 0) / recent.length;
      const trend = recent[recent.length - 1].riskScore - recent[0].riskScore;

      if (avgRisk > 50 || trend > 20) {
        threats.push({ agentDid, threatLevel: avgRisk + trend * 0.5 });
      }
    }

    return threats.sort((a, b) => b.threatLevel - a.threatLevel);
  }
}
