import type { CompliancePosture, ControlPosture, RiskArea, DriftEvent, FrameworkCode } from "../types.js";

export interface PostureCalculationInput {
  tenantId: string;
  frameworkCode: FrameworkCode;
  controlStatuses: Map<string, { implemented: boolean; evidenceValid: boolean; lastChecked: string }>;
  driftEvents: DriftEvent[];
}

const SEVERITY_WEIGHTS: Record<string, number> = {
  info: 0,
  low: 0.1,
  medium: 0.3,
  high: 0.6,
  critical: 1.0,
};

export class CompliancePostureMonitor {
  private postureHistory: Map<string, CompliancePosture[]> = new Map();

  calculatePosture(input: PostureCalculationInput): CompliancePosture {
    const controlScores = new Map<string, ControlPosture>();
    let totalScore = 0;
    let controlCount = 0;

    for (const [controlId, status] of input.controlStatuses) {
      const controlDrifts = input.driftEvents.filter((d) => d.controlId === controlId && !d.resolved);
      const score = this.calculateControlScore(status, controlDrifts);
      const riskLevel = this.getRiskLevel(score);

      controlScores.set(controlId, {
        controlId,
        controlCode: controlId,
        score,
        status: riskLevel,
        lastCheckedAt: status.lastChecked,
        driftEvents: controlDrifts,
        evidenceIntegrity: status.evidenceValid,
      });

      totalScore += score;
      controlCount++;
    }

    const overallScore = controlCount > 0 ? totalScore / controlCount : 0;
    const unresolvedDrifts = input.driftEvents.filter((d) => !d.resolved).length;
    const trend = this.calculateTrend(input.tenantId, input.frameworkCode, overallScore);
    const riskAreas = this.identifyRiskAreas(controlScores);

    const posture: CompliancePosture = {
      tenantId: input.tenantId,
      frameworkCode: input.frameworkCode,
      overallScore,
      controlScores,
      trend,
      driftCount: input.driftEvents.length,
      unresolvedDrifts,
      lastCalculatedAt: new Date().toISOString(),
      riskAreas,
    };

    this.storePosture(input.tenantId, input.frameworkCode, posture);
    return posture;
  }

  private calculateControlScore(
    status: { implemented: boolean; evidenceValid: boolean; lastChecked: string },
    drifts: DriftEvent[]
  ): number {
    let score = 0;

    if (status.implemented) score += 40;
    if (status.evidenceValid) score += 30;

    const lastChecked = new Date(status.lastChecked).getTime();
    const ageDays = (Date.now() - lastChecked) / 86400000;
    if (ageDays < 7) score += 20;
    else if (ageDays < 30) score += 10;

    const driftPenalty = drifts.reduce((sum, d) => sum + (SEVERITY_WEIGHTS[d.severity] || 0) * 10, 0);
    score = Math.max(0, score - driftPenalty);

    return Math.min(100, score);
  }

  private getRiskLevel(score: number): ControlPosture["status"] {
    if (score >= 80) return "healthy";
    if (score >= 50) return "degraded";
    return "critical";
  }

  private calculateTrend(tenantId: string, frameworkCode: string, currentScore: number): CompliancePosture["trend"] {
    const key = `${tenantId}:${frameworkCode}`;
    const history = this.postureHistory.get(key) || [];
    if (history.length === 0) return "stable";

    const lastScore = history[history.length - 1].overallScore;
    const diff = currentScore - lastScore;

    if (diff > 5) return "improving";
    if (diff < -5) return "degrading";
    return "stable";
  }

  private identifyRiskAreas(controlScores: Map<string, ControlPosture>): RiskArea[] {
    const riskAreas: RiskArea[] = [];
    const domainScores = new Map<string, { total: number; count: number; controls: string[] }>();

    for (const [controlId, posture] of controlScores) {
      const domain = controlId.split(".")[0] || "general";
      const existing = domainScores.get(domain) || { total: 0, count: 0, controls: [] };
      existing.total += posture.score;
      existing.count++;
      existing.controls.push(controlId);
      domainScores.set(domain, existing);
    }

    for (const [domain, data] of domainScores) {
      const avgScore = data.total / data.count;
      if (avgScore < 70) {
        riskAreas.push({
          domain,
          riskScore: 100 - avgScore,
          affectedControls: data.controls,
          recommendation: `Review and remediate controls in ${domain} domain`,
        });
      }
    }

    return riskAreas.sort((a, b) => b.riskScore - a.riskScore);
  }

  private storePosture(tenantId: string, frameworkCode: string, posture: CompliancePosture): void {
    const key = `${tenantId}:${frameworkCode}`;
    const history = this.postureHistory.get(key) || [];
    history.push(posture);
    if (history.length > 100) history.shift();
    this.postureHistory.set(key, history);
  }

  getPostureHistory(tenantId: string, frameworkCode: string): CompliancePosture[] {
    return this.postureHistory.get(`${tenantId}:${frameworkCode}`) || [];
  }
}
