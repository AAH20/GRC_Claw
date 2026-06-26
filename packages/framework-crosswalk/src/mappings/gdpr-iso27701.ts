import type { CrossMapping } from '../types.js';

export const GDPR_ISO27701_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'gdpr', sourceControl: 'Art.5', targetFramework: 'iso27701', targetControl: 'A.5.2', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.6', targetFramework: 'iso27701', targetControl: 'A.7.2', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.12', targetFramework: 'iso27701', targetControl: 'A.7.3', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.13', targetFramework: 'iso27701', targetControl: 'A.7.3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.14', targetFramework: 'iso27701', targetControl: 'A.7.3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.15', targetFramework: 'iso27701', targetControl: 'A.7.3', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.16', targetFramework: 'iso27701', targetControl: 'A.7.4', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.17', targetFramework: 'iso27701', targetControl: 'A.7.4', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.20', targetFramework: 'iso27701', targetControl: 'A.7.4', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.21', targetFramework: 'iso27701', targetControl: 'A.7.4', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.25', targetFramework: 'iso27701', targetControl: 'A.5.4', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.28', targetFramework: 'iso27701', targetControl: 'A.6.14', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.30', targetFramework: 'iso27701', targetControl: 'A.5.2', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.32', targetFramework: 'iso27701', targetControl: 'A.8.1', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.33', targetFramework: 'iso27701', targetControl: 'A.7.6', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'gdpr', sourceControl: 'Art.35', targetFramework: 'iso27701', targetControl: 'A.5.3', confidence: 0.85, relationship: 'partial' },
];

export const GDPR_ISO27701_PAIR = { source: 'gdpr', target: 'iso27701' };
