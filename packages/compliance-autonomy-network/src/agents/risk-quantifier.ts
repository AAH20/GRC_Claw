import { randomBytes } from "node:crypto";
import { BaseAgent } from "./base-agent.js";
import type {
  SwarmTask,
  SwarmResult,
  RiskAssessment,
  RiskItem,
  FrameworkRiskBreakdown,
  ControlStatus,
  ComplianceFramework,
  RiskLevel,
} from "../types.js";

// ============================================================================
// RiskQuantifier – quantifies compliance risk across frameworks
// ============================================================================

export class RiskQuantifier extends BaseAgent {
  private assessments: Map<string, RiskAssessment> = new Map();

  constructor(signingKey: string = randomBytes(32).toString("hex")) {
    super(
      "risk-quantifier",
      "Risk Quantification Agent",
      "1.0.0",
      [
        {
          name: "quantify-risk",
          frameworks: ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA", "GDPR", "CCPA", "SOX", "FedRAMP", "Custom"],
          confidenceLevel: 0.90,
        },
      ],
      signingKey,
    );
  }

  protected async doExecute(task: SwarmTask): Promise<SwarmResult["output"]> {
    const controlStatuses = task.input.customParameters?.controlStatuses as ControlStatus[] | undefined;
    const riskScope = task.input.riskScope;

    const assessment = await this.quantifyRisk(task.framework, controlStatuses ?? [], riskScope);
    this.assessments.set(task.id, assessment);

    const topRisks = assessment.topRisks.filter((r) => r.riskLevel === "critical" || r.riskLevel === "high");

    return {
      riskAssessment: assessment,
      summary: `Risk quantification complete: overall score ${assessment.overallScore.toFixed(2)}/10, risk level ${assessment.riskLevel}. Residual risk: ${assessment.residualRiskScore.toFixed(2)}/10. ${assessment.topRisks.length} risk(s) identified, ${topRisks.length} critical/high.`,
      recommendations: this.generateRiskRecommendations(assessment),
    };
  }

  // ------------------------------------------------------------------
  // Risk quantification
  // ------------------------------------------------------------------

  private async quantifyRisk(
    framework: ComplianceFramework,
    controlStatuses: ControlStatus[],
    riskScope?: SwarmTask["input"]["riskScope"],
  ): Promise<RiskAssessment> {
    const frameworkBreakdowns = this.calculateFrameworkBreakdowns(framework, controlStatuses);
    const topRisks = this.identifyTopRisks(framework, controlStatuses, riskScope);
    const overallScore = this.calculateOverallScore(frameworkBreakdowns, topRisks);
    const riskLevel = this.scoreToRiskLevel(overallScore);
    const mitigatedRisks = topRisks
      .filter((r) => r.mitigationStatus === "fully-mitigated")
      .map((r) => r.id);
    const residualRiskScore = this.calculateResidualRisk(topRisks);

    return {
      overallScore,
      riskLevel,
      frameworkBreakdown: frameworkBreakdowns,
      topRisks,
      mitigatedRisks,
      residualRiskScore,
      calculatedAt: new Date().toISOString(),
    };
  }

  private calculateFrameworkBreakdowns(
    framework: ComplianceFramework,
    controlStatuses: ControlStatus[],
  ): FrameworkRiskBreakdown[] {
    const relevantStatuses = controlStatuses.filter((s) => s.framework === framework);

    if (relevantStatuses.length === 0) {
      return [
        {
          framework,
          score: 5.0,
          riskLevel: "medium",
          controlsCompliant: 0,
          controlsNonCompliant: 0,
          controlsPartial: 0,
          controlsTotal: 0,
        },
      ];
    }

    const compliant = relevantStatuses.filter((s) => s.status === "compliant").length;
    const nonCompliant = relevantStatuses.filter((s) => s.status === "non-compliant").length;
    const partial = relevantStatuses.filter((s) => s.status === "partial").length;
    const total = relevantStatuses.length;

    const complianceRate = total > 0 ? compliant / total : 0;
    const score = (1 - complianceRate) * 10;

    return [
      {
        framework,
        score: Math.round(score * 100) / 100,
        riskLevel: this.scoreToRiskLevel(score),
        controlsCompliant: compliant,
        controlsNonCompliant: nonCompliant,
        controlsPartial: partial,
        controlsTotal: total,
      },
    ];
  }

  private identifyTopRisks(
    framework: ComplianceFramework,
    controlStatuses: ControlStatus[],
    riskScope?: SwarmTask["input"]["riskScope"],
  ): RiskItem[] {
    const risks: RiskItem[] = [];

    for (const status of controlStatuses) {
      if (status.status === "non-compliant") {
        risks.push(
          this.createRiskItem(
            `risk-${status.controlId}`,
            `Non-compliance: ${status.title}`,
            `Control ${status.controlId} under ${framework} is not compliant. ${status.findings.map((f) => f.description).join(" ")}`,
            "critical",
            [status.controlId],
          ),
        );
      } else if (status.status === "partial") {
        risks.push(
          this.createRiskItem(
            `risk-${status.controlId}`,
            `Partial compliance: ${status.title}`,
            `Control ${status.controlId} under ${framework} is partially implemented. Gaps exist.`,
            "high",
            [status.controlId],
          ),
        );
      }
    }

    if (riskScope?.regulatoryRisk && risks.length > 0) {
      risks.push(
        this.createRiskItem(
          `reg-risk-${framework}`,
          `Regulatory exposure under ${framework}`,
          `Multiple control failures increase regulatory scrutiny risk for ${framework} compliance.`,
          risks.length > 3 ? "critical" : "high",
          controlStatuses.filter((s) => s.status !== "compliant").map((s) => s.controlId),
        ),
      );
    }

    return risks.sort((a, b) => b.score - a.score).slice(0, 10);
  }

  private createRiskItem(
    id: string,
    title: string,
    description: string,
    riskLevel: RiskLevel,
    relatedControls: string[],
  ): RiskItem {
    const likelihoodMap: Record<RiskLevel, number> = {
      critical: 0.9,
      high: 0.7,
      medium: 0.5,
      low: 0.3,
      informational: 0.1,
    };
    const impactMap: Record<RiskLevel, number> = {
      critical: 0.95,
      high: 0.75,
      medium: 0.5,
      low: 0.3,
      informational: 0.1,
    };

    const likelihood = likelihoodMap[riskLevel];
    const impact = impactMap[riskLevel];
    const score = Math.round(likelihood * impact * 10 * 100) / 100;

    return {
      id,
      title,
      description,
      riskLevel,
      likelihood,
      impact,
      score,
      relatedControls,
      mitigationStatus: "unmitigated",
    };
  }

  private calculateOverallScore(
    breakdowns: FrameworkRiskBreakdown[],
    risks: RiskItem[],
  ): number {
    if (breakdowns.length === 0) return 5.0;

    const frameworkAvgScore =
      breakdowns.reduce((sum, b) => sum + b.score, 0) / breakdowns.length;

    const criticalRisks = risks.filter((r) => r.riskLevel === "critical").length;
    const riskPenalty = criticalRisks * 0.5;

    return Math.min(10, Math.max(0, Math.round((frameworkAvgScore + riskPenalty) * 100) / 100));
  }

  private calculateResidualRisk(risks: RiskItem[]): number {
    if (risks.length === 0) return 0;

    const unmitigated = risks.filter((r) => r.mitigationStatus === "unmitigated");
    const partiallyMitigated = risks.filter((r) => r.mitigationStatus === "partially-mitigated");

    const totalRisk = unmitigated.reduce((sum, r) => sum + r.score, 0);
    const partialReduction = partiallyMitigated.reduce((sum, r) => sum + r.score * 0.3, 0);
    const avgRisk = (totalRisk - partialReduction) / Math.max(risks.length, 1);

    return Math.round(Math.max(0, Math.min(10, avgRisk)) * 100) / 100;
  }

  private scoreToRiskLevel(score: number): RiskLevel {
    if (score >= 8) return "critical";
    if (score >= 6) return "high";
    if (score >= 4) return "medium";
    if (score >= 2) return "low";
    return "informational";
  }

  private generateRiskRecommendations(assessment: RiskAssessment): string[] {
    const recs: string[] = [];

    if (assessment.riskLevel === "critical" || assessment.riskLevel === "high") {
      recs.push(`Overall risk level is ${assessment.riskLevel.toUpperCase()} – prioritize risk treatment immediately`);
    }

    const criticalRisks = assessment.topRisks.filter((r) => r.riskLevel === "critical");
    if (criticalRisks.length > 0) {
      recs.push(`${criticalRisks.length} critical risk(s) identified: ${criticalRisks.map((r) => r.title).join("; ")}`);
    }

    for (const breakdown of assessment.frameworkBreakdown) {
      if (breakdown.controlsNonCompliant > 0) {
        recs.push(
          `${breakdown.framework}: ${breakdown.controlsNonCompliant}/${breakdown.controlsTotal} controls non-compliant (risk score: ${breakdown.score})`,
        );
      }
    }

    if (assessment.residualRiskScore > 5) {
      recs.push(`Residual risk score ${assessment.residualRiskScore}/10 is above acceptable threshold – implement additional mitigations`);
    }

    if (assessment.mitigatedRisks.length > 0) {
      recs.push(`${assessment.mitigatedRisks.length} risk(s) fully mitigated – verify controls remain effective`);
    }

    return recs;
  }

  getAssessment(taskId: string): RiskAssessment | undefined {
    return this.assessments.get(taskId);
  }
}
