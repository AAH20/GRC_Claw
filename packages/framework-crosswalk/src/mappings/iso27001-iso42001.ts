import type { CrossMapping } from '../types.js';

export const ISO27001_ISO42001_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'iso27001', sourceControl: 'A.5.1', targetFramework: 'iso42001', targetControl: 'A.5.1', confidence: 0.95, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.2', targetFramework: 'iso42001', targetControl: 'A.5.2', confidence: 0.95, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.3', targetFramework: 'iso42001', targetControl: 'A.5.3', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.7', targetFramework: 'iso42001', targetControl: 'A.6.1', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.9', targetFramework: 'iso42001', targetControl: 'A.5.9', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.15', targetFramework: 'iso42001', targetControl: 'A.5.15', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.23', targetFramework: 'iso42001', targetControl: 'A.7.1', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.6.3', targetFramework: 'iso42001', targetControl: 'A.6.3', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.1', targetFramework: 'iso42001', targetControl: 'A.8.1', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.5', targetFramework: 'iso42001', targetControl: 'A.8.5', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.8', targetFramework: 'iso42001', targetControl: 'A.8.8', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.9', targetFramework: 'iso42001', targetControl: 'A.8.9', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.16', targetFramework: 'iso42001', targetControl: 'A.8.16', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.20', targetFramework: 'iso42001', targetControl: 'A.8.20', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.25', targetFramework: 'iso42001', targetControl: 'A.8.25', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.28', targetFramework: 'iso42001', targetControl: 'A.8.28', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.32', targetFramework: 'iso42001', targetControl: 'A.8.32', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.34', targetFramework: 'iso42001', targetControl: 'A.5.34', confidence: 0.9, relationship: 'equivalent' },
];

export const ISO27001_ISO42001_PAIR = { source: 'iso27001', target: 'iso42001' };
