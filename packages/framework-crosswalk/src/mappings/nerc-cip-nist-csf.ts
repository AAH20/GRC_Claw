import type { CrossMapping } from '../types.js';

export const NERC_CIP_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-002-5.1a', targetFramework: 'nist_csf', targetControl: 'ID.AM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-003-8', targetFramework: 'nist_csf', targetControl: 'ID.GV-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-004-7', targetFramework: 'nist_csf', targetControl: 'PR.AC-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-005-7', targetFramework: 'nist_csf', targetControl: 'PR.AC-3', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-006-6r2', targetFramework: 'nist_csf', targetControl: 'PR.AC-4', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-007-6r2', targetFramework: 'nist_csf', targetControl: 'PR.IP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-008-5', targetFramework: 'nist_csf', targetControl: 'RS.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-009-6r2', targetFramework: 'nist_csf', targetControl: 'RC.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-010-4', targetFramework: 'nist_csf', targetControl: 'DE.CM-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-011-2', targetFramework: 'nist_csf', targetControl: 'PR.DS-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-012-2', targetFramework: 'nist_csf', targetControl: 'PR.DS-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-013-2', targetFramework: 'nist_csf', targetControl: 'ID.SC-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'nerc_cip', sourceControl: 'CIP-014-3', targetFramework: 'nist_csf', targetControl: 'ID.RA-1', confidence: 0.85, relationship: 'supports' },
];

export const NERC_CIP_PAIR = { source: 'nerc_cip', target: 'nist_csf' };
