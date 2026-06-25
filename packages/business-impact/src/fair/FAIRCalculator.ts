import type { FAIRInput, FAIROutput } from "../types.js";

export class FAIRCalculator {
  private monteCarloIterations: number;

  constructor(monteCarloIterations: number = 10000) {
    this.monteCarloIterations = monteCarloIterations;
  }

  calculate(input: FAIRInput): FAIROutput {
    const lossEvents = input.lossEvents || this.estimateLossEvents(input);
    const annualizedLossExposure = lossEvents * input.probableLossMagnitude;

    const samples: number[] = [];
    for (let i = 0; i < this.monteCarloIterations; i++) {
      const tef = this.randomize(input.threatEventFrequency, 0.3);
      const lm = this.randomize(input.probableLossMagnitude, 0.4);
      samples.push(tef * lm);
    }

    samples.sort((a, b) => a - b);
    const low = samples[Math.floor(samples.length * 0.05)];
    const high = samples[Math.floor(samples.length * 0.95)];
    const expected = samples.reduce((a, b) => a + b, 0) / samples.length;

    return {
      expectedAnnualLoss: Math.round(expected),
      confidenceInterval: { low: Math.round(low), high: Math.round(high) },
      riskRating: this.getRiskRating(expected),
      annualizedLossExposure: Math.round(annualizedLossExposure),
    };
  }

  private estimateLossEvents(input: FAIRInput): number {
    return input.threatEventFrequency * input.vulnerability * input.threatCapability;
  }

  private randomize(mean: number, stdDev: number): number {
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + z * stdDev * mean;
  }

  private getRiskRating(ale: number): FAIROutput["riskRating"] {
    if (ale < 10000) return "minimal";
    if (ale < 50000) return "low";
    if (ale < 250000) return "medium";
    if (ale < 1000000) return "high";
    return "critical";
  }
}
