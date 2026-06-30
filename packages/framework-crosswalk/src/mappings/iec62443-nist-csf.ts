import type { CrossMapping } from '../types.js';

export const IEC62443_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'iec_62443', sourceControl: 'SR 1.1', targetFramework: 'nist_csf', targetControl: 'ID.AM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 1.2', targetFramework: 'nist_csf', targetControl: 'ID.AM-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 1.3', targetFramework: 'nist_csf', targetControl: 'ID.AM-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 1.4', targetFramework: 'nist_csf', targetControl: 'ID.AM-5', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 1.5', targetFramework: 'nist_csf', targetControl: 'ID.AM-6', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 2.1', targetFramework: 'nist_csf', targetControl: 'PR.AC-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 2.2', targetFramework: 'nist_csf', targetControl: 'PR.AC-3', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 2.3', targetFramework: 'nist_csf', targetControl: 'PR.AC-4', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 2.4', targetFramework: 'nist_csf', targetControl: 'PR.AC-5', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 3.1', targetFramework: 'nist_csf', targetControl: 'PR.DS-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 3.2', targetFramework: 'nist_csf', targetControl: 'PR.DS-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 3.3', targetFramework: 'nist_csf', targetControl: 'PR.DS-5', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 3.4', targetFramework: 'nist_csf', targetControl: 'PR.DS-6', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 4.1', targetFramework: 'nist_csf', targetControl: 'PR.IP-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 4.2', targetFramework: 'nist_csf', targetControl: 'PR.IP-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 5.1', targetFramework: 'nist_csf', targetControl: 'DE.CM-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 5.2', targetFramework: 'nist_csf', targetControl: 'DE.CM-3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 5.3', targetFramework: 'nist_csf', targetControl: 'DE.CM-4', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 6.1', targetFramework: 'nist_csf', targetControl: 'DE.AE-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 6.2', targetFramework: 'nist_csf', targetControl: 'DE.AE-2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 7.1', targetFramework: 'nist_csf', targetControl: 'RS.RP-1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 7.2', targetFramework: 'nist_csf', targetControl: 'RS.RC-1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 7.3', targetFramework: 'nist_csf', targetControl: 'RS.CO-1', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iec_62443', sourceControl: 'SR 7.4', targetFramework: 'nist_csf', targetControl: 'RC.RP-1', confidence: 0.85, relationship: 'supports' },
];

export const IEC62443_PAIR = { source: 'iec_62443', target: 'nist_csf' };
