import type { CrossMapping } from '../types.js';

export const SOC2_ISO27001_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'soc2', sourceControl: 'CC6.1', targetFramework: 'iso27001', targetControl: 'A.8.5', confidence: 0.95, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.1', targetFramework: 'iso27001', targetControl: 'A.8.3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.2', targetFramework: 'iso27001', targetControl: 'A.5.15', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.2', targetFramework: 'iso27001', targetControl: 'A.5.16', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'soc2', sourceControl: 'CC6.3', targetFramework: 'iso27001', targetControl: 'A.8.2', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.1', targetFramework: 'iso27001', targetControl: 'A.8.16', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.2', targetFramework: 'iso27001', targetControl: 'A.8.15', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.2', targetFramework: 'iso27001', targetControl: 'A.8.16', confidence: 0.8, relationship: 'supports' },
  { sourceFramework: 'soc2', sourceControl: 'CC7.3', targetFramework: 'iso27001', targetControl: 'A.8.16', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'CC8.1', targetFramework: 'iso27001', targetControl: 'A.8.9', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'CC9.1', targetFramework: 'iso27001', targetControl: 'A.5.23', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'CC9.2', targetFramework: 'iso27001', targetControl: 'A.5.24', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'A1.1', targetFramework: 'iso27001', targetControl: 'A.5.20', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'A1.2', targetFramework: 'iso27001', targetControl: 'A.5.21', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'soc2', sourceControl: 'C1.1', targetFramework: 'iso27001', targetControl: 'A.5.12', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'soc2', sourceControl: 'PI1.1', targetFramework: 'iso27001', targetControl: 'A.5.34', confidence: 0.85, relationship: 'equivalent' },
];

export const SOC2_ISO27001_PAIR = { source: 'soc2', target: 'iso27001' };
