import type { CrossMapping } from '../types.js';

export const NIS2_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'nis2', sourceControl: 'Art.21.1', targetFramework: 'nist_csf', targetControl: 'ID.GV-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.2', targetFramework: 'nist_csf', targetControl: 'ID.RA-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.3', targetFramework: 'nist_csf', targetControl: 'ID.AM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.4', targetFramework: 'nist_csf', targetControl: 'PR.AC-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.5', targetFramework: 'nist_csf', targetControl: 'PR.AC-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.6', targetFramework: 'nist_csf', targetControl: 'PR.AC-4', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.7', targetFramework: 'nist_csf', targetControl: 'PR.AC-5', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.8', targetFramework: 'nist_csf', targetControl: 'PR.AC-7', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.9', targetFramework: 'nist_csf', targetControl: 'PR.DS-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.10', targetFramework: 'nist_csf', targetControl: 'PR.DS-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.11', targetFramework: 'nist_csf', targetControl: 'PR.IP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.12', targetFramework: 'nist_csf', targetControl: 'PR.IP-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.13', targetFramework: 'nist_csf', targetControl: 'DE.CM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.14', targetFramework: 'nist_csf', targetControl: 'DE.CM-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.15', targetFramework: 'nist_csf', targetControl: 'RS.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.16', targetFramework: 'nist_csf', targetControl: 'RS.RC-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.17', targetFramework: 'nist_csf', targetControl: 'RC.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nis2', sourceControl: 'Art.21.18', targetFramework: 'nist_csf', targetControl: 'RC.IM-1', confidence: 0.85, relationship: 'supports' },
];

export const NIS2_PAIR = { source: 'nis2', target: 'nist_csf' };
