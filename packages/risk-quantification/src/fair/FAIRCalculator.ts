import type { FAIRFactor, FAIRModel, RiskScenario } from '../types.js';
import { MonteCarloEngine } from '../monte-carlo/MonteCarloEngine.js';

function factor(value: number, confidence?: number, source?: string): FAIRFactor {
  return { value: Math.max(0, value), confidence, source };
}

export class FAIRCalculator {
  private scenario: RiskScenario;
  private iterations: number;
  private seed?: number;

  constructor(scenario: RiskScenario, options?: { iterations?: number; seed?: number }) {
    this.scenario = scenario;
    this.iterations = options?.iterations ?? 10000;
    this.seed = options?.seed;
  }

  calculate(): FAIRModel {
    const s = this.scenario;
    const engine = new MonteCarloEngine(s, { iterations: this.iterations, seed: this.seed });
    const mcResult = engine.run();

    const tef = mcResult.mean;
    const vuln = s.probability.type
      ? this.estimateVulnerability()
      : { value: 1, confidence: 1 };
    const lossMag = this.estimateLossMagnitude();
    const primaryLoss = lossMag;
    const secondaryLossFreq = this.estimateSecondaryLossFrequency();
    const secondaryLossMag = this.estimateSecondaryLossMagnitude();

    const lef = tef * vuln.value;
    const lm = primaryLoss.value + (secondaryLossFreq.value * secondaryLossMag.value);
    const ale = lef * lm;

    return {
      threatEventFrequency: factor(tef),
      threatCapability: factor(tef),
      vulnerability: vuln,
      primaryLoss: primaryLoss,
      secondaryLossFrequency: secondaryLossFreq,
      secondaryLossMagnitude: secondaryLossMag,
      lossEventFrequency: lef,
      lossMagnitude: lm,
      annualizedLossExpectancy: ale,
    };
  }

  calculateALE(tef: number, vulnerability: number, primaryLoss: number, secondaryLossFreq = 0, secondaryLossMag = 0): number {
    const lef = tef * vulnerability;
    const lm = primaryLoss + secondaryLossFreq * secondaryLossMag;
    return lef * lm;
  }

  calculateLEF(tef: number, vulnerability: number): number {
    return tef * vulnerability;
  }

  calculateLM(primaryLoss: number, secondaryLossFreq = 0, secondaryLossMag = 0): number {
    return primaryLoss + secondaryLossFreq * secondaryLossMag;
  }

  monteCarloALE(samples = 10000, seed?: number): {
    mean: number;
    percentiles: { P10: number; P50: number; P90: number; P99: number };
    histogram: Array<{ bucket: number; count: number; frequency: number }>;
  } {
    const rng = new (this.createRngConstructor())(seed ?? Date.now());
    const results: number[] = [];

    for (let i = 0; i < samples; i++) {
      const tefSample = this.sampleTEF(rng);
      const vulnSample = this.sampleVulnerability(rng);
      const plSample = this.samplePrimaryLoss(rng);
      const slfSample = this.sampleSecondaryLossFreq(rng);
      const slmSample = this.sampleSecondaryLossMag(rng);

      const lef = tefSample * vulnSample;
      const lm = plSample + slfSample * slmSample;
      results.push(lef * lm);
    }

    results.sort((a, b) => a - b);
    const mu = results.reduce((s, v) => s + v, 0) / results.length;

    return {
      mean: mu,
      percentiles: {
        P10: this.percentileAt(results, 10),
        P50: this.percentileAt(results, 50),
        P90: this.percentileAt(results, 90),
        P99: this.percentileAt(results, 99),
      },
      histogram: this.buildHist(results, 30),
    };
  }

  private sampleTEF(rng: { next(): number }): number {
    const impact = this.scenario.impact;
    const prob = this.scenario.probability;
    const meanImpact = impact.mean ?? ((impact.min ?? 0) + (impact.max ?? 1)) / 2;
    return meanImpact * 52;
  }

  private sampleVulnerability(rng: { next(): number }): number {
    const prob = this.scenario.probability;
    const mu = prob.mean ?? 0.5;
    const sd = prob.stdDev ?? 0.15;
    let u = 0, v = 0;
    while (u === 0) u = rng.next();
    while (v === 0) v = rng.next();
    const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    return Math.max(0, Math.min(1, mu + z * sd));
  }

  private samplePrimaryLoss(rng: { next(): number }): number {
    const impact = this.scenario.impact;
    switch (impact.type) {
      case 'normal':
        return Math.max(0, (impact.mean ?? 100) + this.boxMuller(rng) * (impact.stdDev ?? 10));
      case 'lognormal': {
        const mu = Math.log((impact.mean ?? 100) ** 2 / Math.sqrt((impact.stdDev ?? 10) ** 2 + (impact.mean ?? 100) ** 2));
        const sigma = Math.sqrt(Math.log(1 + (impact.stdDev ?? 10) ** 2 / (impact.mean ?? 100) ** 2));
        return Math.exp(mu + sigma * this.boxMuller(rng));
      }
      case 'uniform':
        return (impact.min ?? 0) + rng.next() * ((impact.max ?? 1) - (impact.min ?? 0));
      case 'triangular':
        return this.triSample(rng, impact.min ?? 0, impact.max ?? 1, impact.mode ?? 0.5);
      case 'betaPERT':
        return this.pertSample(rng, impact.min ?? 0, impact.mode ?? 0.5, impact.max ?? 1);
      default:
        return impact.mean ?? 100;
    }
  }

  private sampleSecondaryLossFreq(rng: { next(): number }): number {
    return rng.next() * 0.3;
  }

  private sampleSecondaryLossMag(rng: { next(): number }): number {
    const impact = this.scenario.impact;
    const mu = (impact.mean ?? 100) * 0.2;
    return Math.max(0, mu + this.boxMuller(rng) * (mu * 0.3));
  }

  private estimateVulnerability(): FAIRFactor {
    return factor(this.scenario.probability.mean ?? 0.5, 0.8, 'scenario-probability');
  }

  private estimateLossMagnitude(): FAIRFactor {
    const impact = this.scenario.impact;
    const mu = impact.mean ?? ((impact.min ?? 0) + (impact.max ?? 1)) / 2;
    return factor(mu, 0.9, 'scenario-impact');
  }

  private estimateSecondaryLossFrequency(): FAIRFactor {
    return factor(0.15, 0.5, 'estimated');
  }

  private estimateSecondaryLossMagnitude(): FAIRFactor {
    const impact = this.scenario.impact;
    const mu = (impact.mean ?? 100) * 0.2;
    return factor(mu, 0.5, 'estimated');
  }

  private createRngConstructor() {
    return class {
      private s: number;
      constructor(seed: number) { this.s = seed % 2147483647; if (this.s <= 0) this.s += 2147483646; }
      next(): number { this.s = (this.s * 16807) % 2147483647; return (this.s - 1) / 2147483646; }
    };
  }

  private boxMuller(rng: { next(): number }): number {
    let u = 0, v = 0;
    while (u === 0) u = rng.next();
    while (v === 0) v = rng.next();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  private triSample(rng: { next(): number }, min: number, max: number, mode: number): number {
    const u = rng.next();
    const fc = (mode - min) / (max - min);
    return u < fc
      ? min + Math.sqrt(u * (max - min) * (mode - min))
      : max - Math.sqrt((1 - u) * (max - min) * (max - mode));
  }

  private pertSample(rng: { next(): number }, min: number, mode: number, max: number): number {
    const mu = (min + 4 * mode + max) / 6;
    const v = Math.max(((mu - min) * (max - mu)) / ((max - min) ** 2) * ((max - min) ** 2) / ((max - min) + 1), 0.01);
    const alpha = Math.max(((mu - min) / (max - min)) * ((mu - min) * (max - mu) / v - 1), 0.1);
    const beta = Math.max(((max - mu) / (max - min)) * ((mu - min) * (max - mu) / v - 1), 0.1);
    const x = this.betaSample(rng, alpha, beta);
    return min + x * (max - min);
  }

  private betaSample(rng: { next(): number }, a: number, b: number): number {
    const ga = this.gammaSample(rng, a);
    const gb = this.gammaSample(rng, b);
    return ga / (ga + gb);
  }

  private gammaSample(rng: { next(): number }, alpha: number): number {
    if (alpha < 1) return this.gammaSample(rng, alpha + 1) * Math.pow(rng.next(), 1 / alpha);
    const d = alpha - 1 / 3;
    const c = 1 / Math.sqrt(9 * d);
    while (true) {
      let x: number, v: number;
      do { x = this.boxMuller(rng); v = 1 + c * x; } while (v <= 0);
      v = v * v * v;
      const u = rng.next();
      if (u < 1 - 0.0331 * x ** 4) return d * v;
      if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
    }
  }

  private percentileAt(sorted: number[], p: number): number {
    const idx = (p / 100) * (sorted.length - 1);
    const lo = Math.floor(idx), hi = Math.ceil(idx);
    return sorted[lo] * (1 - (idx - lo)) + sorted[hi] * (idx - lo);
  }

  private buildHist(samples: number[], bins: number): Array<{ bucket: number; count: number; frequency: number }> {
    const min = Math.min(...samples);
    const max = Math.max(...samples);
    const w = (max - min) / bins || 1;
    const h = Array.from({ length: bins }, (_, i) => ({ bucket: min + i * w + w / 2, count: 0, frequency: 0 }));
    for (const s of samples) {
      let idx = Math.floor((s - min) / w);
      if (idx >= bins) idx = bins - 1;
      h[idx].count++;
    }
    for (const c of h) c.frequency = c.count / samples.length;
    return h;
  }
}
