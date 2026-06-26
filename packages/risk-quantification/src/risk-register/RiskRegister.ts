import type { RiskAppetite, RiskHeatMap, RiskHeatMapCell, RiskQuantification, RiskRegisterEntry, RiskScenario, RiskTrend } from '../types.js';
import { FAIRCalculator } from '../fair/FAIRCalculator.js';
import { MonteCarloEngine } from '../monte-carlo/MonteCarloEngine.js';

function riskLevel(score: number): RiskQuantification['riskLevel'] {
  if (score >= 90) return 'critical';
  if (score >= 70) return 'high';
  if (score >= 40) return 'medium';
  if (score >= 20) return 'low';
  return 'negligible';
}

function recommendation(level: RiskQuantification['riskLevel'], ale: number): string {
  const formatted = Math.round(ale).toLocaleString();
  switch (level) {
    case 'critical': return `CRITICAL: Annualized loss expectancy of $${formatted} requires immediate mitigation. Implement compensating controls and escalate to executive risk committee.`;
    case 'high': return `HIGH: ALE of $${formatted} warrants priority treatment. Develop risk response plan within 30 days.`;
    case 'medium': return `MEDIUM: ALE of $${formatted} should be monitored with periodic reassessment. Consider cost-effective controls.`;
    case 'low': return `LOW: ALE of $${formatted} is within acceptable range. Monitor and reassess annually.`;
    case 'negligible': return `NEGLIGIBLE: ALE of $${formatted} poses minimal threat. Accept risk.`;
  }
}

function computeRiskScore(ale: number, var95: number, iterations: number): number {
  const aleScore = Math.min(50, (Math.log10(ale + 1) / 8) * 50);
  const tailScore = Math.min(30, (Math.log10(var95 + 1) / 8) * 30);
  const freqScore = Math.min(20, (iterations > 0 ? 1 : 0) * 20);
  return Math.round(Math.min(100, aleScore + tailScore + freqScore));
}

export class RiskRegister {
  private entries: Map<string, RiskRegisterEntry> = new Map();
  private trends: RiskTrend[] = [];
  private mcIterations: number;
  private mcSeed?: number;

  constructor(options?: { iterations?: number; seed?: number }) {
    this.mcIterations = options?.iterations ?? 10000;
    this.mcSeed = options?.seed;
  }

  addScenario(scenario: RiskScenario): void {
    const q = this.quantify(scenario);
    this.entries.set(scenario.id, {
      scenario,
      quantification: q,
      status: 'assessed',
      lastAssessed: new Date(),
      nextReview: new Date(Date.now() + 90 * 86400000),
    });
    this.trends.push({
      date: new Date(),
      riskScore: q.riskScore,
      ale: q.fairModel.annualizedLossExpectancy,
      scenarioId: scenario.id,
    });
  }

  quantify(scenario: RiskScenario): RiskQuantification {
    const mcEngine = new MonteCarloEngine(scenario, { iterations: this.mcIterations, seed: this.mcSeed });
    const mcResult = mcEngine.run();

    const fairCalc = new FAIRCalculator(scenario, { iterations: this.mcIterations, seed: this.mcSeed });
    const fairModel = fairCalc.calculate();

    const score = computeRiskScore(
      fairModel.annualizedLossExpectancy,
      mcResult.valueAtRisk.confidence95,
      mcResult.iterations
    );
    const level = riskLevel(score);

    return {
      scenario,
      fairModel,
      monteCarloResult: mcResult,
      riskScore: score,
      riskLevel: level,
      recommendation: recommendation(level, fairModel.annualizedLossExpectancy),
      calculatedAt: new Date(),
    };
  }

  updateStatus(scenarioId: string, status: RiskRegisterEntry['status']): boolean {
    const entry = this.entries.get(scenarioId);
    if (!entry) return false;
    entry.status = status;
    return true;
  }

  getEntry(scenarioId: string): RiskRegisterEntry | undefined {
    return this.entries.get(scenarioId);
  }

  getAllEntries(): RiskRegisterEntry[] {
    return [...this.entries.values()];
  }

  getActiveEntries(): RiskRegisterEntry[] {
    return this.getAllEntries().filter(e => e.status === 'assessed' || e.status === 'monitoring');
  }

  portfolioMetrics(): {
    totalALE: number;
    totalVaR95: number;
    totalVaR99: number;
    meanRiskScore: number;
    criticalCount: number;
    highCount: number;
    scenarioCount: number;
  } {
    const active = this.getActiveEntries();
    let totalALE = 0, totalVaR95 = 0, totalVaR99 = 0, totalScore = 0;
    let critical = 0, high = 0;

    for (const entry of active) {
      if (!entry.quantification) continue;
      totalALE += entry.quantification.fairModel.annualizedLossExpectancy;
      totalVaR95 += entry.quantification.monteCarloResult.valueAtRisk.confidence95;
      totalVaR99 += entry.quantification.monteCarloResult.valueAtRisk.confidence99;
      totalScore += entry.quantification.riskScore;
      if (entry.quantification.riskLevel === 'critical') critical++;
      if (entry.quantification.riskLevel === 'high') high++;
    }

    return {
      totalALE,
      totalVaR95,
      totalVaR99,
      meanRiskScore: active.length > 0 ? totalScore / active.length : 0,
      criticalCount: critical,
      highCount: high,
      scenarioCount: active.length,
    };
  }

  getTrends(): RiskTrend[] {
    return [...this.trends];
  }

  getTrendsForScenario(scenarioId: string): RiskTrend[] {
    return this.trends.filter(t => t.scenarioId === scenarioId);
  }

  generateHeatMap(likelihoodBins = 5, impactBins = 5): RiskHeatMap {
    const active = this.getActiveEntries();
    const cells: RiskHeatMapCell[] = [];

    for (let l = 0; l < likelihoodBins; l++) {
      for (let i = 0; i < impactBins; i++) {
        cells.push({
          likelihood: l,
          impact: i,
          scenarios: [],
          totalRisk: 0,
        });
      }
    }

    for (const entry of active) {
      if (!entry.quantification) continue;
      const q = entry.quantification;
      const ale = q.fairModel.annualizedLossExpectancy;
      const maxALE = this.estimateMaxALE();
      const likelihoodBin = Math.min(
        likelihoodBins - 1,
        Math.floor((q.fairModel.lossEventFrequency / 100) * likelihoodBins)
      );
      const impactBin = Math.min(
        impactBins - 1,
        Math.floor((q.fairModel.lossMagnitude / (maxALE || 1)) * impactBins)
      );
      const cellIdx = likelihoodBin * impactBins + impactBin;
      cells[cellIdx].scenarios.push(entry.scenario.id);
      cells[cellIdx].totalRisk += ale;
    }

    return {
      cells,
      axisLabels: { x: 'Impact', y: 'Likelihood' },
    };
  }

  assessAppetite(maxRiskScore = 70, maxALE = 1000000, maxVaR95 = 2000000): RiskAppetite {
    const active = this.getActiveEntries();
    const tolerable: string[] = [];
    const exceedances: string[] = [];

    for (const entry of active) {
      if (!entry.quantification) continue;
      const q = entry.quantification;
      const overScore = q.riskScore > maxRiskScore;
      const overALE = q.fairModel.annualizedLossExpectancy > maxALE;
      const overVaR = q.monteCarloResult.valueAtRisk.confidence95 > maxVaR95;
      if (overScore || overALE || overVaR) {
        exceedances.push(entry.scenario.id);
      } else {
        tolerable.push(entry.scenario.id);
      }
    }

    return {
      maxRiskScore,
      maxALE,
      maxVaR95,
      tolerableScenarios: tolerable,
      boundaryExceedances: exceedances,
    };
  }

  topRisks(count = 10): RiskQuantification[] {
    return this.getActiveEntries()
      .filter(e => e.quantification != null)
      .map(e => e.quantification!)
      .sort((a, b) => b.riskScore - a.riskScore)
      .slice(0, count);
  }

  private estimateMaxALE(): number {
    const entries = this.getActiveEntries();
    if (entries.length === 0) return 1;
    let max = 0;
    for (const e of entries) {
      if (e.quantification && e.quantification.fairModel.annualizedLossExpectancy > max) {
        max = e.quantification.fairModel.annualizedLossExpectancy;
      }
    }
    return max || 1;
  }
}
