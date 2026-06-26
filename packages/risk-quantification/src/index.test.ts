import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { MonteCarloEngine, Random, percentile, mean, variance } from './monte-carlo/MonteCarloEngine.js';
import { FAIRCalculator } from './fair/FAIRCalculator.js';
import { RiskRegister } from './risk-register/RiskRegister.js';
import type { RiskScenario } from './types.js';

const basicScenario: RiskScenario = {
  id: 'test-ransomware',
  name: 'Ransomware Attack',
  threat: 'APT Group',
  vulnerability: 'Unpatched SMB',
  impact: { type: 'lognormal', mean: 500000, stdDev: 200000 },
  probability: { type: 'triangular', min: 0.01, mode: 0.08, max: 0.25 },
};

const fixedScenario: RiskScenario = {
  id: 'test-fixed',
  name: 'Fixed Impact',
  threat: 'Phishing',
  vulnerability: 'Weak MFA',
  impact: { type: 'uniform', min: 100000, max: 200000 },
  probability: { type: 'normal', mean: 0.1, stdDev: 0.02 },
};

describe('Random', () => {
  it('produces values in [0,1) from seeded generator', () => {
    const rng = new Random(42);
    for (let i = 0; i < 1000; i++) {
      const v = rng.next();
      assert.ok(v >= 0 && v < 1, `Value ${v} out of range`);
    }
  });

  it('is deterministic with same seed', () => {
    const a = new Random(123);
    const b = new Random(123);
    for (let i = 0; i < 100; i++) {
      assert.equal(a.next(), b.next());
    }
  });

  it('different seeds produce different sequences', () => {
    const a = new Random(1);
    const b = new Random(2);
    let same = 0;
    for (let i = 0; i < 100; i++) {
      if (a.next() === b.next()) same++;
    }
    assert.ok(same < 10, 'Sequences should differ significantly');
  });

  it('normal distribution has expected mean', () => {
    const rng = new Random(42);
    const samples: number[] = [];
    for (let i = 0; i < 100000; i++) samples.push(rng.normal(100, 15));
    const mu = mean(samples);
    assert.ok(Math.abs(mu - 100) < 1, `Mean ${mu} too far from 100`);
  });

  it('uniform distribution is bounded', () => {
    const rng = new Random(42);
    for (let i = 0; i < 10000; i++) {
      const v = rng.uniform(10, 50);
      assert.ok(v >= 10 && v <= 50, `Uniform ${v} out of bounds`);
    }
  });
});

describe('Utility functions', () => {
  it('percentile computes correct values', () => {
    const sorted = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    assert.equal(percentile(sorted, 50), 5.5);
    assert.equal(percentile(sorted, 0), 1);
    assert.equal(percentile(sorted, 100), 10);
  });

  it('mean computes correctly', () => {
    assert.equal(mean([1, 2, 3, 4, 5]), 3);
  });

  it('variance computes correctly', () => {
    assert.ok(Math.abs(variance([1, 2, 3, 4, 5], 3) - 2) < 0.001);
  });
});

describe('MonteCarloEngine', () => {
  it('runs simulation with correct iteration count', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 5000, seed: 42 });
    const result = engine.run();
    assert.equal(result.iterations, 5000);
    assert.equal(result.rawSamples.length, 5000);
  });

  it('percentiles are monotonically increasing', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    const p = result.percentiles;
    assert.ok(p.P10 <= p.P25, 'P10 <= P25');
    assert.ok(p.P25 <= p.P50, 'P25 <= P50');
    assert.ok(p.P50 <= p.P75, 'P50 <= P75');
    assert.ok(p.P75 <= p.P90, 'P75 <= P90');
    assert.ok(p.P90 <= p.P95, 'P90 <= P95');
    assert.ok(p.P95 <= p.P99, 'P95 <= P99');
  });

  it('mean is within reasonable range', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.mean > 0, 'Mean should be positive');
    assert.ok(result.mean < 500000, `Mean ${result.mean} unexpectedly high`);
  });

  it('stdDev is non-negative', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.stdDev >= 0);
    assert.ok(result.variance >= 0);
  });

  it('min <= P10 and P99 <= max', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.min <= result.percentiles.P10);
    assert.ok(result.percentiles.P99 <= result.max);
  });

  it('VaR 99 >= VaR 95', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.valueAtRisk.confidence99 >= result.valueAtRisk.confidence95);
  });

  it('CVaR >= VaR for same confidence', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.conditionalValueAtRisk.confidence95 >= result.valueAtRisk.confidence95);
    assert.ok(result.conditionalValueAtRisk.confidence99 >= result.valueAtRisk.confidence99);
  });

  it('histogram buckets sum to iteration count', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    const total = result.histogram.reduce((s, b) => s + b.count, 0);
    assert.equal(total, 10000);
  });

  it('histogram frequencies sum to ~1', () => {
    const engine = new MonteCarloEngine(basicScenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    const totalFreq = result.histogram.reduce((s, b) => s + b.frequency, 0);
    assert.ok(Math.abs(totalFreq - 1) < 0.001, `Total frequency ${totalFreq}`);
  });

  it('deterministic with seed produces identical results', () => {
    const a = new MonteCarloEngine(basicScenario, { iterations: 5000, seed: 7 });
    const b = new MonteCarloEngine(basicScenario, { iterations: 5000, seed: 7 });
    const ra = a.run();
    const rb = b.run();
    assert.equal(ra.mean, rb.mean);
    assert.equal(ra.percentiles.P50, rb.percentiles.P50);
    assert.equal(ra.stdDev, rb.stdDev);
  });

  it('supports normal distribution', () => {
    const scenario: RiskScenario = {
      id: 'norm', name: 'Normal', threat: 'T', vulnerability: 'V',
      impact: { type: 'normal', mean: 200000, stdDev: 50000 },
      probability: { type: 'normal', mean: 0.1, stdDev: 0.02 },
    };
    const engine = new MonteCarloEngine(scenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.mean > 0);
    assert.ok(result.rawSamples.length === 10000);
  });

  it('supports uniform distribution', () => {
    const scenario: RiskScenario = {
      id: 'uni', name: 'Uniform', threat: 'T', vulnerability: 'V',
      impact: { type: 'uniform', min: 50000, max: 150000 },
      probability: { type: 'uniform', min: 0.05, max: 0.15 },
    };
    const engine = new MonteCarloEngine(scenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    for (const s of result.rawSamples) {
      assert.ok(s >= 0, `Sample ${s} should be non-negative`);
    }
  });

  it('supports triangular distribution', () => {
    const scenario: RiskScenario = {
      id: 'tri', name: 'Tri', threat: 'T', vulnerability: 'V',
      impact: { type: 'triangular', min: 10000, max: 500000, mode: 100000 },
      probability: { type: 'triangular', min: 0.01, mode: 0.1, max: 0.3 },
    };
    const engine = new MonteCarloEngine(scenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.mean > 0);
  });

  it('supports betaPERT distribution', () => {
    const scenario: RiskScenario = {
      id: 'pert', name: 'PERT', threat: 'T', vulnerability: 'V',
      impact: { type: 'betaPERT', min: 50000, max: 1000000, mode: 200000 },
      probability: { type: 'betaPERT', min: 0.01, mode: 0.08, max: 0.3 },
    };
    const engine = new MonteCarloEngine(scenario, { iterations: 10000, seed: 42 });
    const result = engine.run();
    assert.ok(result.mean > 0);
    assert.ok(result.max >= result.min);
  });
});

describe('FAIRCalculator', () => {
  it('calculates FAIR model', () => {
    const calc = new FAIRCalculator(basicScenario, { iterations: 5000, seed: 42 });
    const model = calc.calculate();
    assert.ok(model.lossEventFrequency >= 0);
    assert.ok(model.lossMagnitude >= 0);
    assert.ok(model.annualizedLossExpectancy >= 0);
  });

  it('calculates ALE directly', () => {
    const calc = new FAIRCalculator(basicScenario);
    const ale = calc.calculateALE(50, 0.1, 500000, 0.05, 100000);
    assert.ok(ale > 0);
    assert.equal(ale, 50 * 0.1 * (500000 + 0.05 * 100000));
  });

  it('calculates LEF = TEF * Vulnerability', () => {
    const calc = new FAIRCalculator(basicScenario);
    assert.equal(calc.calculateLEF(100, 0.2), 20);
  });

  it('calculates LM = Primary + SecondaryFreq * SecondaryMag', () => {
    const calc = new FAIRCalculator(basicScenario);
    assert.equal(calc.calculateLM(500000, 0.1, 100000), 510000);
  });

  it('monteCarloALE returns valid distribution', () => {
    const calc = new FAIRCalculator(basicScenario, { iterations: 5000, seed: 42 });
    const mc = calc.monteCarloALE(5000, 42);
    assert.ok(mc.mean >= 0);
    assert.ok(mc.percentiles.P10 <= mc.percentiles.P50);
    assert.ok(mc.percentiles.P50 <= mc.percentiles.P90);
    assert.ok(mc.percentiles.P90 <= mc.percentiles.P99);
    assert.ok(mc.histogram.length > 0);
  });

  it('secondary loss factors default correctly', () => {
    const calc = new FAIRCalculator(basicScenario);
    const model = calc.calculate();
    assert.ok(model.secondaryLossFrequency !== undefined);
    assert.ok(model.secondaryLossMagnitude !== undefined);
  });
});

describe('RiskRegister', () => {
  it('adds and retrieves scenarios', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    const entry = reg.getEntry('test-ransomware');
    assert.ok(entry);
    assert.equal(entry.scenario.id, 'test-ransomware');
    assert.equal(entry.status, 'assessed');
  });

  it('quantifies a scenario with all fields populated', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    const q = reg.quantify(basicScenario);
    assert.ok(q.fairModel.annualizedLossExpectancy >= 0);
    assert.ok(q.monteCarloResult.iterations === 1000);
    assert.ok(q.riskScore >= 0 && q.riskScore <= 100);
    assert.ok(['critical', 'high', 'medium', 'low', 'negligible'].includes(q.riskLevel));
    assert.ok(q.recommendation.length > 0);
  });

  it('tracks trends per scenario', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    const trends = reg.getTrendsForScenario('test-ransomware');
    assert.equal(trends.length, 1);
    assert.equal(trends[0].scenarioId, 'test-ransomware');
    assert.ok(trends[0].riskScore >= 0);
  });

  it('portfolioMetrics returns aggregated values', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    const pm = reg.portfolioMetrics();
    assert.equal(pm.scenarioCount, 2);
    assert.ok(pm.totalALE >= 0);
    assert.ok(pm.meanRiskScore >= 0);
  });

  it('updateStatus changes entry status', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    const ok = reg.updateStatus('test-ransomware', 'treated');
    assert.ok(ok);
    assert.equal(reg.getEntry('test-ransomware')!.status, 'treated');
  });

  it('updateStatus returns false for unknown id', () => {
    const reg = new RiskRegister();
    assert.equal(reg.updateStatus('nonexistent', 'accepted'), false);
  });

  it('getActiveEntries filters by status', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    reg.updateStatus('test-ransomware', 'treated');
    const active = reg.getActiveEntries();
    assert.equal(active.length, 1);
    assert.equal(active[0].scenario.id, 'test-fixed');
  });

  it('topRisks returns scenarios sorted by risk score', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    const top = reg.topRisks(1);
    assert.equal(top.length, 1);
    assert.ok(top[0].riskScore >= 0);
  });

  it('generateHeatMap produces cells', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    const hm = reg.generateHeatMap(3, 3);
    assert.equal(hm.cells.length, 9);
    assert.equal(hm.axisLabels.x, 'Impact');
  });

  it('assessAppetite categorizes scenarios', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    const appetite = reg.assessAppetite(0, 0, 0);
    assert.equal(appetite.boundaryExceedances.length, 2);
    assert.equal(appetite.tolerableScenarios.length, 0);
  });

  it('assessAppetite with high thresholds classifies all as tolerable', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    const appetite = reg.assessAppetite(100, Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER);
    assert.equal(appetite.boundaryExceedances.length, 0);
    assert.equal(appetite.tolerableScenarios.length, 1);
  });

  it('getTrends returns all trend records', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    assert.equal(reg.getTrends().length, 2);
  });

  it('multiple scenarios in register are independent', () => {
    const reg = new RiskRegister({ iterations: 1000, seed: 42 });
    reg.addScenario(basicScenario);
    reg.addScenario(fixedScenario);
    const e1 = reg.getEntry('test-ransomware')!;
    const e2 = reg.getEntry('test-fixed')!;
    assert.notEqual(e1.scenario.name, e2.scenario.name);
    assert.notEqual(e1.quantification!.riskScore, e2.quantification!.riskScore);
  });
});
