import type { FrameworkCode } from "../types.js";
import type {
  RegulatoryChange,
  ImpactAnalysis,
  AffectedControl,
  CrossFrameworkImpact,
  ImpactLevel,
} from "../types.js";

export interface ImpactAnalyzerConfig {
  impactScoringWeights: {
    controlImportance: number;
    changeSeverity: number;
    frameworkCriticality: number;
  };
  crossFrameworkMappings: Map<string, CrossFrameworkImpact[]>;
}

const DEFAULT_CONFIG: ImpactAnalyzerConfig = {
  impactScoringWeights: {
    controlImportance: 0.4,
    changeSeverity: 0.35,
    frameworkCriticality: 0.25,
  },
  crossFrameworkMappings: new Map(),
};

export class RegulatoryImpactAnalyzer {
  private config: ImpactAnalyzerConfig;
  private impactHistory: Map<string, ImpactAnalysis> = new Map();

  constructor(config: Partial<ImpactAnalyzerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  analyzeImpact(
    change: RegulatoryChange,
    currentControls: Map<string, { controlId: string; controlCode: string; framework: FrameworkCode; status: string }>
  ): ImpactAnalysis {
    const affectedControls = this.identifyAffectedControls(change, currentControls);
    const crossFrameworkImpact = this.analyzeCrossFrameworkImpact(change);
    const overallImpact = this.calculateOverallImpact(affectedControls, crossFrameworkImpact);
    const estimatedRemediationDays = this.estimateRemediationDays(affectedControls);
    const complianceGapScore = this.calculateGapScore(affectedControls);
    const recommendedActions = this.generateRecommendations(change, affectedControls);

    const analysis: ImpactAnalysis = {
      affectedControls,
      overallImpact,
      estimatedRemediationDays,
      complianceGapScore,
      recommendedActions,
      crossFrameworkImpact,
    };

    this.impactHistory.set(change.id, analysis);
    return analysis;
  }

  private identifyAffectedControls(
    change: RegulatoryChange,
    currentControls: Map<string, { controlId: string; controlCode: string; framework: FrameworkCode; status: string }>
  ): AffectedControl[] {
    const affected: AffectedControl[] = [];

    for (const [controlId, control] of currentControls) {
      const relevanceScore = this.calculateControlRelevance(change, control);

      if (relevanceScore > 0.5) {
        affected.push({
          controlId: control.controlId,
          controlCode: control.controlCode,
          framework: control.framework,
          impact: this.determineImpactLevel(relevanceScore, control.status),
          gapDescription: this.generateGapDescription(change, control),
          remediation: this.suggestRemediation(change, control),
          estimatedEffort: this.estimateEffort(relevanceScore, control.status),
        });
      }
    }

    return affected.sort((a, b) => {
      const impactOrder = { critical: 4, significant: 3, moderate: 2, minimal: 1, none: 0 };
      return (impactOrder[b.impact] || 0) - (impactOrder[a.impact] || 0);
    });
  }

  private calculateControlRelevance(
    change: RegulatoryChange,
    control: { controlId: string; controlCode: string; framework: FrameworkCode; status: string }
  ): number {
    let relevance = 0;

    if (change.affectedControls.includes(control.controlCode)) {
      relevance += 0.6;
    }

    if (change.framework === control.framework) {
      relevance += 0.3;
    }

    const keywords = change.title.toLowerCase().split(/\s+/);
    const controlKeywords = control.controlCode.toLowerCase().split(/[.\-_]/);
    const overlap = keywords.filter((k) => controlKeywords.some((ck) => ck.includes(k)));
    relevance += (overlap.length / keywords.length) * 0.1;

    return Math.min(1, relevance);
  }

  private determineImpactLevel(relevanceScore: number, controlStatus: string): ImpactLevel {
    const adjustedScore = relevanceScore * (controlStatus === "implemented" ? 1.2 : 1.0);

    if (adjustedScore >= 0.8) return "critical";
    if (adjustedScore >= 0.6) return "significant";
    if (adjustedScore >= 0.4) return "moderate";
    if (adjustedScore >= 0.2) return "minimal";
    return "none";
  }

  private analyzeCrossFrameworkImpact(change: RegulatoryChange): CrossFrameworkImpact[] {
    const impacts: CrossFrameworkImpact[] = [];

    for (const controlId of change.affectedControls) {
      const mappings = this.config.crossFrameworkMappings.get(`${change.framework}:${controlId}`) || [];
      impacts.push(...mappings);
    }

    return impacts;
  }

  private calculateOverallImpact(affectedControls: AffectedControl[], crossFrameworkImpact: CrossFrameworkImpact[]): ImpactLevel {
    const impactScores = { critical: 4, significant: 3, moderate: 2, minimal: 1, none: 0 };
    const controlImpacts = affectedControls.map((c) => impactScores[c.impact] || 0);
    const maxControlImpact = controlImpacts.length > 0 ? Math.max(...controlImpacts) : 0;

    const crossFrameworkBonus = crossFrameworkImpact.length > 0 ? 0.5 : 0;
    const totalScore = maxControlImpact + crossFrameworkBonus;

    if (totalScore >= 4) return "critical";
    if (totalScore >= 3) return "significant";
    if (totalScore >= 2) return "moderate";
    if (totalScore >= 1) return "minimal";
    return "none";
  }

  private estimateRemediationDays(affectedControls: AffectedControl[]): number {
    const effortDays: Record<string, number> = {
      "1-2 days": 1.5,
      "3-5 days": 4,
      "1-2 weeks": 10,
      "2-4 weeks": 21,
      "1-3 months": 60,
    };

    return affectedControls.reduce((total, control) => {
      return total + (effortDays[control.estimatedEffort] || 5);
    }, 0);
  }

  private calculateGapScore(affectedControls: AffectedControl[]): number {
    const impactWeights = { critical: 25, significant: 15, moderate: 8, minimal: 3, none: 0 };
    return affectedControls.reduce((score, control) => {
      return score + (impactWeights[control.impact] || 0);
    }, 0);
  }

  private generateRecommendations(
    change: RegulatoryChange,
    affectedControls: AffectedControl[]
  ): string[] {
    const recommendations: string[] = [];

    const criticalControls = affectedControls.filter((c) => c.impact === "critical");
    if (criticalControls.length > 0) {
      recommendations.push(`Immediately review ${criticalControls.length} critically affected controls`);
    }

    if (affectedControls.length > 5) {
      recommendations.push("Consider phased implementation approach for broad regulatory changes");
    }

    const crossFrameworkControls = affectedControls.filter((c) =>
      change.affectedControls.some((ac) => ac !== c.controlCode)
    );
    if (crossFrameworkControls.length > 0) {
      recommendations.push("Leverage existing cross-framework mappings to reduce remediation effort");
    }

    recommendations.push("Schedule compliance review meeting within 5 business days");
    recommendations.push("Update compliance documentation and evidence repository");

    return recommendations;
  }

  private generateGapDescription(
    change: RegulatoryChange,
    control: { controlId: string; controlCode: string; framework: FrameworkCode; status: string }
  ): string {
    return `Regulatory change "${change.title}" affects control ${control.controlCode} (${control.status}). ${change.summary}`;
  }

  private suggestRemediation(
    change: RegulatoryChange,
    control: { controlId: string; controlCode: string; framework: FrameworkCode; status: string }
  ): string {
    if (control.status === "not_started") {
      return `Implement new control requirements per ${change.title}`;
    }
    if (control.status === "in_progress") {
      return `Update in-progress implementation to address new requirements`;
    }
    return `Review and update existing implementation for compliance with changes`;
  }

  private estimateEffort(relevanceScore: number, controlStatus: string): string {
    if (relevanceScore > 0.8 && controlStatus === "not_started") return "2-4 weeks";
    if (relevanceScore > 0.6) return "1-2 weeks";
    if (relevanceScore > 0.4) return "3-5 days";
    return "1-2 days";
  }

  getImpactHistory(changeId: string): ImpactAnalysis | undefined {
    return this.impactHistory.get(changeId);
  }
}
