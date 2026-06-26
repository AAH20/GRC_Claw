import type { DistributionParams, MonteCarloResult, RiskScenario } from '../types.js';

interface RNG {
  next(): number;
}

class SeededRNG implements RNG {
  private state: number;
  constructor(seed: number) {
    this.state = seed % 2147483647;
    if (this.state <= 0) this.state += 2147483646;
  }
  next(): number {
    this.state = (this.state * 16807) % 2147483647;
    return (this.state - 1) / 2147483646;
  }
}

class MersenneTwister implements RNG {
  private mt: number[] = new Array(624);
  private index = 624;
  constructor(seed: number) {
    this.mt[0] = seed >>> 0;
    for (let i = 1; i < 624; i++) {
      this.mt[i] = (1812433253 * (this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)) + i) >>> 0;
    }
  }
  next(): number {
    if (this.index >= 624) {
      for (let i = 0; i < 624; i++) {
        const y = (this.mt[i] & 0x80000000) + (this.mt[(i + 1) % 624] & 0x7fffffff);
        this.mt[i] = this.mt[(i + 397) % 624] ^ (y >>> 1);
        if (y % 2 !== 0) this.mt[i] ^= 0x9908b0df;
      }
      this.index = 0;
    }
    let z = this.mt[this.index++];
    z ^= z >>> 11;
    z ^= (z << 7) & 0x9d2c5680;
    z ^= (z << 15) & 0xefc60000;
    z ^= z >>> 18;
    return (z >>> 0) / 4294967295;
  }
}

class Random {
  private rng: RNG;
  constructor(seed?: number) {
    this.rng = seed != null ? new MersenneTwister(seed) : new SeededRNG(Date.now() ^ (Math.random() * 0xffffffff));
  }
  next(): number {
    return this.rng.next();
  }
  uniform(min = 0, max = 1): number {
    return min + this.rng.next() * (max - min);
  }
  normal(mean = 0, stdDev = 1): number {
    let u = 0, v = 0;
    while (u === 0) u = this.rng.next();
    while (v === 0) v = this.rng.next();
    const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    return mean + z * stdDev;
  }
  lognormal(mean: number, stdDev: number): number {
    const mu = Math.log((mean * mean) / Math.sqrt(stdDev * stdDev + mean * mean));
    const sigma = Math.sqrt(Math.log(1 + (stdDev * stdDev) / (mean * mean)));
    return Math.exp(mu + sigma * this.normal());
  }
  triangular(min: number, max: number, mode: number): number {
    const u = this.rng.next();
    const fc = (mode - min) / (max - min);
    if (u < fc) {
      return min + Math.sqrt(u * (max - min) * (mode - min));
    }
    return max - Math.sqrt((1 - u) * (max - min) * (max - mode));
  }
  betaPert(min: number, mode: number, max: number): number {
    const mu = (min + 4 * mode + max) / 6;
    const v = ((mu - min) * (max - mu)) / ((max - min) * (max - min)) * ((max - min) * (max - min)) / ((max - min) + 1);
    const alpha = ((mu - min) / (max - min)) * ((mu - min) * (max - mu) / (v || 1) - 1);
    const betaVal = ((max - mu) / (max - min)) * ((mu - min) * (max - mu) / (v || 1) - 1);
    const a = Math.max(alpha, 0.1);
    const b = Math.max(betaVal, 0.1);
    const x = this.beta(a, b);
    return min + x * (max - min);
  }
  beta(a: number, b: number): number {
    const gammaA = this.gamma(a);
    const gammaB = this.gamma(b);
    return gammaA / (gammaA + gammaB);
  }
  gamma(alpha: number): number {
    if (alpha < 1) {
      return this.gamma(alpha + 1) * Math.pow(this.rng.next(), 1 / alpha);
    }
    const d = alpha - 1 / 3;
    const c = 1 / Math.sqrt(9 * d);
    while (true) {
      let x: number;
      let v: number;
      do {
        x = this.normal();
        v = 1 + c * x;
      } while (v <= 0);
      v = v * v * v;
      const u = this.rng.next();
      if (u < 1 - 0.0331 * x * x * x * x) {
        return d * v;
      }
      if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) {
        return d * v;
      }
    }
  }
  sample(d: DistributionParams): number {
    switch (d.type) {
      case 'normal':
        return this.normal(d.mean ?? 0, d.stdDev ?? 1);
      case 'lognormal':
        return this.lognormal(d.mean ?? 1, d.stdDev ?? 1);
      case 'uniform':
        return this.uniform(d.min ?? 0, d.max ?? 1);
      case 'triangular':
        return this.triangular(d.min ?? 0, d.max ?? 1, d.mode ?? 0.5);
      case 'betaPERT':
        return this.betaPert(d.min ?? 0, d.mode ?? 0.5, d.max ?? 1);
      default:
        throw new Error(`Unknown distribution type: ${d.type}`);
    }
  }
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  if (sorted.length === 1) return sorted[0];
  const idx = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(idx);
  const upper = Math.ceil(idx);
  const w = idx - lower;
  return sorted[lower] * (1 - w) + sorted[upper] * w;
}

function mean(arr: number[]): number {
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function variance(arr: number[], mu: number): number {
  return arr.reduce((s, v) => s + (v - mu) ** 2, 0) / arr.length;
}

function stdDev(arr: number[], mu: number): number {
  return Math.sqrt(variance(arr, mu));
}

function buildHistogram(samples: number[], bins = 50): MonteCarloResult['histogram'] {
  if (samples.length === 0) return [];
  const min = Math.min(...samples);
  const max = Math.max(...samples);
  const range = max - min || 1;
  const binWidth = range / bins;
  const buckets = new Array(bins).fill(0).map((_, i) => ({
    bucket: min + i * binWidth + binWidth / 2,
    count: 0,
    frequency: 0,
  }));
  for (const s of samples) {
    let idx = Math.floor((s - min) / binWidth);
    if (idx >= bins) idx = bins - 1;
    if (idx < 0) idx = 0;
    buckets[idx].count++;
  }
  for (const b of buckets) {
    b.frequency = b.count / samples.length;
  }
  return buckets;
}

export class MonteCarloEngine {
  private scenario: RiskScenario;
  private iterations: number;
  private seed?: number;

  constructor(scenario: RiskScenario, options?: { iterations?: number; seed?: number }) {
    this.scenario = scenario;
    this.iterations = options?.iterations ?? 10000;
    this.seed = options?.seed;
  }

  run(): MonteCarloResult {
    const rng = new Random(this.seed);
    const samples: number[] = new Array(this.iterations);

    for (let i = 0; i < this.iterations; i++) {
      const impact = rng.sample(this.scenario.impact);
      const probability = rng.sample(this.scenario.probability);
      samples[i] = impact * Math.max(0, probability);
    }

    const sorted = [...samples].sort((a, b) => a - b);
    const mu = mean(samples);
    const sigma = stdDev(samples, mu);
    const v = variance(samples, mu);

    const p10 = percentile(sorted, 10);
    const p25 = percentile(sorted, 25);
    const p50 = percentile(sorted, 50);
    const p75 = percentile(sorted, 75);
    const p90 = percentile(sorted, 90);
    const p95 = percentile(sorted, 95);
    const p99 = percentile(sorted, 99);

    const var95 = p95;
    const var99 = p99;

    const above95 = sorted.filter(v => v >= var95);
    const above99 = sorted.filter(v => v >= var99);
    const cvaR95 = above95.length > 0 ? mean(above95) : var95;
    const cvaR99 = above99.length > 0 ? mean(above99) : var99;

    return {
      iterations: this.iterations,
      percentiles: { P10: p10, P25: p25, P50: p50, P75: p75, P90: p90, P95: p95, P99: p99 },
      mean: mu,
      stdDev: sigma,
      variance: v,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      valueAtRisk: { confidence95: var95, confidence99: var99 },
      conditionalValueAtRisk: { confidence95: cvaR95, confidence99: cvaR99 },
      histogram: buildHistogram(sorted),
      rawSamples: sorted,
    };
  }
}

export { Random, percentile, mean, variance, stdDev };
