import type { CrossMapping } from '../types.js';

export const DORA_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'dora', sourceControl: 'Art.6', targetFramework: 'nist_csf', targetControl: 'ID.GV', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.8', targetFramework: 'nist_csf', targetControl: 'ID.RA', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.9', targetFramework: 'nist_csf', targetControl: 'ID.RA', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'dora', sourceControl: 'Art.10', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.11', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'dora', sourceControl: 'Art.13', targetFramework: 'nist_csf', targetControl: 'PR.MA', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.14', targetFramework: 'nist_csf', targetControl: 'PR.PT', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.15', targetFramework: 'nist_csf', targetControl: 'DE.CM', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.16', targetFramework: 'nist_csf', targetControl: 'DE.AE', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.17', targetFramework: 'nist_csf', targetControl: 'RS.RP', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.18', targetFramework: 'nist_csf', targetControl: 'RS.CO', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'dora', sourceControl: 'Art.19', targetFramework: 'nist_csf', targetControl: 'RC.RP', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'dora', sourceControl: 'Art.28', targetFramework: 'nist_csf', targetControl: 'ID.SC', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'dora', sourceControl: 'Art.30', targetFramework: 'nist_csf', targetControl: 'ID.SC', confidence: 0.8, relationship: 'partial' },
];

export const DORA_NISTCSF_PAIR = { source: 'dora', target: 'nist_csf' };
