export type {
  DistributionType,
  DistributionParams,
  RiskScenario,
  FAIRFactor,
  FAIRModel,
  MonteCarloResult,
  RiskQuantification,
  RiskTrend,
  RiskHeatMapCell,
  RiskHeatMap,
  RiskAppetite,
  RiskRegisterEntry,
} from './types.js';

export { MonteCarloEngine, Random, percentile, mean, variance, stdDev } from './monte-carlo/MonteCarloEngine.js';
export { FAIRCalculator } from './fair/FAIRCalculator.js';
export { RiskRegister } from './risk-register/RiskRegister.js';
