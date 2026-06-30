import type { CrossMapping } from '../types.js';

export const NIST_PRIVACY_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'nist_privacy', sourceControl: 'P-ID.DM-1', targetFramework: 'nist_csf', targetControl: 'ID.AM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-ID.DM-2', targetFramework: 'nist_csf', targetControl: 'ID.AM-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-ID.IM-1', targetFramework: 'nist_csf', targetControl: 'ID.GV-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.DS-1', targetFramework: 'nist_csf', targetControl: 'PR.DS-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.DS-2', targetFramework: 'nist_csf', targetControl: 'PR.DS-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.AC-1', targetFramework: 'nist_csf', targetControl: 'PR.AC-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.AC-2', targetFramework: 'nist_csf', targetControl: 'PR.AC-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.AC-3', targetFramework: 'nist_csf', targetControl: 'PR.AC-4', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.AC-4', targetFramework: 'nist_csf', targetControl: 'PR.AC-5', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.IP-1', targetFramework: 'nist_csf', targetControl: 'PR.IP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-PR.IP-2', targetFramework: 'nist_csf', targetControl: 'PR.IP-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-DE.CM-1', targetFramework: 'nist_csf', targetControl: 'DE.CM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-DE.CM-2', targetFramework: 'nist_csf', targetControl: 'DE.CM-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-DE.DP-1', targetFramework: 'nist_csf', targetControl: 'DE.AE-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-RS.RP-1', targetFramework: 'nist_csf', targetControl: 'RS.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-RS.CO-1', targetFramework: 'nist_csf', targetControl: 'RS.CO-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nist_privacy', sourceControl: 'P-RC.RP-1', targetFramework: 'nist_csf', targetControl: 'RC.RP-1', confidence: 0.90, relationship: 'equivalent' },
];

export const NIST_PRIVACY_PAIR = { source: 'nist_privacy', target: 'nist_csf' };
