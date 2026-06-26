import type { CrossMapping } from '../types.js';

export const SOC2_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'soc2', sourceControl: 'CC6.1', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.2', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.3', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.1', targetFramework: 'nist_csf', targetControl: 'DE.CM', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.2', targetFramework: 'nist_csf', targetControl: 'DE.AE', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.3', targetFramework: 'nist_csf', targetControl: 'RS.RP', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'CC8.1', targetFramework: 'nist_csf', targetControl: 'PR.IP', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC9.1', targetFramework: 'nist_csf', targetControl: 'ID.RA', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'CC9.2', targetFramework: 'nist_csf', targetControl: 'ID.RA', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'A1.1', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'A1.2', targetFramework: 'nist_csf', targetControl: 'PR.MA', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'C1.1', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.9, relationship: 'equivalent' },
];

export const SOC2_NISTCSF_PAIR = { source: 'soc2', target: 'nist_csf' };
