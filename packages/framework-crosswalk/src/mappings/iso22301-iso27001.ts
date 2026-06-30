import type { CrossMapping } from '../types.js';

export const ISO22301_ISO27001_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'iso_22301', sourceControl: '4.1', targetFramework: 'iso27001', targetControl: 'A.5.1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '4.2', targetFramework: 'iso27001', targetControl: 'A.5.2', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '5.1', targetFramework: 'iso27001', targetControl: 'A.5.3', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '5.2', targetFramework: 'iso27001', targetControl: 'A.5.4', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '5.3', targetFramework: 'iso27001', targetControl: 'A.6.1', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '6.1', targetFramework: 'iso27001', targetControl: 'A.8.1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iso_22301', sourceControl: '6.2', targetFramework: 'iso27001', targetControl: 'A.8.2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '6.3', targetFramework: 'iso27001', targetControl: 'A.8.3', confidence: 0.80, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '7.1', targetFramework: 'iso27001', targetControl: 'A.8.8', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iso_22301', sourceControl: '7.2', targetFramework: 'iso27001', targetControl: 'A.8.9', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '7.3', targetFramework: 'iso27001', targetControl: 'A.8.10', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '8.1', targetFramework: 'iso27001', targetControl: 'A.12.1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iso_22301', sourceControl: '8.2', targetFramework: 'iso27001', targetControl: 'A.12.2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '9.1', targetFramework: 'iso27001', targetControl: 'A.16.1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iso_22301', sourceControl: '9.2', targetFramework: 'iso27001', targetControl: 'A.16.2', confidence: 0.85, relationship: 'supports' },
  { sourceFramework: 'iso_22301', sourceControl: '10.1', targetFramework: 'iso27001', targetControl: 'A.17.1', confidence: 0.90, relationship: 'equivalent' },
  { sourceFramework: 'iso_22301', sourceControl: '10.2', targetFramework: 'iso27001', targetControl: 'A.17.2', confidence: 0.85, relationship: 'supports' },
];

export const ISO22301_PAIR = { source: 'iso_22301', target: 'iso27001' };
