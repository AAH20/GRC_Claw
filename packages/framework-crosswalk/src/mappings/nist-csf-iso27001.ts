import type { CrossMapping } from '../types.js';

export const NISTCSF_ISO27001_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'nist_csf', sourceControl: 'DE.AE', targetFramework: 'iso27001', targetControl: 'A.8.16', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'DE.CM', targetFramework: 'iso27001', targetControl: 'A.8.15', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'DE.DP', targetFramework: 'iso27001', targetControl: 'A.8.16', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'nist_csf', sourceControl: 'ID.AM', targetFramework: 'iso27001', targetControl: 'A.5.9', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'ID.RA', targetFramework: 'iso27001', targetControl: 'A.5.7', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'ID.RA', targetFramework: 'iso27001', targetControl: 'A.8.8', confidence: 0.8, relationship: 'supports' },
  { sourceFramework: 'nist_csf', sourceControl: 'ID.IM', targetFramework: 'iso27001', targetControl: 'A.5.1', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.AC', targetFramework: 'iso27001', targetControl: 'A.5.15', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.AC', targetFramework: 'iso27001', targetControl: 'A.5.16', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.AT', targetFramework: 'iso27001', targetControl: 'A.6.3', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.DS', targetFramework: 'iso27001', targetControl: 'A.8.24', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.IP', targetFramework: 'iso27001', targetControl: 'A.5.1', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.MA', targetFramework: 'iso27001', targetControl: 'A.8.1', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'PR.PT', targetFramework: 'iso27001', targetControl: 'A.8.9', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'RC.RP', targetFramework: 'iso27001', targetControl: 'A.5.24', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'nist_csf', sourceControl: 'RS.RP', targetFramework: 'iso27001', targetControl: 'A.5.24', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'nist_csf', sourceControl: 'RS.MA', targetFramework: 'iso27001', targetControl: 'A.5.24', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'nist_csf', sourceControl: 'RS.CO', targetFramework: 'iso27001', targetControl: 'A.5.5', confidence: 0.8, relationship: 'partial' },
];

export const NISTCSF_ISO27001_PAIR = { source: 'nist_csf', target: 'iso27001' };
